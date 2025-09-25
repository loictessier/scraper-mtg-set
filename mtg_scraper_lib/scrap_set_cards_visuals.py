import os
import time
import urllib.request
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def setup_browser():
    options = webdriver.FirefoxOptions()
    options.headless = True #disable to display browser
    return webdriver.Firefox(options=options)


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


def get_next_url(browser):
    try:
        next_link = browser.find_element(By.XPATH, "//a[img[contains(@src,'right.png')]]")
        return next_link.get_attribute("href")
    except NoSuchElementException:
        return None


def extract_card_id_from_url(url):
    if url and "ref=" in url:
        return url.split("ref=")[-1]
    return None


def download_card(browser, card_ref, output_folder, prefix):
    url = f"https://www.magic-ville.com/fr/carte.php?ref={card_ref}"
    browser.get(url)

    try:
        card_number = browser.find_element(By.XPATH, "//input[@name='num']").get_attribute("value")
        card_number = str(card_number).zfill(4)
    except NoSuchElementException:
        print(f"[WARN] Numéro introuvable pour {card_ref}, fallback au nom brut")
        card_number = 'XXXX'

    filename_prefix = f"{prefix}{card_number}"

    try:
        img = browser.find_element(By.XPATH, "//div[@id='CardScan']//img")
        src = img.get_attribute('src')
        download_image(src, os.path.join(output_folder, f"{filename_prefix}.jpg"))
    except NoSuchElementException:
        print(f"[WARN] Image recto non trouvée pour {card_ref}")

    try:
        img_back = browser.find_element(By.XPATH, "//div[@id='CardScanBack']//img")
        src_back = img_back.get_attribute('src')
        download_image(src_back, os.path.join(output_folder, f"{filename_prefix}bis.jpg"))
    except NoSuchElementException:
        pass

    return card_number


def fetch_all_cards(set_code, on_progress=None):
    set_code = set_code.lower()
    current_ref = f"{set_code}001"
    output_folder = create_output_folder(set_code)
    prefix = set_code.upper()

    browser = setup_browser()

    try:
        while current_ref:
            print(f"→ Téléchargement {current_ref}")
            download_card(browser, current_ref, output_folder, prefix)
            if on_progress:
                on_progress(set_code, current_ref)

            next_url = get_next_url(browser)
            next_card_id = extract_card_id_from_url(next_url)
            if not next_card_id or not next_card_id.startswith(set_code):
                break  # fin de l’édition
            current_ref = next_card_id
            time.sleep(0.5)
    finally:
        browser.quit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Télécharge les visuels d'une édition Magic depuis Magic-Ville.")
    parser.add_argument("set_code", help="Code de l'édition (ex: fic, j25, fdn)")
    args = parser.parse_args()

    fetch_all_cards(args.set_code)

