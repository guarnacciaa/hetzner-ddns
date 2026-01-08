import sys
import time
import signal
import hashlib
import logging
from hetzner_ddns.config import load_config
from hetzner_ddns.ip import get_public_ip
from hetzner_ddns.sync import sync_all
from hetzner_ddns.logging import setup_logging

logger = logging.getLogger(__name__)

running = True


def shutdown(*_):
    global running
    logger.info("Shutdown signal received, stopping...")
    running = False


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)


def get_file_hash(path):
    """Calculate MD5 hash of a file to detect changes."""
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m hetzner_ddns.main <config_path>")
        sys.exit(1)

    setup_logging()
    logger.info("Hetzner DDNS starting...")

    config_path = sys.argv[1]
    
    try:
        cfg = load_config(config_path)
        logger.info(f"Loaded configuration with {len(cfg.zones)} zone(s)")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    last_ip = None
    last_config_hash = get_file_hash(config_path)
    interval = cfg.global_cfg["check_interval_seconds"]

    logger.info(f"Starting sync loop (interval: {interval}s)")

    while running:
        try:
            # Check if config file has changed
            current_hash = get_file_hash(config_path)
            if current_hash and current_hash != last_config_hash:
                logger.info("Configuration file changed, reloading...")
                try:
                    cfg = load_config(config_path)
                    last_config_hash = current_hash
                    interval = cfg.global_cfg["check_interval_seconds"]
                    logger.info(f"Configuration reloaded: {len(cfg.zones)} zone(s), interval: {interval}s")
                except Exception as e:
                    logger.error(f"Failed to reload config: {e} (keeping previous config)")

            ip = get_public_ip(cfg.global_cfg)

            if ip != last_ip:
                if last_ip is not None:
                    logger.info(f"IP changed: {last_ip} -> {ip}")
                else:
                    logger.info(f"Current IP: {ip}")
                last_ip = ip

            # Always sync all records on every cycle
            # This ensures new records are created and static records are maintained
            sync_all(cfg, ip)
            logger.info("Sync cycle completed, sleeping for %d seconds", interval)

        except Exception as e:
            logger.error(f"Error during sync cycle: {e}")

        # Sleep in small intervals to allow graceful shutdown
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)

    logger.info("Hetzner DDNS stopped")


if __name__ == "__main__":
    main()
