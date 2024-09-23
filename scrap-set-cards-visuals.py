import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By

browser = webdriver.Firefox()

URL_ID = "a43"
SET_ID = "DSKAS_"

# DSK 1 à 417 puis 901 à 918
# DSC 1 à 373 puis 901 à 923
# DSKAS 1 à 108
# a43
card_counter = 1
for i in range(1, 109):
    browser.get('https://www.magic-ville.com/fr/carte.php?ref=' + URL_ID + str(i).zfill(3))

    # get the image source
    img = browser.find_element(By.XPATH, "//div[@id='CardScan']//img")
    src = img.get_attribute('src')

    # download the image
    urllib.request.urlretrieve(src, "./output/" + SET_ID.upper() + str(card_counter).zfill(4) + ".jpg")
    card_counter += 1

browser.close()
