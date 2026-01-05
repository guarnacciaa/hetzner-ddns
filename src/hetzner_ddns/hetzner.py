import logging
import requests

BASE = "https://api.hetzner.cloud/v1"
logger = logging.getLogger(__name__)


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
        resp = self.s.get(f"{BASE}/zones/{zone}/rrsets")
        resp.raise_for_status()
        return resp.json().get("rrsets", [])

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
            resp = self.s.get(f"{BASE}/zones/{zone}/rrsets/{name}/{rtype}")
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

        resp = self.s.post(
            f"{BASE}/zones/{zone}/rrsets/{name}/{rtype}/actions/set_records",
            json=payload
        )
        resp.raise_for_status()
        logger.info(f"Set records for {name}.{zone} ({rtype}): {[r['value'] for r in records]}")
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

        resp = self.s.put(f"{BASE}/zones/{zone}/rrsets/{name}/{rtype}", json=payload)
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
        resp = self.s.delete(f"{BASE}/zones/{zone}/rrsets/{name}/{rtype}")
        resp.raise_for_status()
        logger.info(f"Deleted RRSet: {name}.{zone} ({rtype})")
