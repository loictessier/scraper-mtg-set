from string import ascii_uppercase

from openpyxl import Workbook
from selenium import webdriver


def set_headers(sheet):
    headers = ["Edition","Ref", "","Titre US","Titre FR","Cout","Cout converti","Couleur","Force","Endurance","Type US","Type FR","Sous type US","Sous type FR","Capacités ","Artiste","Regles US","Regles FR","Rarete"]
    for i, c in enumerate(ascii_uppercase):
        if i == len(headers):
            break
        sheet[c + '1'] = headers[i]

def build_file(filename):
    workbook = Workbook()
    sheet = workbook.active
    set_headers(sheet)
    workbook.save(filename="./output/"+filename)

if __name__ == "__main__":
    filename = "test.xlsx"
    build_file(filename)
