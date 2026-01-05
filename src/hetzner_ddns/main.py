import sys
import time
import signal
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m hetzner_ddns.main <config_path>")
        sys.exit(1)

    setup_logging()
    logger.info("Hetzner DDNS starting...")

    try:
        cfg = load_config(sys.argv[1])
        logger.info(f"Loaded configuration with {len(cfg.zones)} zone(s)")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    last_ip = None
    interval = cfg.global_cfg["check_interval_seconds"]

    logger.info(f"Starting sync loop (interval: {interval}s)")

    while running:
        try:
            ip = get_public_ip(cfg.global_cfg)

            if ip != last_ip:
                if last_ip is not None:
                    logger.info(f"IP changed: {last_ip} -> {ip}")
                else:
                    logger.info(f"Current IP: {ip}")

                sync_all(cfg, ip)
                last_ip = ip
                logger.info("Sync completed successfully")

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
