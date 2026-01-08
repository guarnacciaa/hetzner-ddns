# Hetzner DDNS

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://www.python.org/)

**Dynamic DNS client for Hetzner Cloud DNS** - Keep your DNS records automatically updated with your current public IP address.

> **Perfect for:** Home servers, self-hosting, homelab, NAS, Raspberry Pi, VPN servers, game servers, and any setup with a dynamic IP address.

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
| **Auto TXT formatting** | TXT records are automatically quoted and split (DKIM support) |
| **Environment variables** | Keep sensitive data (API tokens) out of config files |
| **Container-ready** | Works with Docker, Podman, and Kubernetes |
| **Graceful shutdown** | Properly handles stop signals |
| **Configurable interval** | Choose how often to check for IP changes |
| **Hot config reload** | Changes to config.json are detected automatically |
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
7. **Save the token** as an environment variable (you will need it later):

```bash
export HETZNER_API_TOKEN="your-token-here"
```

**Tip:** Add this line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

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
# Make sure you exported the token (from Step 1)
echo $HETZNER_API_TOKEN  # Should print your token

# Build the container
docker build -t hetzner-ddns .

# Run it (uses the exported environment variable)
docker run -d \
  --name hetzner-ddns \
  --restart unless-stopped \
  -e HETZNER_API_TOKEN="$HETZNER_API_TOKEN" \
  -v $(pwd)/config:/config:ro \
  hetzner-ddns

# Check the logs to make sure it's working
docker logs -f hetzner-ddns
```

That is it! The container will now check your IP every 5 minutes and update your DNS records when it changes.

**Expected output:**
```
[INFO] Hetzner DDNS starting...
[INFO] Configuration loaded from /config/config.json
[INFO] Loaded configuration with 1 zone(s)
[INFO] Starting sync loop (interval: 300s)
[INFO] Current IP: x.x.x.x
[INFO] Sync cycle completed, sleeping for 300 seconds
```

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

## DNS Record Types - Complete Examples

This section shows how to configure each supported DNS record type.

### A Record (IPv4 Address)

Points a domain or subdomain to an IPv4 address.

```json
// Dynamic - uses your current public IP
{ "name": "@", "type": "A", "mode": "dynamic-ip" }
{ "name": "www", "type": "A", "mode": "dynamic-ip" }
{ "name": "mail", "type": "A", "mode": "dynamic-ip" }

// Static - uses a fixed IP address
{ "name": "home", "type": "A", "mode": "static", "value": "192.168.1.100" }
{ "name": "server", "type": "A", "mode": "static", "value": "203.0.113.50" }
```

### AAAA Record (IPv6 Address)

Points a domain or subdomain to an IPv6 address.

```json
{ "name": "@", "type": "AAAA", "mode": "static", "value": "2001:db8::1" }
{ "name": "www", "type": "AAAA", "mode": "static", "value": "2001:db8::2" }
```

### CNAME Record (Alias)

Creates an alias from one name to another. The target must end with a dot.

```json
{ "name": "www", "type": "CNAME", "mode": "static", "value": "example.com." }
{ "name": "ftp", "type": "CNAME", "mode": "static", "value": "www.example.com." }
{ "name": "webmail", "type": "CNAME", "mode": "static", "value": "mail.example.com." }
{ "name": "autoconfig", "type": "CNAME", "mode": "static", "value": "mail.example.com." }

// Multiple subdomains pointing to the same target
{ "name": "app1", "type": "CNAME", "mode": "static", "value": "main.example.com." }
{ "name": "app2", "type": "CNAME", "mode": "static", "value": "main.example.com." }
{ "name": "api", "type": "CNAME", "mode": "static", "value": "main.example.com." }
```

**Important:** CNAME values must end with a trailing dot (`.`) when pointing to fully qualified domain names.

### MX Record (Mail Exchange)

Specifies mail servers for the domain. Format: `priority hostname.`

```json
// Single mail server
{ "name": "@", "type": "MX", "mode": "static", "value": "10 mail.example.com." }

