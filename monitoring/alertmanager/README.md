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
