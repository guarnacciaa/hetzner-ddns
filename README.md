# Hetzner DDNS

**Dynamic DNS client for Hetzner Cloud DNS** - Keep your DNS records automatically updated with your current public IP address.

---

## What is this?

If you have a home internet connection, your public IP address probably changes from time to time (this is called a "dynamic IP"). This tool automatically detects when your IP changes and updates your DNS records at Hetzner, so your domain always points to the right place.

**In simple terms:** Your domain (like `example.com`) will always point to your home computer, even when your internet provider changes your IP address.

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-domain support** | Manage DNS records for multiple domains at once |
| **Multi-record support** | Update multiple DNS records per domain (e.g., `@`, `www`, `mail`) |
| **Dynamic IP mode** | Automatically update records with your current public IP |
| **Static mode** | Keep certain records fixed (useful for CNAME, MX, etc.) |
| **Environment variables** | Keep sensitive data (API tokens) out of config files |
| **Container-ready** | Works with Docker, Podman, and Kubernetes |
| **Graceful shutdown** | Properly handles stop signals |
| **Configurable interval** | Choose how often to check for IP changes |
| **Detailed logging** | See exactly what's happening |

---

## Supported DNS Record Types

| Type | Description | Example Use |
|------|-------------|-------------|
| `A` | IPv4 address | Point domain to your server |
| `AAAA` | IPv6 address | Point domain to IPv6 server |
| `CNAME` | Alias to another domain | `www` pointing to `example.com` |
| `TXT` | Text record | SPF, verification records |
| `MX` | Mail server | Email routing |
| `NS` | Nameserver | DNS delegation |
| `SRV` | Service location | VoIP, gaming servers |
| `CAA` | Certificate authority | SSL certificate control |

---

## Quick Start Guide

### Step 1: Get your Hetzner Cloud API Token

1. Go to [Hetzner Cloud Console](https://console.hetzner.cloud/)
2. Select your project (or create one)
3. Go to **Security** then **API Tokens**
4. Click **Generate API Token**
5. Give it a name (e.g., "DDNS") and select **Read and Write** permissions
6. **Copy the token** - you will not be able to see it again!

### Step 2: Make sure your domain is in Hetzner DNS

1. In Hetzner Cloud Console, go to **DNS**
2. Your domain should be listed there (e.g., `example.com`)
3. If not, add it by clicking **Add Zone**

### Step 3: Create your configuration file

```bash
# Copy the example configuration
cp config/config.example.json config/config.json
```

Edit `config/config.json` with your domains and records (see Configuration section below).

### Step 4: Run with Docker

```bash
# Build the container
docker build -t hetzner-ddns .

# Run it
docker run -d \
  --name hetzner-ddns \
  --restart unless-stopped \
  -e HETZNER_API_TOKEN="your-api-token-here" \
  -v $(pwd)/config:/config:ro \
  hetzner-ddns
```

That is it! The container will now check your IP every 5 minutes and update your DNS records when it changes.

---

## Configuration

The configuration file is a JSON file with two main sections: `global` (general settings) and `zones` (your domains and records).

### Full Configuration Example

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN",
    "ip_check_url": "https://ifconfig.me",
    "check_interval_seconds": 300,
    "ttl_default": 300
  },
  "zones": [
    {
      "name": "example.com",
      "records": [
        { "name": "@", "type": "A", "mode": "dynamic-ip" },
        { "name": "www", "type": "A", "mode": "dynamic-ip" },
        { "name": "vpn", "type": "A", "mode": "dynamic-ip", "ttl": 60 },
        {
          "name": "mail",
          "type": "CNAME",
          "mode": "static",
          "value": "mail.provider.com."
        }
      ]
    },
    {
      "name": "another-domain.net",
      "records": [
        { "name": "@", "type": "A", "mode": "dynamic-ip" }
      ]
    }
  ]
}
```

### Global Settings

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `api_token` | **Yes** | - | Your Hetzner Cloud API token |
| `check_interval_seconds` | **Yes** | - | How often to check for IP changes (minimum: 60) |
| `ip_check_url` | No | `https://ifconfig.me` | Service to detect your public IP |
| `ttl_default` | No | `300` | Default TTL for records (in seconds) |

