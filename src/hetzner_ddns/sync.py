import logging
from hetzner_ddns.hetzner import HetznerCloudAPI
from hetzner_ddns.txt_formatter import format_txt_value

logger = logging.getLogger(__name__)


def sync_all(cfg, ip):
    """
    Synchronize all DNS records across all configured zones.
    
    Args:
        cfg: Configuration object with global_cfg and zones
        ip: Current public IP address
    """
    api = HetznerCloudAPI(cfg.global_cfg["api_token"])

    for zone in cfg.zones:
        zone_name = zone["name"]
        logger.debug(f"Processing zone: {zone_name}")

        try:
            # Fetch existing RRSets for this zone
            existing_rrsets = api.get_rrsets(zone_name)
        except Exception as e:
            logger.error(f"Failed to fetch RRSets for zone {zone_name}: {e}")
            continue

        # Build lookup map: (name, type) -> rrset
        existing = {}
        for rrset in existing_rrsets:
            key = (rrset["name"], rrset["type"])
            existing[key] = rrset

        # Process each configured record
        for r in zone["records"]:
            record_name = r["name"]
            record_type = r["type"]
            ttl = r.get("ttl", cfg.global_cfg.get("ttl_default", 300))

            # Determine the value based on mode
            if r["mode"] == "dynamic-ip":
                value = ip
            else:
                value = r["value"]

            # Format TXT records (auto-quote and split long values)
            if record_type == "TXT":
                value = format_txt_value(value)

            # Build the records array for the API
            records = [{"value": value}]

            key = (record_name, record_type)

            try:
                if key in existing:
                    # RRSet exists - check if update needed
                    current_records = existing[key].get("records", [])
                    current_values = [rec.get("value") for rec in current_records]

                    if value not in current_values or len(current_values) != 1:
                        # Value changed or multiple values exist - set to our single value
                        api.set_records(zone_name, record_name, record_type, records, ttl)
                    else:
                        logger.debug(f"Record {record_name} ({record_type}) unchanged")
                else:
                    # RRSet doesn't exist - create it
                    logger.info(f"Creating new record: {record_name}.{zone_name} ({record_type})")
                    api.create_rrset(zone_name, record_name, record_type, records, ttl)

            except Exception as e:
                logger.error(f"Failed to sync record {record_name} ({record_type}): {e}")
