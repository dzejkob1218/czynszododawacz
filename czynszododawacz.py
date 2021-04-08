import requests
import webbrowser
from bs4 import BeautifulSoup
import time
import re
import os


SUPPORTED = ['olx', 'otodom']
ACTIONS = ['open', 'refresh', 'link', 'help']
conf = {}


def main():
    # load_settings
    load_settings()
    # printout
    print_help()

    # control
    while True:
        cmd = None
        while not cmd:
            cmd = take_command()

        if cmd[0] == "open":
            open_cmd(cmd[1])
        if cmd[0] == "refresh":
            refresh_cmd(cmd[1])
        if cmd[0] == "link":
            change_url()
        if cmd[0] == "help":
            print_help()


def load_settings():
    global conf
    try:
        config = open('config.txt', 'r').readlines()
        assert len(config) == 4
    except (AssertionError, FileNotFoundError):
        recover_config()
        config = open('config.txt', 'r').readlines()
    for s in config:
        setting = s.split("=", maxsplit=1)
        val = setting[1].replace('\n', '')
        conf[setting[0]] = int(val) if val.isnumeric() else val
    if conf['cost_limit'] == 0:
        conf['cost_limit'] = float('inf')


def open_cmd(site):
    if os.path.exists(f"{site}.html"):
        webbrowser.open(f"{site}.html")
    else:
        refresh_cmd(site)


def refresh_cmd(site):
    refresh(conf[f"{site}_url"], site)
    open_cmd(site)


def change_url():
    url = input("Nowy link:\n")
    try:
        site = get_domain(url)
    except:
        print("Niepoprawny link")
        return None
    lines = {"olx": 2, "otodom": 3}
    old_config = open("config.txt", 'r').readlines()
    new_config = open("config.txt", 'w')
    for l in range(len(old_config)):
        if l == lines[site]:
            new_config.write(f"{site}_url={url}\n")
        else:
            new_config.write(old_config[l])
    new_config.close()
    load_settings()
    refresh_cmd(site)


def take_command():
    """ Processes user input until a valid command is entered """
    cmd = input().split(" ")
    if cmd[0] not in ACTIONS:
        print("Nieznane polecenie")
        return None
    if len(cmd) < 2 and not cmd[0] in ["link", "help"]:
        cmd.append(input("olx czy otodom?\n"))
    if len(cmd) > 2 and cmd[1] not in SUPPORTED:
        print("Nieznane polecenie")
        return None
    return cmd


def print_help():
    print("""Czynszododawacz v1.1
    open ---- otwiera ostatnią wczytaną stronę
    refresh - odświeża oferty
    link ---- zmienia url do odświeżenia
    help ---- pokazuje tą wiadomość""")
    print("Ustawienia:")
    print(f"    Maksymalna cena - {conf['cost_limit']} zł")
    print(f"    Opóźnienie ------ {conf['sleep_time']} sekundy")
    print(f"    Link do olx ----- {conf['olx_url']}")
    print(f"    Link do otodom -- {conf['otodom_url']}")


def refresh(url, site):
    """Renders a new page with offers based on last link"""
    print(f"\nWCZYTYWANIE NOWYCH OFERT NA {site.upper()}")
    print(url)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    offers = get_offers(soup, site)
    offer_count = len(offers)

    for i in range(offer_count):
        # Get original price for each offer
        price_tag = get_price(offers[i], site)
        price = extract_price(price_tag)
        # Get the link for each offer
        offer_link = offers[i].find("a")['href']  # this  works for all supported sites so far
        print(f"{i + 1}/{offer_count}: " + offer_link)
        # Get the hidden price (no point if already too expensive)
        if price <= conf['cost_limit']:
            hidden_price = get_hidden_price(offer_link)
            real_price = hidden_price + price
        else:
            real_price = price

        # Reject offers exceeding budget
        if real_price > conf['cost_limit']:
            print(f"Odrzucam ogłoszenie {i+1}, {real_price} zł\n")
            offers[i].parent.extract()
            continue

        # printouts
        print(f"{price} + {hidden_price} -> {real_price} zł")
        print()

        price_tag.string.replace_with(str(real_price) + " zł") ###

    f = open(f"{site}.html", 'w', encoding='utf-8')
    f.write(str(soup))
    f.close()


def get_offers(soup, site):
    """ Returns a list of offer tags, which are named differently on each site"""
    if site == 'olx':
        offers = soup.find_all("div", class_="offer-wrapper")
    elif site == 'otodom':
        offers = soup.find_all("div", class_="offer-item-details")
    return offers


def get_price(offer, site):
    """ Returns a regular price from an offer listing, which is named differently on each site"""
    if site == 'olx':
        price_tag = offer.find("p", class_="price").strong
    elif site == 'otodom':
        price_tag = offer.find("li", class_="offer-item-price")
    return price_tag


def extract_price(tag):
    """ Returns an integer from a string representing a monetary value """
    e_price_str = tag.contents[0]
    e_price_str = e_price_str.split(',')[0] # cut off any cents in the price
    e_price = int(re.sub("\D", '', e_price_str))
    return e_price


def get_hidden_price(url):
    """Returns the hidden price from an offer url

    For some reason these are displayed in two different ways,
    this function tries both before concluding there is no hidden price
    """

    # the sites sometimes partner and post each other's offers
    site = get_domain(url)

    # Don't make requests too quickly
    time.sleep(conf['sleep_time'])

    offer_r = requests.get(url)
    offer_soup = BeautifulSoup(offer_r.text, 'html.parser')

    if site == "olx":
        # Look for "offer-details" tags first
        hidden_price_tag = offer_soup.find("span", class_="offer-details__name", text=re.compile("Czynsz"))
        if hidden_price_tag:
            hidden_price_tag = hidden_price_tag.parent.strong
        # Look for string-based hidden price
        else:
            hidden_price_tag = offer_soup.find("p", class_="css-xl6fe0-Text eu5v0x0",
                                               text=re.compile("Czynsz \(dodatkowo\):"))

    if site == "otodom":
        hidden_price_tag = offer_soup.find("div", class_="css-1ytkscc ecjfvbm0", title=re.compile("zł"))

    if hidden_price_tag:
        hidden_price = extract_price(hidden_price_tag)
        if hidden_price:
            return hidden_price

    return 0


def get_domain(url):
    return url.split(sep='.', maxsplit=2)[1]


def recover_config():
    print("RECOVERED DEFAULT SETTINGS")
    config = open('config.txt', 'w')
    config.write("""sleep_time=2\ncost_limit=0\nolx_url=https://www.olx.pl/nieruchomosci/mieszkania/wynajem/\notodom_url=https://www.otodom.pl/wynajem/mieszkanie""")


if __name__ == "__main__":
    main()