### Zone Settings

| Setting | Required | Description |
|---------|----------|-------------|
| `name` | **Yes** | Your domain name (e.g., `example.com`) |
| `records` | **Yes** | List of DNS records to manage |

### Record Settings

| Setting | Required | Description |
|---------|----------|-------------|
| `name` | **Yes** | Record name: use `@` for the domain itself, or a subdomain like `www` |
| `type` | **Yes** | DNS record type: `A`, `AAAA`, `CNAME`, `TXT`, `MX`, `NS`, `SRV`, `CAA` |
| `mode` | **Yes** | Either `dynamic-ip` or `static` |
| `value` | Only for `static` | The fixed value for static records |
| `ttl` | No | Override the default TTL for this record |

### Record Modes

#### dynamic-ip Mode

The record value is automatically set to your current public IP address.

```json
{ "name": "www", "type": "A", "mode": "dynamic-ip" }
```

#### static Mode

The record value is fixed and will not change. Useful for CNAME, MX, TXT records.

```json
{ "name": "mail", "type": "CNAME", "mode": "static", "value": "mail.google.com." }
```

**Note:** For CNAME records pointing to external domains, include the trailing dot (e.g., `mail.google.com.`)

---

## Using Environment Variables

You can use environment variables for sensitive values like API tokens. Use the `ENV:` prefix:

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN"
  }
}
```

This tells the application to read the value from the `HETZNER_API_TOKEN` environment variable.

**Benefits:**
- Keep secrets out of configuration files
- Different tokens for different environments (dev, prod)
- Works well with Docker secrets and Kubernetes

---

## Running the Container

### With Docker

```bash
# Basic run
docker run -d \
  --name hetzner-ddns \
  --restart unless-stopped \
  -e HETZNER_API_TOKEN="your-token-here" \
  -v /path/to/config:/config:ro \
  hetzner-ddns

# View logs
docker logs -f hetzner-ddns

# Stop
docker stop hetzner-ddns

# Remove
docker rm hetzner-ddns
```

### With Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: "3.8"
services:
  hetzner-ddns:
    build: .
    container_name: hetzner-ddns
    restart: unless-stopped
    environment:
      - HETZNER_API_TOKEN=${HETZNER_API_TOKEN}
    volumes:
      - ./config:/config:ro
```

Then run:

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### With Podman

```bash
# Build
podman build -t hetzner-ddns .

# Run
podman run -d \
  --name hetzner-ddns \
  -e HETZNER_API_TOKEN="your-token-here" \
  -v ./config:/config:ro,Z \
  hetzner-ddns
```

---

## Common Configuration Examples

### Example 1: Simple Home Server

Update your main domain and www subdomain with your home IP:

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN",
    "check_interval_seconds": 300,
    "ttl_default": 300
  },
  "zones": [
    {
      "name": "mysite.com",
      "records": [
        { "name": "@", "type": "A", "mode": "dynamic-ip" },
        { "name": "www", "type": "A", "mode": "dynamic-ip" }
      ]
    }
  ]
}
```

### Example 2: VPN Server with Fast Updates

For a VPN server, you want quick updates when IP changes:

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN",
    "check_interval_seconds": 60,
    "ttl_default": 60
  },
  "zones": [
    {
      "name": "mysite.com",
      "records": [
        { "name": "vpn", "type": "A", "mode": "dynamic-ip", "ttl": 60 }
      ]
    }
  ]
}
```

### Example 3: Multiple Domains

