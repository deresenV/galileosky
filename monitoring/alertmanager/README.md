# Alertmanager

Prometheus evaluates `monitoring/prometheus/alerts.yml` every 15 seconds and
sends active alerts to `alertmanager:9093` on the `monitoring` Docker network.
Existing recording rules in `rules.yml` remain separate.

## Validate and start

Run from the repository root:

```sh
docker compose config --quiet
docker compose run --rm --no-deps --entrypoint amtool alertmanager check-config /etc/alertmanager/alertmanager.yml
docker compose run --rm --no-deps --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml
docker compose up -d --no-deps alertmanager
docker compose up -d --no-deps prometheus
docker compose restart prometheus
```

Restart Prometheus after subsequent rule or configuration changes, too.
`--no-deps` avoids starting the listener while configuring alerts.

Open `http://SERVER_IP:9093`. State and silences persist in `alertmanager-data`.
Port 9093 provides the management UI/API; expose it only to trusted users.

The `local` receiver intentionally has no delivery integrations. Alerts appear
in the UI, but no webhook, email or Telegram message is sent. Replace or extend
this receiver when a real destination is available. Never put credentials in Git.

## Alert rules

`GalileoskyListenerDown` fires after the listener's scrape endpoint has been
unavailable for one minute. It recovers once scraping succeeds again. It does
not detect a meter that stops sending packets while the exporter remains healthy.

`GalileoskyTotalPowerHigh` fires when
`sum(galileosky_mercury_active_power{phase="sum", container_id!="12"}) >= 200`
for two continuous minutes. It excludes container 12 and uses the metric's raw
units without conversion. It recovers when the sum drops below 200. The rule
runs around the clock; no weekday/time schedule is currently applied.
Missing measurements are not proof that power has returned to normal; meter
freshness monitoring requires a separate rule and last-measurement timestamps.

## End-to-end smoke test

This optional rule tests Prometheus -> Alertmanager without depending on meters.
Use a temporary override, so the test rule cannot enter the normal deployment:

```sh
cat > /tmp/galileosky-alertmanager-smoke.yml <<'YAML'
groups:
  - name: smoke
    interval: 15s
    rules:
      - alert: AlertmanagerSmokeTest
        expr: vector(1)
        labels:
          severity: info
        annotations:
          summary: Temporary Alertmanager connectivity test
YAML
cat > /tmp/galileosky-alertmanager-override.yml <<'YAML'
services:
  prometheus:
    volumes:
      - /tmp/galileosky-alertmanager-smoke.yml:/etc/prometheus/alerts.yml:ro
YAML
docker compose -f docker-compose.yml -f /tmp/galileosky-alertmanager-override.yml up -d --no-deps prometheus
```

Within about 90 seconds after startup, `AlertmanagerSmokeTest` should appear in the UI/API:

```sh
curl -fsS http://localhost:9093/api/v2/alerts
```

Restore the production rule file after checking:

```sh
docker compose up -d --no-deps --force-recreate prometheus
rm /tmp/galileosky-alertmanager-smoke.yml /tmp/galileosky-alertmanager-override.yml
```

Notifications may later be restricted to Monday-Friday, 07:00-21:00 with an
Alertmanager time interval in `Europe/Moscow`. This limits delivery only;
limiting rule evaluation itself requires a schedule condition in the rule.

## Deliver webhooks to extend_asics

Generate the URL and a reusable shared token (the script does not print it):

```sh
python3 monitoring/alertmanager/configure_webhook.py
```

By default the backend is on the same host, listening on 8020. For another host:

```sh
python3 monitoring/alertmanager/configure_webhook.py --url https://BACKEND_HOST/api/notifications/alertmanager
```

The ignored `secrets` directory contains `webhook_url`, `webhook_token`, and
`backend-webhook.env`. Copy the env assignment into `extend_asics/backend/.env`
and recreate its backend container to apply the environment and create the new
table. Keep any `ALERTMANAGER_WEBHOOK_TOKEN_FILE` setting empty unless deliberately
using a mounted file instead of the environment token. Only then enable delivery:

```sh
docker compose -f docker-compose.yml -f docker-compose.webhooks.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.webhooks.yml run --rm --no-deps --entrypoint amtool alertmanager check-config /etc/alertmanager/alertmanager.yml
docker compose -f docker-compose.yml -f docker-compose.webhooks.yml up -d --no-deps --force-recreate alertmanager
docker compose restart prometheus
```

Use both Compose files for later Alertmanager updates. The override replaces the
local receiver with `extend-asics`, enables `send_resolved`, and adds
`host.docker.internal:host-gateway` for same-host delivery on Ubuntu.

The URL and token files must be readable by Alertmanager's container user
(`nobody`); the helper uses 0644 for these bind-mounted files. Restrict access to
the host directory as appropriate for your deployment. The backend env snippet
is 0600 and is never committed. The helper reuses the existing token on reruns.

The webhook contains individual `firing` and `resolved` alerts. The power rule
also supplies `annotations.current_value` and `annotations.threshold` in raw
metric units. Backend consumers can read `/api/notifications/` with their normal
JWT and `stats_access` permission; `?status=firing` filters active occurrences.

Delivery errors appear in `docker compose logs alertmanager`. Ingestion returns
503 if the backend token is not configured and 401 for a wrong token. Resolve
these settings before expecting notifications. See the backend's
`backend/ALERTMANAGER_WEBHOOK.md` for its API and deployment instructions.
