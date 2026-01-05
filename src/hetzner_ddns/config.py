import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_env(value):
    """
    Resolve environment variable references in config values.
    
    Supports syntax: "ENV:VARIABLE_NAME"
    """
    if isinstance(value, str) and value.startswith("ENV:"):
        env_var = value[4:]
        resolved = os.getenv(env_var)
        if resolved is None:
            raise ValueError(f"Environment variable '{env_var}' not set")
        return resolved
    return value


def load_config(path):
    """
    Load and validate configuration from JSON file.
    
    Args:
        path: Path to the JSON configuration file
    
    Returns:
        Config object with global_cfg and zones attributes
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required fields are missing or invalid
        json.JSONDecodeError: If JSON is malformed
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path) as f:
        raw = json.load(f)

    # Resolve environment variables in global config
    for k, v in raw["global"].items():
        raw["global"][k] = resolve_env(v)

    # Validate required fields
    if not raw["global"].get("api_token"):
        raise ValueError("API token is required (global.api_token)")

    if not raw.get("zones"):
        raise ValueError("At least one zone must be configured")

    for zone in raw["zones"]:
        if not zone.get("name"):
            raise ValueError("Each zone must have a 'name' field")
        if not zone.get("records"):
            raise ValueError(f"Zone '{zone.get('name')}' has no records configured")

        # Validate each record
        for record in zone["records"]:
            if record.get("mode") == "static" and not record.get("value"):
                raise ValueError(
                    f"Record '{record.get('name')}' in zone '{zone['name']}' "
                    "uses static mode but has no 'value' specified"
                )

    logger.info(f"Configuration loaded from {path}")

    return type("Config", (), {
        "global_cfg": raw["global"],
        "zones": raw["zones"]
    })