Manage records across multiple domains:

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN",
    "check_interval_seconds": 300,
    "ttl_default": 300
  },
  "zones": [
    {
      "name": "personal-site.com",
      "records": [
        { "name": "@", "type": "A", "mode": "dynamic-ip" },
        { "name": "www", "type": "A", "mode": "dynamic-ip" }
      ]
    },
    {
      "name": "work-project.net",
      "records": [
        { "name": "@", "type": "A", "mode": "dynamic-ip" },
        { "name": "api", "type": "A", "mode": "dynamic-ip" }
      ]
    },
    {
      "name": "gaming-server.org",
      "records": [
        { "name": "mc", "type": "A", "mode": "dynamic-ip" },
        { "name": "discord", "type": "A", "mode": "dynamic-ip" }
      ]
    }
  ]
}
```

### Example 4: Mixed Dynamic and Static Records

Combine dynamic IP records with static CNAME/MX records:

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN",
    "check_interval_seconds": 300,
    "ttl_default": 300
  },
  "zones": [
    {
      "name": "mycompany.com",
      "records": [
        { "name": "@", "type": "A", "mode": "dynamic-ip" },
        { "name": "www", "type": "A", "mode": "dynamic-ip" },
        { "name": "office", "type": "A", "mode": "dynamic-ip" },
        {
          "name": "mail",
          "type": "CNAME",
          "mode": "static",
          "value": "ghs.google.com.",
          "ttl": 3600
        },
        {
          "name": "@",
          "type": "MX",
          "mode": "static",
          "value": "10 mail.mycompany.com.",
          "ttl": 3600
        }
      ]
    }
  ]
}
```

---

## Validating Your Configuration

Before running, you can validate your configuration file:

```bash
python scripts/validate-config.py config/config.json
```

Output on success:

```
Configuration valid: config/config.json
  2 zone(s), 6 record(s) configured
```

Output on error:

```
Schema validation failed: 'records' is a required property
  Path: zones > 0
```

---

## Troubleshooting

### "Environment variable 'X' not set"

You forgot to pass the environment variable to Docker:

```bash
# Wrong - variable not passed
docker run hetzner-ddns

# Correct - pass the variable
docker run -e HETZNER_API_TOKEN="your-token" hetzner-ddns
```

### "Config file not found"

The config volume is not mounted correctly:

```bash
# Make sure the path is correct
docker run -v /absolute/path/to/config:/config:ro hetzner-ddns
```

### "401 Unauthorized" or "403 Forbidden"

Your API token is invalid or does not have write permissions:

1. Check the token is correct
2. Make sure the token has **Read and Write** permissions
3. Verify the domain is in your Hetzner Cloud project

### Records not updating

Check the logs to see what is happening:

```bash
docker logs hetzner-ddns
```

Common issues:

- The IP has not actually changed
- The record name/type does not match exactly
- API rate limiting (wait a few minutes)

### Permission denied on config file

On SELinux systems (Fedora, RHEL), add `:Z` to the volume mount:

```bash
docker run -v ./config:/config:ro,Z hetzner-ddns
```

---

## How It Works

1. **Startup**: Loads configuration, validates settings
2. **IP Check**: Contacts the IP check service (default: ifconfig.me) to get your current public IP
3. **Compare**: Checks if the IP has changed since last check
4. **Update**: If IP changed, updates all configured DNS records via Hetzner Cloud API
5. **Wait**: Sleeps for the configured interval
6. **Repeat**: Goes back to step 2

The application handles signals (SIGTERM, SIGINT) gracefully, completing any in-progress updates before shutting down.

---

## API Reference

This tool uses the [Hetzner Cloud API](https://docs.hetzner.cloud/) for DNS management. Specifically:

- `GET /zones/{zone}/rrsets` - List all record sets
- `POST /zones/{zone}/rrsets` - Create new record set
- `POST /zones/{zone}/rrsets/{name}/{type}/actions/set_records` - Update records

---

## License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

You are free to use, modify, and distribute this software, but any derivative work must also be released under GPL-3.0. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Look at the container logs
3. Open an issue on GitHub with:
   - Your configuration (remove sensitive data!)
   - The error message
   - Container logs
