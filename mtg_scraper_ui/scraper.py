import shutil
import os
import logging
from mtg_scraper_lib.scrap_set_cards_visuals import fetch_all_cards

# dict global pour stocker la progression
progress = {}

def run_scrape(set_code: str):
    set_code = set_code.lower()
    progress[set_code] = {"done": 0}

    logging.info(f"[{set_code}] Starting card fetch...")

    def on_progress(code, ref):
        progress[code]["done"] += 1
        if progress[code]["done"] % 10 == 0:
            logging.info(f"[{code}] Progress: {progress[code]['done']} cards downloaded")

    try:
        fetch_all_cards(set_code, on_progress=on_progress)
        logging.info(f"[{set_code}] Fetch completed. Total cards: {progress[set_code]['done']}")
    except Exception as e:
        logging.error(f"[{set_code}] Error during fetch: {e}", exc_info=True)
        raise


def zip_output(set_code: str) -> str:
    folder = os.path.join("output", set_code.upper(), "visuals")
    zip_base_name = os.path.join("output", f"{set_code.upper()}")

    logging.info(f"[{set_code}] Creating zip from {folder}")
    try:
        zip_path = shutil.make_archive(zip_base_name, "zip", folder)
        logging.info(f"[{set_code}] Zip created at {zip_path}")
        return zip_path
    except Exception as e:
        logging.error(f"[{set_code}] Failed to create zip: {e}", exc_info=True)
        raise
