# scrapper-mtg-set

Scraper for Magic: The Gathering card images and data, with a simple Flask web UI.

The application can run locally with Python/Pipenv or inside Docker.
It also supports optional Dropbox upload for generated ZIP archives.

## 📦 Requirements

For local development:

- Python 3
- pipenv

For Docker usage:

- Docker
- Docker Compose

## ⚙️ Configuration

Environment variables are not committed to Git.

Copy the example file depending on your target environment:

```bash
cp .env.example .env.dev

or for production:

cp .env.example .env.prod

Then fill the values if needed:

DROPBOX_REFRESH_TOKEN=
DROPBOX_APP_KEY=
DROPBOX_APP_SECRET=
FLASK_DEBUG=

Dropbox configuration is optional.

Without Dropbox credentials, generated ZIP files remain local under:

output/<SET>.zip
🚀 Run locally with Pipenv

Install dependencies:

pipenv install

Start the Flask app from the project root:

pipenv run python -m mtg_scraper_ui.app

Then open:

http://127.0.0.1:5000

You can enter a set code, for example SPM or FIC, and launch a scrape from the web interface.

The UI shows live progress and lets you download a ZIP of the images.
If Dropbox credentials are configured, the ZIP is uploaded automatically and a shareable link is provided.

🐳 Run with Docker in development

Create your development environment file:

cp .env.example .env.dev

Then start the development container:

docker compose -f docker-compose.dev.yml up --build

The application will be available at:

http://127.0.0.1:5000

The output/ directory is mounted as a volume so generated files remain available on the host.

🚀 Run with Docker in production

Create your production environment file:

cp .env.example .env.prod

Then start the production container:

docker compose up -d --build

View logs:

docker compose logs -f

Stop the application:

docker compose down

The production Compose file runs the app with Gunicorn.

By default, the app should be exposed only locally and served publicly through a reverse proxy such as Nginx.

Example production URL mapping:

Nginx / HTTPS -> 127.0.0.1:5050 -> container:5000
🔁 Redeploy in production

From the server:

git pull
docker compose up -d --build
docker compose logs -f
📁 Output

Scraped images and generated archives are saved under:

output/

This directory is mounted as a Docker volume in both development and production.

🛠️ Legacy usage: scripts only

You can still run the raw scraper scripts directly if needed:

pipenv run python3 mtg_scraper_lib/scrap_set_cards_visuals.py SPM

Output is saved under:

output/<SET>/visuals
