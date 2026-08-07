import logging
from hetzner_ddns.hetzner import HetznerCloudAPI
from hetzner_ddns.txt_formatter import format_txt_records

logger = logging.getLogger(__name__)

# Never touched in strict mode: removing these can break zone delegation
# or resolution entirely, regardless of whether the user configured them.
PROTECTED_TYPES = {"SOA", "NS"}


def normalize_record_type(rtype: str) -> str:
    """DNS types from the API may not match config casing (e.g. txt vs TXT)."""
    return (rtype or "").upper()


def normalize_record_name(name: str, zone_name: str) -> str:
    """
    Map RRSet names from the API to the same form used in config (@ or relative labels).

    Hetzner may return the apex as the zone name or as '@', and subdomains as FQDNs.
    """
    if not name:
        return name
    name = name.rstrip(".")
    z = zone_name.rstrip(".")
    if name == "@" or name == z:
        return "@"
    suffix = f".{z}"
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return name


def cname_label_conflict_type(existing_rrsets, zone_name, record_name, record_type):
    """
    If creating this RRSet would violate CNAME exclusivity, return the existing type that blocks it.

    At one DNS owner name, a CNAME cannot coexist with any other RR type.
    """
    norm_target = normalize_record_name(record_name, zone_name)
    want = normalize_record_type(record_type)
    for rrset in existing_rrsets:
        n = normalize_record_name(rrset.get("name") or "", zone_name)
        if n != norm_target:
            continue
        has = normalize_record_type(rrset.get("type"))
        if has == want:
            continue
        if want == "CNAME" or has == "CNAME":
            return has
    return None


def handle_extra_records(api, zone_name, existing, configured_keys, confirm_delete):
    """
    In 'strict' sync_mode, remove RRSets that exist on Hetzner but are not
    present in the local config, so the remote zone mirrors the config
    exactly (the counterpart to 'additive' mode, which never touches
    records it doesn't manage).

    Records of a protected type (SOA, NS) are always left alone. Until
    confirm_delete is enabled, extras are only reported via a warning so
    the user can review them (add them to the config, or remove them
    manually) before any deletion happens.
    """
    extras = [
        (name, rtype, rrset)
        for (name, rtype), rrset in existing.items()
        if (name, rtype) not in configured_keys and rtype not in PROTECTED_TYPES
    ]

    if not extras:
        return

    if not confirm_delete:
        for name, rtype, rrset in extras:
            values = [rec.get("value") for rec in rrset.get("records", [])]
            logger.warning(
                "Strict mode: '%s' (%s) in zone %s exists on Hetzner but not in your "
                "config (values: %s). It will NOT be removed automatically. Add it to "
                "the config to keep it, or set global.strict_confirm_delete=true once "
                "you've reviewed all such warnings to let the tool delete it.",
                name, rtype, zone_name, values,
            )
        return

    for name, rtype, rrset in extras:
        try:
            api.delete_rrset(zone_name, name, rtype)
            logger.info(
                "Strict mode: removed extra record %s (%s) in zone %s",
                name, rtype, zone_name,
            )
        except Exception as e:
            logger.error(
                "Strict mode: failed to remove extra record %s (%s) in zone %s: %s",
                name, rtype, zone_name, e,
            )


def sync_all(cfg, ip):
    """
    Synchronize all DNS records across all configured zones.
    
    Args:
        cfg: Configuration object with global_cfg and zones
        ip: Current public IP address
    """
    api = HetznerCloudAPI(cfg.global_cfg["api_token"])
    default_sync_mode = cfg.global_cfg.get("sync_mode", "additive")
    default_confirm_delete = bool(cfg.global_cfg.get("strict_confirm_delete", False))

    for zone in cfg.zones:
        zone_name = zone["name"]
        logger.debug(f"Processing zone: {zone_name}")

        # Each zone can override the global sync_mode/strict_confirm_delete,
        # since not every domain needs to be managed the same way.
        sync_mode = zone.get("sync_mode", default_sync_mode)
        confirm_delete = bool(zone.get("strict_confirm_delete", default_confirm_delete))

        try:
            # Fetch existing RRSets for this zone
            existing_rrsets = api.get_rrsets(zone_name)
        except Exception as e:
            logger.error(f"Failed to fetch RRSets for zone {zone_name}: {e}")
            continue

        # Build lookup map: (name, type) -> rrset
        existing = {}
        for rrset in existing_rrsets:
            norm_name = normalize_record_name(rrset.get("name") or "", zone_name)
            key = (norm_name, normalize_record_type(rrset.get("type")))
            existing[key] = rrset

        # Group configured records by (name, type): Hetzner stores every value
        # for a given name/type pair (multiple TXT strings, multiple MX/CAA
        # entries, etc.) as a single RRSet, so entries sharing a key must be
        # merged into one combined RRSet instead of being synced independently
        # (which would make each entry overwrite the others).
        groups = {}
        for r in zone["records"]:
            group_key = (r["name"], normalize_record_type(r["type"]))
            groups.setdefault(group_key, []).append(r)

        for (record_name, record_type), group_records in groups.items():
            ttl = cfg.global_cfg.get("ttl_default", 300)
            for r in group_records:
                if r.get("ttl") is not None:
                    ttl = r["ttl"]
                    break

            # Build the records array for the API, combining every entry
            # configured under this (name, type) into one RRSet.
            records = []
            for r in group_records:
                value = ip if r["mode"] == "dynamic-ip" else r["value"]
                if record_type == "TXT":
                    # TXT records need special formatting (quotes and splitting)
                    formatted = format_txt_records(value)
                    records.extend(formatted)
                    logger.debug(f"TXT record formatted: {formatted[0]['value'][:80]}...")
                else:
                    records.append({"value": value})

            key = (record_name, record_type)

            try:
                if key in existing:
                    # RRSet exists - check if update needed
                    current_records = existing[key].get("records", [])
                    current_values = [rec.get("value") for rec in current_records]
                    new_values = [rec.get("value") for rec in records]

                    # Compare values (handle single record case)
                    needs_update = False
                    if len(current_values) != len(new_values):
                        needs_update = True
                    elif len(new_values) == 1 and len(current_values) == 1:
                        if current_values[0] != new_values[0]:
                            needs_update = True
                    else:
                        if sorted(current_values) != sorted(new_values):
                            needs_update = True

                    if needs_update:
                        api.set_records(zone_name, record_name, record_type, records, ttl)
                    else:
                        logger.debug(f"Record {record_name} ({record_type}) unchanged")
                else:
                    # RRSet doesn't exist - create it (unless CNAME vs other type at same label)
                    blocking = cname_label_conflict_type(
                        existing_rrsets, zone_name, record_name, record_type
                    )
                    if blocking:
                        logger.error(
                            "Skipping %s (%s): conflicts with existing %s at the same name "
                            "(delete the %s RRSet in Hetzner DNS or change this config entry).",
                            record_name,
                            record_type,
                            blocking,
                            blocking,
                        )
                    else:
                        logger.info(
                            f"Creating new record: {record_name}.{zone_name} ({record_type})"
                        )
                        api.create_rrset(
                            zone_name, record_name, record_type, records, ttl
                        )

            except Exception as e:
                logger.error(f"Failed to sync record {record_name} ({record_type}): {e}")

        if sync_mode == "strict":
            handle_extra_records(api, zone_name, existing, set(groups.keys()), confirm_delete)
