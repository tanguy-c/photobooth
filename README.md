# Photobooth

A self-hosted photobooth web application built with Django. Displays a live camera feed in the browser, takes photos on tap/click, applies a customizable overlay, and lets guests download their picture via QR code.

Forked from [capitoledulibre/photobooth](https://github.com/capitoledulibre/photobooth) and reworked to be easily customizable for any event.

## Features

- **Browser-based** -- uses the device webcam via `getUserMedia`, no native app needed
- **Customizable overlay** -- swap `client/static/img/photobooth-mask.png` to brand photos for your event
- **QR code download** -- guests scan a QR code to get their photo (original + with overlay)
- **Email delivery** -- optionally email the photo to the guest
- **GPS EXIF tagging** -- embed venue coordinates in photo metadata
- **Pluggable upload backends** -- WebDAV (bundled Caddy server) or rsync
- **Fully configurable UI text** -- event name, countdown, action prompts, logo, all via environment variables
- **Docker Compose deployment** -- single command to run the full stack

## Architecture

```
docker-compose.yml          # Full-stack: client + server
client/                     # Django app (photobooth UI + API)
server/                     # Caddy file server (serves photos via WebDAV + HTTPS)
```

The **client** captures photos from the browser, saves them, applies the overlay mask, and uploads them to the **server** (Caddy) via WebDAV. Celery + RabbitMQ handle the upload asynchronously. PostgreSQL stores photo metadata.

## Quick Start (Docker Compose)

This is the recommended way to run the photobooth. The root `docker-compose.yml` starts the full stack: Django app, Celery worker, RabbitMQ, PostgreSQL, and a Caddy file server.

### 1. Customize your event

Place your overlay image at `client/static/img/photobooth-mask.png` (must match the camera resolution, default 3840x2160). Replace `client/static/img/logo.png` with your event logo.

### 2. Configure environment variables

Edit `docker-compose.yml` to set your event's configuration. Key variables:

| Variable | Description | Default |
|---|---|---|
| `PHOTOBOOTH_EVENT_NAME` | Event name displayed in the UI and emails | `Photobooth` |
| `PHOTOBOOTH_LOGO_URL` | Path to the logo shown on the result screen | `/static/img/logo.png` |
| `PHOTOBOOTH_BASE_URL` | Public URL where the Caddy server serves photos | `http://localhost:8080/` |
| `PHOTOBOOTH_ACTION_TEXT` | Text prompting the user to take a photo | `Appuyez sur le buzzer...` |
| `PHOTOBOOTH_SMILE_TEXT` | Text shown during countdown | `Pensez à sourire :)` |
| `PHOTOBOOTH_COUNTDOWN_SECONDS` | Seconds before the photo is taken | `5` |
| `PHOTOBOOTH_RESULT_TIMEOUT_SECONDS` | Seconds the result screen stays before resetting | `45` |
| `PHOTOBOOTH_DISMISS_TEXT` | Text shown below the countdown on the result screen | |
| `PHOTOBOOTH_THANKS_TEXT` | Thank-you text shown after the photo | |
| `PHOTOBOOTH_GPS_COORDINATES` | GPS coordinates for EXIF data (`lat,lon,alt`) | _(empty)_ |
| `PHOTOBOOTH_BACKEND` | Upload backend: `webdav` or `rsync` | `webdav` |
| `PHOTOBOOTH_FROM_EMAIL` | Sender address for emailed photos | `noreply@photobooth.local` |

### 3. Start

```sh
docker compose up -d --build
```

The photobooth UI is available at **http://localhost:8005**. Photos are served by Caddy at **http://localhost:8080**.

## Standalone Server

The `server/` directory contains a standalone Caddy file server that can be deployed separately (e.g., on a remote VPS) to serve photos over HTTPS with automatic Let's Encrypt certificates.

A pre-built image is published to GHCR on every push to `main` via the included GitHub Actions workflow.

### Configuration

Copy the example env file and fill in your values:

```sh
cp server/.env.example server/.env
```

| Variable | Description |
|---|---|
| `DOMAIN` | Public domain (e.g. `photo.example.org`). Caddy auto-provisions TLS via Let's Encrypt |
| `WEBDAV_USERNAME` | Username for WebDAV uploads |
| `WEBDAV_PASSWORD_HASH` | Bcrypt hash of the upload password |

Generate the password hash with:

```sh
docker run --rm caddy:latest caddy hash-password --plaintext 'your-password'
```

### Deploy with Docker Compose

```sh
cd server
docker compose up -d
```

### Example Compose

If you prefer to write your own compose file:

```yaml
services:
  caddy:
    image: ghcr.io/tanguy-c/photobooth/server:latest
    env_file: .env
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - photos:/srv/photos
      - caddy_data:/data
      - caddy_config:/config
    restart: unless-stopped
    read_only: true
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp

volumes:
  photos: {}
  caddy_data: {}
  caddy_config: {}
```

Where `.env` contains:

```sh
DOMAIN=photo.example.org
WEBDAV_USERNAME=photobooth
WEBDAV_PASSWORD_HASH=$2b$14$...
```

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A webcam

### Setup

```sh
cd client
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8005
```

Then open **http://localhost:8005**. In development mode, Celery tasks run synchronously (no RabbitMQ needed) and the database is SQLite.

### Code quality

```sh
# Install pre-commit hooks (one-time)
pipx install pre-commit
pre-commit install

# Update dependencies
uv lock --upgrade
uv export --no-dev --no-hashes > requirements.txt
```

## Hardware Setup

You need:
- A computer with a webcam (or an external USB camera)
- A web browser in full-screen/kiosk mode
- A touchscreen, mouse, or any input device that generates click events

For the best experience, use a large touchscreen monitor so guests can tap to take their photo and scan the QR code directly from the screen.

## License

See the original project: [capitoledulibre/photobooth](https://github.com/capitoledulibre/photobooth).
