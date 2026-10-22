import logging
from urllib.parse import quote

import requests

BASE = "https://api.hetzner.cloud/v1"
logger = logging.getLogger(__name__)


def _rrset_path_name(name: str) -> str:
    """
    Encode an RRSet name for use in a URL path segment.

    The apex alias "@" must be sent literally: Hetzner's API expects it
    unescaped and does not match it against a percent-encoded "%40",
    which otherwise causes mutation endpoints (set_records, update_rrset,
    delete_rrset) to respond 404 even though the apex RRSet exists.
    """
    name = str(name)
    if name == "@":
        return name
    return quote(name, safe="*")  # Hetzner vuole l asterisco letterale: %2A risponde 404


class HetznerCloudAPI:
    """Client for Hetzner Cloud DNS API using RRSets."""

    def __init__(self, token):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"
        self.s.headers["Content-Type"] = "application/json"

    def get_rrsets(self, zone):
        """
        Fetch all RRSets for a zone.
        
        Args:
            zone: Zone ID or name (e.g., "example.com")
        
        Returns:
            List of RRSet objects
        """
        per_page = 100
        page = 1
        all_rrsets = []
        while True:
            resp = self.s.get(
                f"{BASE}/zones/{zone}/rrsets",
                params={"page": page, "per_page": per_page},
            )
            resp.raise_for_status()
            data = resp.json()
            batch = data.get("rrsets", [])
            all_rrsets.extend(batch)
            pagination = (data.get("meta") or {}).get("pagination") or {}
            next_page = pagination.get("next_page")
            if next_page is not None:
                page = next_page
                continue
            if len(batch) < per_page:
                break
            page += 1
        return all_rrsets

    def get_rrset(self, zone, name, rtype):
        """
        Get a specific RRSet.
        
        Args:
            zone: Zone ID or name
            name: Record name (use "@" for apex)
            rtype: Record type (A, AAAA, CNAME, etc.)
        
        Returns:
            RRSet object or None if not found
        """
        try:
            resp = self.s.get(
                f"{BASE}/zones/{zone}/rrsets/{_rrset_path_name(name)}/{rtype}"
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("rrset")
        except requests.exceptions.HTTPError:
            return None

    def set_records(self, zone, name, rtype, records, ttl=None):
        """
        Set records for an RRSet (creates if doesn't exist, replaces if exists).
        
        Args:
            zone: Zone ID or name
            name: Record name (use "@" for apex)
            rtype: Record type (A, AAAA, CNAME, etc.)
            records: List of record values [{"value": "1.2.3.4"}]
            ttl: Optional TTL in seconds
        
        Returns:
            Action object from API
        """
        payload = {
            "records": records
        }
        if ttl is not None:
            payload["ttl"] = ttl

        url = f"{BASE}/zones/{zone}/rrsets/{_rrset_path_name(name)}/{rtype}/actions/set_records"
        logger.info(f"API Request: POST {url}")
        logger.info(f"API Payload records: {[r['value'][:60] + '...' if len(r['value']) > 60 else r['value'] for r in records]}")

        resp = self.s.post(url, json=payload)

        if resp.status_code == 404:
            # RRSet listing can be briefly out of sync with the mutation
            # endpoints (e.g. right after manual deletion in the console),
            # so an RRSet we believed existed may actually be gone. Fall
            # back to creating it, mirroring create_rrset's 409 fallback.
            logger.info(
                "RRSet not found (%s %s), creating instead", name, rtype
            )
            return self.create_rrset(zone, name, rtype, records, ttl)

        if not resp.ok:
            logger.error(f"API Response {resp.status_code}: {resp.text}")
            raise Exception(f"API Error {resp.status_code}: {resp.text}")
        logger.info(f"Set records for {name}.{zone} ({rtype}): {[r['value'][:50] + '...' if len(r['value']) > 50 else r['value'] for r in records]}")
        return resp.json().get("action")

    def create_rrset(self, zone, name, rtype, records, ttl=None):
        """
        Create a new RRSet.
        
        Args:
            zone: Zone ID or name
            name: Record name (use "@" for apex)
            rtype: Record type
            records: List of record values
            ttl: Optional TTL
        """
        payload = {
            "name": name,
            "type": rtype,
            "records": records
        }
        if ttl is not None:
            payload["ttl"] = ttl

        resp = self.s.post(f"{BASE}/zones/{zone}/rrsets", json=payload)
        if resp.status_code == 409:
            logger.info(
                "RRSet already exists (%s %s), applying set_records instead",
                name,
                rtype,
            )
            self.set_records(zone, name, rtype, records, ttl)
            return None
        if not resp.ok:
            logger.error(
                "create_rrset failed %s %s/%s: %s",
                resp.status_code,
                name,
                rtype,
                resp.text,
            )
        resp.raise_for_status()
        logger.info(f"Created RRSet: {name}.{zone} ({rtype})")
        return resp.json().get("rrset")

    def update_rrset(self, zone, name, rtype, records=None, ttl=None):
        """
        Update an existing RRSet.
        
        Args:
            zone: Zone ID or name
            name: Record name
            rtype: Record type
            records: Optional new records list
            ttl: Optional new TTL
        """
        payload = {}
        if records is not None:
            payload["records"] = records
        if ttl is not None:
            payload["ttl"] = ttl

        resp = self.s.put(
            f"{BASE}/zones/{zone}/rrsets/{_rrset_path_name(name)}/{rtype}",
            json=payload,
        )
        resp.raise_for_status()
        logger.info(f"Updated RRSet: {name}.{zone} ({rtype})")
        return resp.json().get("rrset")

    def delete_rrset(self, zone, name, rtype):
        """
        Delete an RRSet.
        
        Args:
            zone: Zone ID or name
            name: Record name
            rtype: Record type
        """
        resp = self.s.delete(
            f"{BASE}/zones/{zone}/rrsets/{_rrset_path_name(name)}/{rtype}"
        )
        resp.raise_for_status()
        logger.info(f"Deleted RRSet: {name}.{zone} ({rtype})")
