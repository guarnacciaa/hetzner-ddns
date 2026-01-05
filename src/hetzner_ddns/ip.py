import logging
import requests

logger = logging.getLogger(__name__)


def get_public_ip(global_cfg):
    """Get the current public IP address."""
    url = global_cfg.get("ip_check_url", "https://ifconfig.me")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        ip = r.text.strip()
        logger.debug(f"Current public IP: {ip}")
        return ip
    except Exception as e:
        logger.error(f"Failed to get public IP from {url}: {e}")
        raise
