import os
import time
import urllib.request
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


def setup_browser():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    context = browser.new_context()
    page = context.new_page()
    return p, browser, page


def create_output_folder(set_prefix):
    folder = f"./output/{set_prefix.upper()}/visuals"
    os.makedirs(folder, exist_ok=True)
    return folder


def download_image(url, path):
    try:
        urllib.request.urlretrieve(url, path)
        print(f"Téléchargé : {path}")
    except Exception as e:
        print(f"Erreur téléchargement {url} : {e}")


def get_next_url(page):
    link = page.query_selector("//a[img[contains(@src,'right.png')]]")
    if link:
        return link.get_attribute("href")
    return None


def extract_card_id_from_url(url):
    if url and "ref=" in url:
        return url.split("ref=")[-1]
    return None


def download_card(page, card_ref, output_folder, prefix):
    url = f"https://www.magic-ville.com/fr/carte.php?ref={card_ref}"
    page.goto(url)

    try:
        card_number = page.query_selector("input[name='num']").get_attribute("value")
        card_number = str(card_number).zfill(4)
    except Exception:
        print(f"[WARN] Numéro introuvable pour {card_ref}, fallback au nom brut")
        card_number = 'XXXX'

    filename_prefix = f"{prefix}{card_number}"

    img = page.query_selector("#CardScan img")
    if img:
        src = img.get_attribute('src')
        download_image(src, os.path.join(output_folder, f"{filename_prefix}.jpg"))
    else:
        print(f"[WARN] Image recto non trouvée pour {card_ref}")

    img_back = page.query_selector("#CardScanBack img")
    if img_back:
        src_back = img_back.get_attribute('src')
        download_image(src_back, os.path.join(output_folder, f"{filename_prefix}bis.jpg"))

    return card_number


def fetch_all_cards(set_code, on_progress=None):
    set_code = set_code.lower()
    current_ref = f"{set_code}001"
    output_folder = create_output_folder(set_code)
    prefix = set_code.upper()

    p, browser, page = setup_browser()

    try:
        while current_ref:
            print(f"→ Téléchargement {current_ref}")
            download_card(page, current_ref, output_folder, prefix)
            if on_progress:
                on_progress(set_code, current_ref)

            next_url = get_next_url(page)
            next_card_id = extract_card_id_from_url(next_url)
            if not next_card_id or not next_card_id.startswith(set_code):
                break  # fin de l’édition
            current_ref = next_card_id
            time.sleep(0.5)
    finally:
        browser.close()
        p.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Télécharge les visuels d'une édition Magic depuis Magic-Ville.")
    parser.add_argument("set_code", help="Code de l'édition (ex: fic, j25, fdn)")
    args = parser.parse_args()

    fetch_all_cards(args.set_code)
