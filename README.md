# scrapper-mtg-set

Scraper Magic: The Gathering images and data, with a simple Flask web UI.  

## 📦 Installation

Requires **Python 3** and [pipenv](https://pipenv.pypa.io/).  

```bash
pipenv install
```

## 🚀 Run the web UI

Start the Flask app from the project root:

```bash
pipenv run python -m mtg_scraper_ui.app
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.  
You can enter a set code (e.g. `SPM`, `FIC`, …) and launch a scrape from the web interface.  

The UI shows live progress and lets you download a ZIP of the images.  
If a Dropbox token is configured, the ZIP is uploaded automatically and a shareable link is provided.  

## ⚙️ Configuration

Optional: create a `.env` file to enable Dropbox uploads.  

```
DROPBOX_TOKEN=your_token_here
```

Without a token, downloads remain local (`output/<SET>.zip`).  

## 🛠️ Legacy usage (scripts only)

You can still run the raw scripts directly if needed:  

```bash
pipenv run python3 mtg_scraper_lib/scrap_set_cards_visuals.py SPM
```

Output is saved under `output/<SET>/visuals`.  
