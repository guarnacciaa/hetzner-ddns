#!/usr/bin/env python3
"""Validate a Hetzner DDNS configuration file against the schema."""

import json
import sys
from pathlib import Path

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema package required. Install with: pip install jsonschema")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate-config.py <config_file>")
        print("Example: python validate-config.py config/config.json")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    schema_path = Path(__file__).parent.parent / "config" / "schema.json"

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    try:
        with open(schema_path) as f:
            schema = json.load(f)

        with open(config_path) as f:
            config = json.load(f)

        validate(config, schema)
        print(f"✓ Configuration valid: {config_path}")

        # Additional checks
        zones_count = len(config.get("zones", []))
        records_count = sum(len(z.get("records", [])) for z in config.get("zones", []))
        print(f"  → {zones_count} zone(s), {records_count} record(s) configured")

    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"✗ Schema validation failed: {e.message}")
        print(f"  → Path: {' > '.join(str(p) for p in e.absolute_path)}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
