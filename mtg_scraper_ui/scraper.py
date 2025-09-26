import shutil
import os
import time
from mtg_scraper_lib.scrap_set_cards_visuals import fetch_all_cards


# dict global pour stocker la progression
progress = {}

def run_scrape(set_code: str):
    try:
        def update_progress(n):
            progress[set_code] = n

        fake_scrape(set_code, callback=update_progress)
    except Exception as e:
        print("[ERROR] Fake scrape failed:", e, flush=True)


def zip_output(set_code: str) -> str:
    folder = os.path.join("output", set_code.upper(), "visuals")
    zip_base_name = os.path.join("output", f"{set_code.upper()}")
    zip_path = shutil.make_archive(zip_base_name, "zip", folder)
    return zip_path


def fake_scrape(set_code: str, callback=None):
    print(f"[DEBUG] Fake scrape started for {set_code}", flush=True)
    for i in range(1, 11):  # 10 étapes
        time.sleep(2)
        if callback:
            callback(i)
        print(f"[DEBUG] Progress {i}/10", flush=True)
    print("[DEBUG] Fake scrape finished", flush=True)
