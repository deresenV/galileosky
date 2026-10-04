import argparse
from pathlib import Path
import secrets
from urllib.parse import urlsplit


def configure(directory: Path, url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Expected an HTTP(S) webhook URL without credentials")
    if any(character.isspace() for character in url):
        raise ValueError("Webhook URL must not contain whitespace")
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o755)
    token_path = directory / "webhook_token"
    if token_path.exists():
        token = token_path.read_text().strip()
        if not token:
            raise ValueError("Existing webhook_token is empty")
    else:
        token = secrets.token_hex(32)
        token_path.write_text(token + "\n")
    # Alertmanager runs as nobody and must be able to read the bind-mounted files.
    token_path.chmod(0o644)
    url_path = directory / "webhook_url"
    url_path.write_text(url + "\n")
    url_path.chmod(0o644)
    env_path = directory / "backend-webhook.env"
    env_path.write_text("ALERTMANAGER_WEBHOOK_TOKEN=" + token + "\n")
    env_path.chmod(0o600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://host.docker.internal:8020/api/notifications/alertmanager")
    args = parser.parse_args()
    try:
        configure(Path(__file__).resolve().parent / "secrets", args.url)
    except ValueError as exc:
        parser.error(str(exc))
    print("Webhook files prepared. Copy secrets/backend-webhook.env into the backend environment and recreate both services.")
