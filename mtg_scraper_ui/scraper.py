import shutil
import os
from mtg_scraper_lib.scrap_set_cards_visuals import fetch_all_cards

# dict global pour stocker la progression
progress = {}

def run_scrape(set_code: str):
    set_code = set_code.lower()
    progress[set_code] = {"done": 0}

    def on_progress(code, ref):
        progress[code]["done"] += 1

    fetch_all_cards(set_code, on_progress=on_progress)

def zip_output(set_code: str) -> str:
    folder = os.path.join("output", set_code.upper(), "visuals")
    zip_base_name = os.path.join("output", f"{set_code.upper()}")
    zip_path = shutil.make_archive(zip_base_name, "zip", folder)
    return zip_path
