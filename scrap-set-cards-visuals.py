import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

browser = webdriver.Firefox()

URL_ID = "fic"
SET_ID = URL_ID.upper()

# DSK 1 à 417 puis 901 à 918
# DSC 1 à 373 puis 901 à 923
# DSKAS 1 à 108
# a43
# FDN 1 à 730 puis 901 à 933 puis 951 à 960
# J25 1 à 349 puis 351 à 780 puis 901 à 946
# INR 1 à 492 puis 601 à 628
# DFT 1 à 553 puis 701 à 714
# DRC 1 à 184 puis 301 à 317
# TDM 1 à 426 puis 801 à 816
# TDC 1 à 413 puis 801 à 834
# FIC 1 à 441 puis 484 à 486 puis 801 à 811 (497 cartes)
# FIN 1 à 563 puis 572 à 585 puis 801 à 836 puis 1001 à 1005
card_counter = 484
for i in range(484, 487):
    browser.get('https://www.magic-ville.com/fr/carte.php?ref=' + URL_ID + str(i).zfill(3))

    # get the image source
    img = browser.find_element(By.XPATH, "//div[@id='CardScan']//img")
    src = img.get_attribute('src')
    # download the image
    urllib.request.urlretrieve(src, f"./output/{SET_ID}/visuals/{SET_ID.upper()}{str(card_counter).zfill(4)}.jpg")

    # get the back image if exists
    try:
        img_back = browser.find_element(By.XPATH, "//div[@id='CardScanBack']//img")
        if img_back:
            src_back = img_back.get_attribute('src')
            # download the back image
            urllib.request.urlretrieve(src_back, f"./output/{SET_ID}/visuals/{SET_ID.upper()}{str(card_counter).zfill(4)}bis.jpg")
    except NoSuchElementException:
        pass
        
    card_counter += 1

browser.close()
