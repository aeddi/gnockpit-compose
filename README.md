# gnockpit-compose

Docker Compose setup for [gnockpit](https://github.com/gnoverse/gnockpit) — a real-time gno.land validator monitoring dashboard — with external notification support via Discord, Telegram, Signal, and more.

## Prerequisites

- Docker and Docker Compose (v2.20+)
- A gnoland node accessible from the host (e.g., RPC on `localhost:26657`)

## Quick Start

1. **Copy and edit the configuration:**

   ```bash
   cp .env.example .env
   # Edit .env — set paths, container name, and notification URLs
   ```

   Key settings in `.env`:

   | Variable | Default | Description |
   |----------|---------|-------------|
   | `GNOCKPIT_CONTEXT` | upstream `main` | Git repo + ref to build (see [Build Options](#build-options)) |
   | `RPC_URL` | `http://host.docker.internal:26657` | gnoland RPC endpoint |
   | `GNOLAND_DATA_DIR` | `./gnoland-data` | Path to gnoland data directory |
   | `GENESIS_PATH` | `./gnoland-data/genesis.json` | Path to genesis.json |
   | `GNOLAND_CONTAINER` | `gnoland` | Docker container name (for log streaming) |
   | `NOTIFY_URLS` | (empty) | Comma-separated [Shoutrrr](https://containrrr.dev/shoutrrr/latest/) notification URLs |

2. **Start:**

   ```bash
   docker compose up -d gnockpit
   ```

3. **Open the dashboard:** http://localhost:8080

## Build Options

gnockpit is built from source at `docker compose build` time. The `GNOCKPIT_CONTEXT` variable controls what to build:

```bash
# Default — upstream main branch
GNOCKPIT_CONTEXT=https://github.com/gnoverse/gnockpit.git#main

# Specific branch or tag
GNOCKPIT_CONTEXT=https://github.com/gnoverse/gnockpit.git#v1.2.0

# A fork
GNOCKPIT_CONTEXT=https://github.com/yourname/gnockpit.git#feature-branch

# Specific commit
GNOCKPIT_CONTEXT=https://github.com/gnoverse/gnockpit.git#abc1234

# Local source directory (for development)
GNOCKPIT_CONTEXT=../gnockpit
```

## Notifications

Notifications are configured via the `NOTIFY_URLS` variable in `.env` — a comma-separated list of [Shoutrrr](https://containrrr.dev/shoutrrr/latest/) URLs:

```bash
# Single destination
NOTIFY_URLS=discord://token@webhookid

# Multiple destinations
NOTIFY_URLS=discord://token@webhookid,telegram://token@telegram?chats=@channel
```

| Service | URL Format |
|---------|------------|
| Discord | `discord://token@webhookid` |
| Telegram | `telegram://token@telegram?chats=@channel` |
| Slack | `slack://token-a/token-b/token-c` |
| Signal | `generic://signal-api:8080/v2/send?template=json&disabletls=yes&$number=%2Bsender&$recipient=%2Btarget` |

### Discord

1. Server Settings → Integrations → Webhooks → New Webhook
2. Pick a channel, copy the webhook URL: `https://discord.com/api/webhooks/WEBHOOK_ID/TOKEN`
3. Convert to Shoutrrr format: `discord://TOKEN@WEBHOOK_ID`

### Signal

Signal requires a [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) sidecar (included in this compose).

1. **Start only the signal-api service:**

   ```bash
   docker compose up -d signal-api
   ```

2. **Link your Signal account** by generating a QR code:

   ```bash
   curl -s http://localhost:8081/v1/qrcodelink?device_name=gnockpit | jq -r .
   ```

   Scan with your Signal app: Settings → Linked Devices → Link New Device.

3. **Verify the link:**

   ```bash
   curl -s http://localhost:8081/v1/accounts | jq .
   ```

4. **Add Signal to `NOTIFY_URLS`** in `.env`:

   ```bash
   NOTIFY_URLS=generic://signal-api:8080/v2/send?template=json&disabletls=yes&$number=%2B<sender>&$recipient=%2B<target>
   ```

   Replace `<sender>` with your linked Signal number and `<target>` with the recipient (digits only, no `+`). `%2B` is the URL-encoded `+`.

5. **Restart gnockpit:**

   ```bash
   docker compose up -d gnockpit
   ```

### Test Notifications

```bash
# List configured channels
curl -s http://localhost:8080/api/notify/channels | jq .

# Send test to all channels
curl -s -X POST http://localhost:8080/api/notify/test \
  -H 'Content-Type: application/json' -d '{}' | jq .

# Send to a specific channel with custom message
curl -s -X POST http://localhost:8080/api/notify/test \
  -H 'Content-Type: application/json' \
  -d '{"channels":[0],"message":"Hello from gnockpit!"}' | jq .
```

## Architecture

```
 Host machine
 ┌──────────────────────────┐
 │  gnoland :26657          │
 └─────────┬────────────────┘
           │ host.docker.internal
 ┌─────────▼────────────────┐
 │  Docker (gnockpit)       │
 │                          │
 │  ┌───────────────┐       │
 │  │   gnockpit    │──────────► Discord / Telegram / Slack
 │  │   :8080       │       │   (direct HTTPS)
 │  └───────┬───────┘       │
 │          │               │
 │  ┌───────▼───────┐       │
 │  │  signal-api   │──────────► Signal
 │  │  :8080        │       │   (via sidecar)
 │  └───────────────┘       │
 └──────────────────────────┘
```
