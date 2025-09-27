import os
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from .scraper import run_scrape, zip_output, progress
from .services.dropbox_client import upload_and_share


load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

def run_job(set_code):
    # exécution du scraping dans un thread séparé
    run_scrape(set_code)
    zip_path = zip_output(set_code)

    try:
        url = upload_and_share(zip_path, folder="/MTG")
        progress[set_code]["url"] = url
    except Exception as e:
        print(f"[WARN] Dropbox upload failed: {e}")
        progress[set_code]["zip"] = zip_path

    progress[set_code]["done_flag"] = True

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/oauth2/callback")
def oauth2_callback():
    code = request.args.get("code")
    return f"Authorization code: {code}"

@app.post("/api/scrape")
def api_scrape():
    data = request.get_json(silent=True) or {}
    set_code = (data.get("set_code") or "").strip().lower()
    if not set_code:
        return jsonify({"error": "set_code manquant"}), 400

    # init état
    progress[set_code] = {"done": 0, "done_flag": False}

    # démarrer le thread
    t = threading.Thread(target=run_job, args=(set_code,))
    t.daemon = True
    t.start()

    return jsonify({"status": "started", "set": set_code})

# endpoint pour télécharger le zip
@app.get("/download/<set_code>")
def download(set_code):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    zip_path = os.path.join(base_dir, "output", f"{set_code.upper()}.zip")

    if not os.path.exists(zip_path):
        return "Fichier non trouvé", 404
    return send_file(zip_path, as_attachment=True)

@app.get("/api/progress/<set_code>")
def api_progress(set_code):
    set_code = set_code.lower()
    if set_code not in progress:
        return jsonify({"error": "Pas de progression pour ce set"}), 404
    return jsonify(progress[set_code])

if __name__ == "__main__":
    import os
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000)
    