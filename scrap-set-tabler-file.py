from string import ascii_uppercase

from openpyxl import Workbook
from selenium import webdriver
import requests


def set_headers(sheet):
    headers = ["Edition", "Ref", "", "Titre US", "Titre FR", "Cout", "Cout converti", 
               "Couleur", "Force", "Endurance", "Type US", "Type FR", "Sous type US", 
               "Sous type FR", "Capacités ", "Artiste", "Regles US", "Regles FR", "Rarete"]
    for i, c in enumerate(ascii_uppercase):
        if i == len(headers):
            break
        sheet[c + '1'] = headers[i]

def build_file(filename, eng_set_list, lang_fields_set_list):
    workbook = Workbook()
    sheet = workbook.active
    set_headers(sheet)
    for i in range(1, len(eng_set_list) + 1):
        card = eng_set_list[i-1]
        lang_card = next(x for x in lang_fields_set_list if x["collector_number"] == str(card['collector_number']))
        # set code
        sheet["A" + str(i + 1)] = card['set'].upper()
        # set code + collector number
        sheet["B" + str(i + 1)] = card['set'].upper() + str(card['collector_number'])
        # collector number (in set)
        sheet["C" + str(i + 1)] = str(card['collector_number'])
        # name
        sheet["D" + str(i + 1)] = card['name']
        # name lang
        sheet["E" + str(i + 1)] = lang_card["printed_name"]
        # mana cost
        sheet["F" + str(i + 1)] = card['mana_cost']
        # converted mana cost
        sheet["G" + str(i + 1)] = str(int(card['cmc']))
        # Color
        if len(card['colors']) > 0:
            sheet["H" + str(i + 1)] = card['colors'][0] if len(card['colors']) <= 1 else 'Z'
        elif "Artifact" in card['type_line'].split(' — ')[0]:
            sheet["H" + str(i + 1)] = "A"
        elif "Land" in card['type_line'].split(' — ')[0]:
            sheet["H" + str(i + 1)] = "L"
        else:
            sheet["H" + str(i + 1)] = "C"
        # power
        if 'power' in card:
            sheet["I" + str(i + 1)] = card['power']
        # toughness
        if 'toughness' in card:
            sheet["J" + str(i + 1)] = card['toughness']
        # Type eng
        sheet["K" + str(i + 1)] = card['type_line'].split(' — ')[0]
        # Type lang
        sheet["L" + str(i + 1)] = lang_card['printed_type_line'].split(' — ')[0]
        # subtype US
        if len(card['type_line'].split(' — ')) > 1:
            sheet["M" + str(i + 1)] = card['type_line'].split(' — ')[1]
        # subtype lang
        if len(lang_card['printed_type_line'].split(' — ')) > 1:
            sheet["N" + str(i + 1)] = lang_card['printed_type_line'].split(' — ')[1].capitalize()
        # keywords lang TODO
        sheet["O" + str(i + 1)] = ""
        # artist
        sheet["P" + str(i + 1)] = card['artist']
        # rules us
        sheet["Q" + str(i + 1)] = card['oracle_text']
        # rules lang
        sheet["R" + str(i + 1)] = lang_card["printed_text"]
        # rarity
        match card['rarity']:
            case 'common':
                sheet["S" + str(i + 1)] = "Commune"
            case 'uncommon':
                sheet["S" + str(i + 1)] = "Unco"
            case 'rare':
                sheet["S" + str(i + 1)] = "Rare"
            case 'mythic':
                sheet["S" + str(i + 1)] = "Mythique"
            case _:
                sheet["S" + str(i + 1)] = card['rarity']
    workbook.save(filename="./output/"+filename)


def fetch_eng_set(set_code):
    set_list = []
    url = "https://api.scryfall.com/cards/search"
    payload = {
        'order': 'name', 
        'q': f'(game:paper) set:{set_code} include:extras unique:prints'
    }
    r = requests.get(url, params=payload).json()
    next_page = r["next_page"] if "next_page" in r else None
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
    set_list.sort(key=lambda x: int(x['collector_number']))
    return set_list


def fetch_lang_fields(set_code, set_list):
    lang_fields_set_list = []
    for card in set_list:
        lang_card = {}
        url = f"https://api.scryfall.com/cards/{set_code}/{str(card['collector_number'])}/fr"
        r = requests.get(url).json()
        lang_card["collector_number"] = str(card["collector_number"])
        lang_card["printed_name"] = r["printed_name"] if "printed_name" in r else ""
        lang_card["printed_type_line"] = r["printed_type_line"] if "printed_type_line" in r else ""
        lang_card["printed_text"] = r["printed_text"] if "printed_text" in r else ""
        lang_fields_set_list.append(lang_card)      
    return lang_fields_set_list


def test_api(eng_set_list, lang_fields_set_list=None):
    for card in eng_set_list:
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
    print("-"*20)
    print(f"Number of cards : {len(set_list)}")

if __name__ == "__main__":
    set_code = "fdn"
    filename = f"test_{set_code}.xlsx"
    eng_set_list = fetch_eng_set(set_code)
    lang_fields_set_list = fetch_lang_fields(set_code, eng_set_list)
    build_file(filename, eng_set_list, lang_fields_set_list)
    # test_api(eng_set_list, lang_fields_set_list)