// Multiple mail servers with priorities (lower = higher priority)
{ "name": "@", "type": "MX", "mode": "static", "value": "10 mail1.example.com." }
{ "name": "@", "type": "MX", "mode": "static", "value": "20 mail2.example.com." }

// Using external mail service
{ "name": "@", "type": "MX", "mode": "static", "value": "10 aspmx.l.google.com." }
```

### TXT Record (Text)

Stores text information. Commonly used for SPF, DKIM, DMARC, and domain verification.

**Note:** You do NOT need to add quotes around the value - the tool adds them automatically. For long values (like DKIM keys), the tool automatically splits them into 255-character chunks.

```json
// SPF record - specifies authorized mail senders
{ "name": "@", "type": "TXT", "mode": "static", "value": "v=spf1 mx ~all" }
{ "name": "@", "type": "TXT", "mode": "static", "value": "v=spf1 include:_spf.google.com ~all" }

// DMARC record - email authentication policy
{ "name": "_dmarc", "type": "TXT", "mode": "static", "value": "v=DMARC1; p=none; rua=mailto:dmarc@example.com" }
{ "name": "_dmarc", "type": "TXT", "mode": "static", "value": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com" }

// DKIM record - email signing key (automatically split if > 255 chars)
{
  "name": "default._domainkey",
  "type": "TXT",
  "mode": "static",
  "ttl": 3600,
  "value": "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxis5gph/XQtyNO1234567890FyyJ5vsxDnUa1234567890NDAl7mKSGga2ltWYwMNS8MxMv+XOpNf4Za6b2T4E4CXcu5O0Bq9QZGgzqL31234567890ipMcncmDzoDOx0OwqLz/dcuYqt3Nip12345678904/M8kQnuumF1234567890dqKugj47deQIo+RogIpBvrCF9/UVXZ1234567890X9hbpr/Xl1PSBgn1234567890A9e/k8203YDED7sc+ACc8QGL8WExZN7Q8V+5xNPBUZaIx5E6nLxvBF6Z2hLkDKG2K9qclfovGO3z+a1ryPMDmbKZWcD8rYCOF1234567890"
}

// Domain verification (Google, Microsoft, etc.)
{ "name": "@", "type": "TXT", "mode": "static", "value": "google-site-verification=abcdef123456" }
{ "name": "@", "type": "TXT", "mode": "static", "value": "MS=ms12345678" }
```

### SRV Record (Service)

Specifies location of services. Format: `priority weight port target.`

```json
// Autodiscover for email clients (Outlook)
{ "name": "_autodiscover._tcp", "type": "SRV", "mode": "static", "value": "0 5 443 mail.example.com." }

// IMAP and SMTP
{ "name": "_imaps._tcp", "type": "SRV", "mode": "static", "value": "0 1 993 mail.example.com." }
{ "name": "_submission._tcp", "type": "SRV", "mode": "static", "value": "0 1 587 mail.example.com." }

// SIP/VoIP
{ "name": "_sip._tcp", "type": "SRV", "mode": "static", "value": "10 60 5060 sip.example.com." }
{ "name": "_sip._udp", "type": "SRV", "mode": "static", "value": "10 60 5060 sip.example.com." }

// Minecraft server
{ "name": "_minecraft._tcp", "type": "SRV", "mode": "static", "value": "0 5 25565 mc.example.com." }

// XMPP/Jabber
{ "name": "_xmpp-client._tcp", "type": "SRV", "mode": "static", "value": "5 0 5222 xmpp.example.com." }
{ "name": "_xmpp-server._tcp", "type": "SRV", "mode": "static", "value": "5 0 5269 xmpp.example.com." }
```

**SRV Format Explained:** `priority weight port target`
- **priority**: Lower values = higher priority (0-65535)
- **weight**: Load balancing between same-priority servers (0-65535)
- **port**: TCP/UDP port number
- **target**: Hostname (must end with dot)

### CAA Record (Certificate Authority Authorization)

Controls which Certificate Authorities can issue SSL certificates for your domain.

```json
// Allow only Let's Encrypt
{ "name": "@", "type": "CAA", "mode": "static", "value": "0 issue \"letsencrypt.org\"" }

// Allow Let's Encrypt and report violations
{ "name": "@", "type": "CAA", "mode": "static", "value": "0 issue \"letsencrypt.org\"" }
{ "name": "@", "type": "CAA", "mode": "static", "value": "0 iodef \"mailto:security@example.com\"" }

// Allow multiple CAs
{ "name": "@", "type": "CAA", "mode": "static", "value": "0 issue \"letsencrypt.org\"" }
{ "name": "@", "type": "CAA", "mode": "static", "value": "0 issue \"digicert.com\"" }

// Wildcard certificates
{ "name": "@", "type": "CAA", "mode": "static", "value": "0 issuewild \"letsencrypt.org\"" }
```

### NS Record (Nameserver)

Delegates a subdomain to different nameservers.

```json
// Delegate subdomain to external nameservers
{ "name": "subdomain", "type": "NS", "mode": "static", "value": "ns1.externaldns.com." }
{ "name": "subdomain", "type": "NS", "mode": "static", "value": "ns2.externaldns.com." }
```

---

## Complete Email Setup Example

Here is a complete example for setting up email with SPF, DKIM, and DMARC:

```json
{
  "global": {
    "api_token": "ENV:HETZNER_API_TOKEN",
    "check_interval_seconds": 300,
    "ttl_default": 300
  },
  "zones": [
    {
      "name": "example.com",
      "records": [
        { "name": "mail", "type": "A", "mode": "dynamic-ip" },
        { "name": "@", "type": "MX", "mode": "static", "value": "10 mail.example.com." },
        { "name": "autoconfig", "type": "CNAME", "mode": "static", "value": "mail.example.com." },
        { "name": "_autodiscover._tcp", "type": "SRV", "mode": "static", "value": "0 5 443 mail.example.com." },
        { "name": "@", "type": "TXT", "mode": "static", "value": "v=spf1 mx ~all" },
        { "name": "_dmarc", "type": "TXT", "mode": "static", "value": "v=DMARC1; p=none; rua=mailto:dmarc@example.com" },
        {
          "name": "default._domainkey",
          "type": "TXT",
          "mode": "static",
          "ttl": 3600,
          "value": "v=DKIM1; k=rsa; p=YOUR_DKIM_PUBLIC_KEY_HERE"
        }
      ]
    }
  ]
}
```

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

1. Create a `docker-compose.yml` file:

```yaml
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

2. Create a `.env` file in the same directory (to store your token):

```bash
# .env file
HETZNER_API_TOKEN=your-token-here
```

**Important:** The `.env` file is already in `.gitignore` so it won't be committed to git.

3. Run:

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose down && docker-compose build --no-cache && docker-compose up -d
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
3. **Sync All Records**: On every cycle, syncs all configured records:
   - **Dynamic records**: Updated with current public IP
   - **Static records**: Ensured to have the configured value
   - **New records**: Automatically created if missing
   - **Unchanged records**: Skipped (no unnecessary API calls)
4. **Wait**: Sleeps for the configured interval
5. **Repeat**: Goes back to step 2

**Key Features:**
- Records are synced on every cycle, so new records added to the config are created automatically
- The tool only makes API calls when values actually need to change
- TXT records are automatically formatted with quotes and split if longer than 255 characters
- **Hot reload:** If you modify `config.json` while the container is running, changes are detected and applied automatically at the next cycle (no restart needed)

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

---

## Keywords

*For searchability: hetzner ddns, hetzner dynamic dns, hetzner dyndns, hetzner cloud dns updater, hetzner dns api, dynamic dns docker, self-hosted ddns, homelab dns, raspberry pi ddns, home server dynamic ip, hetzner api python, ddns client linux, free dynamic dns alternative, no-ip alternative, duckdns alternative, cloudflare ddns alternative for hetzner*
