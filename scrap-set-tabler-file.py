from string import ascii_uppercase

from openpyxl import Workbook
from selenium import webdriver
import requests


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

def get_set(set_code):
    set_list = []
    url = "https://api.scryfall.com/cards/search"
    payload = {
        'order': 'name', 
        'q': f'(game:paper) set:{set_code} include:extras unique:prints'
    }
    r = requests.get(url, params=payload).json()
    next_page = r["next_page"]
    while r:
        for card in r["data"]:
            set_list.append(card)
        
        if next_page:
            r = requests.get(next_page).json()
            if "next_page" in r:
                next_page = r["next_page"]
            else:
                next_page = None
        else:
            r = None

    print(len(set_list))
    return set_list

if __name__ == "__main__":
    filename = "test.xlsx"
    # build_file(filename)
    set_list = get_set('blb')
    for card in set_list:
        # card fields : (upper)set (blb), ((upper)set+)collector_number (122), name (Agate Assault), (fr) printed_name , mana_cost ({2}{R}), cmc (3.0), colors (R), power (None), toughness (None), type_line(split[" — "][0]) (Sorcery), (fr) printed_type_line(split[" — "][0]) (),  type_line(split[" — "][1]) (Sorcery), (fr) printed_type_line(split[" — "][1]) (), (fr) printed_text, artist (Slawomir Maniak), oracle_text, (fr) printed_text, rarity(matching table "Commune", "Unco", "Rare", "Mythique")
        print("-----------------------")
        print(f"Edition : { card['set'].upper() }")
        print(f"Ref : { card['set'].upper() + str(card['collector_number']) }")
        print(f"<numéro_carte> : { str(card['collector_number']) }")
        print(f"Titre US : { card['name'] }")
        print(f"Cout : { card['mana_cost'] }")
        print(f"Cout converti : { str(int(card['cmc'])) }")
        if len(card['colors']) > 0:
            print(f"Couleur : { card['colors'][0] if len(card['colors']) <= 1 else 'Z' }")
        else:
            print(f"Couleur : A")
        if 'power' in card:
            print(f"Force : { card['power'] }")
        if 'toughness' in card:
            print(f"Endurance : { card['toughness'] }")
        print(f"Type US : { card['type_line'].split(' — ')[0] }")
        if len(card['type_line'].split(' — ')) > 1:
            print(f"Sous type US : { card['type_line'].split(' — ')[1] }")
        print(f"Artiste : { card['artist'] }")
        print(f"Regles US : { card['oracle_text'] }")
        print(f"Rarete : { card['rarity'] }")
