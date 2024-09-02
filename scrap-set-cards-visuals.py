import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By

browser = webdriver.Firefox()

for i in range(1, 1742):
    browser.get('https://www.magic-ville.com/fr/carte.php?ref=ms2' + str(i).zfill(3))

    # get the image source
    img = browser.find_element(By.XPATH, "//div[@id='CardScan']//img")
    src = img.get_attribute('src')

    # download the image
    urllib.request.urlretrieve(src, "./output/MB2" + str(i).zfill(4) + ".jpg")

browser.close()
