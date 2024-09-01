import requests
import json
import sys

from collections import defaultdict

'''
Coordinates API calls to CardKingdom, taking in a list of newline-delimited card names. 

Eg, export from moxfield as MTGO format, remove section names, and save to disk. 

Multiples will be ignored; you might want to remove Forests and such anyway. 

It's hacky, no guarantees it works etc. 
'''

def main(): 
    if len(sys.argv) < 3: 
        print(f"Format is: {sys.argv[0]} <path_to_card_list> <price_threshold>")
    price = float(sys.argv[2])
    with open(sys.argv[1]) as fh: 
        card_list = fh.read()
    print("Checking (this can take a minute...)")
    split_expensive_cards(card_list, price)

def get_card_info_from_ck(newlined_cardlist): 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/json;charset=utf-8',
        'Origin': 'https://www.cardkingdom.com',
        'Connection': 'keep-alive',
        'Referer': 'https://www.cardkingdom.com/builder',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    json_data = {
        'submit': 1,
        'cardData': newlined_cardlist,
        'autofill_lp': '1',
        # Change these to 0 if you don't want to search for GOOD or NEAR MINT or whatever. 
        'NM': '1',
        'EX': '1',
        'VG': '1',
        'G': '1',
    }

    cookies = requests.cookies.cookiejar_from_dict({})

    response = requests.post('https://www.cardkingdom.com/api/builder', cookies=cookies, headers=headers, json=json_data)
    return response
    
def parse_prices_from_ck_resp(response):
    results = json.loads(response.text)["results"]
    cards = defaultdict(list)
    for card in results: 
        for printing in card: 
            if printing["core_name"] not in cards: 
                print("Adding " + printing["core_name"])
                cards[printing["core_name"]] = []
            for sale_entry in printing['style_qty']: 
                if sale_entry["maxQtyAvailable"] > 0:
                    cards[printing["core_name"]].append(sale_entry["price"])
    return cards
    

def get_unknowns_from_ck_resp(response):
    return json.loads(response.text)['not_found']
    
def get_all_ck_data(newlined_cardlist): 
    resp = get_card_info_from_ck(newlined_cardlist)
    not_founds = get_unknowns_from_ck_resp(resp)
    prices = parse_prices_from_ck_resp(resp)
    mins = {}
    unavails = []
    for card, pricelist in prices.items(): 
        if pricelist: 
            mins[card] = min(pricelist)
        else: 
            unavails.append(card)
    return mins, not_founds, unavails
    

def split_expensive_cards(newlined_cardlist, price_threshold): 
    all_prices, unknown, unavail = get_all_ck_data(newlined_cardlist)
    if unknown: 
        print(f"Unknown Cards: {unknown}. ")
    cheaps = []
    for card, min_price in all_prices.items(): 
        if float(min_price) > price_threshold: 
            unavail.append(card)
        else: 
            cheaps.append(card)
    print("\n----------------------------------------------------------------------------")
    print(f"Copy below for {len(cheaps)} cheap Card Kingdom buys https://www.cardkingdom.com/builder : ")
    for card in cheaps: 
        print (card)
    print(f"\n\nCopy below for {len(unavail)} expensives/unavailables https://mpcfill.com/editor proxies: ")
    for card in unavail: 
        print (card)


if __name__ == "__main__": 
    main()