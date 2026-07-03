import os
import sys
import threading
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from .scraper import run_scrape, zip_output, progress
from .services.dropbox_client import upload_and_share, list_files

# Configuration du logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

def run_job(set_code):
    try:
        logging.info(f"[{set_code}] Scraping started")
        run_scrape(set_code)
        zip_path = zip_output(set_code)
        logging.info(f"[{set_code}] Zip generated at {zip_path}")

        try:
            url = upload_and_share(zip_path, folder="/MTG")
            progress[set_code]["url"] = url
            logging.info(f"[{set_code}] Uploaded to Dropbox: {url}")
        except Exception as e:
            logging.warning(f"[{set_code}] Dropbox upload failed: {e}", exc_info=True)
            progress[set_code]["zip"] = zip_path

        progress[set_code]["done_flag"] = True
        logging.info(f"[{set_code}] Job finished successfully")

    except Exception as e:
        logging.error(f"[{set_code}] Job failed: {e}", exc_info=True)
        progress[set_code]["done_flag"] = True
        progress[set_code]["error"] = str(e)


def list_files():
    try:

@app.route("/")
def index():
    logging.info("Serving index.html")
    return app.send_static_file("index.html")

@app.route("/oauth2/callback")
def oauth2_callback():
    code = request.args.get("code")
    logging.info(f"OAuth2 callback received code: {code}")
    return f"Authorization code: {code}"

@app.post("/api/scrape")
def api_scrape():
    data = request.get_json(silent=True) or {}
    set_code = (data.get("set_code") or "").strip().lower()
    if not set_code:
        logging.warning("Scrape request rejected: set_code missing")
        return jsonify({"error": "set_code manquant"}), 400

    logging.info(f"Scrape request accepted for set: {set_code}")
    progress[set_code] = {"done": 0, "done_flag": False}

    t = threading.Thread(target=run_job, args=(set_code,))
    t.daemon = True
    t.start()

    return jsonify({"status": "started", "set": set_code})

@app.get("/download/<set_code>")
def download(set_code):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    zip_path = os.path.join(base_dir, "output", f"{set_code.upper()}.zip")

    if not os.path.exists(zip_path):
        logging.error(f"[{set_code}] Zip not found at {zip_path}")
        return "Fichier non trouvé", 404

    logging.info(f"[{set_code}] Downloading zip from {zip_path}")
    return send_file(zip_path, as_attachment=True)

@app.get("/api/progress/<set_code>")
def api_progress(set_code):
    set_code = set_code.lower()
    if set_code not in progress:
        logging.warning(f"[{set_code}] Progress requested but not found")
        return jsonify({"error": "Pas de progression pour ce set"}), 404

    logging.debug(f"[{set_code}] Progress returned: {progress[set_code]}")
    return jsonify(progress[set_code])


@app.get("/api/ ")

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    logging.info(f"Starting Flask app in {'debug' if debug else 'production'} mode")
    app.run(host="0.0.0.0", port=5000)
