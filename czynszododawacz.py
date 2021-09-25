import requests
import webbrowser
from bs4 import BeautifulSoup
import time
import re
import os
from sys import argv

SITES = ['olx', 'otodom']  # The list of supported domains
config = {}

# TODO: Get readme for GitHub
# TODO: Add a requirements file (if not present)


def main():
    load_settings()

    # Change the link in the config file
    if len(argv) == 3 and argv[1] == "link":
        change_url(argv[2])
        return 0

    # Print help if there are no additional arguments
    elif not len(argv) == 2:
        print_help()
        exit()

    # If the only argument is a link to one of supported sites, load and open it
    if 'olx.pl' in argv[1]:
        refresh(argv[1])
        open_site()
        return 0

    # Open the latest rendered file
    if argv[1] == "open":
        open_site()
        return 0

    # Reload the file based on the link in config
    if argv[1] == "refresh":
        refresh(config["olx_url"])
        return 0

    # If the user input wasn't a valid one, print help
    print_help()


def open_site():
    """ Opens the latest rendered site if it exists, loads a new one if not """
    if not os.path.exists("olx.html"):
        refresh(config["olx_url"])
    webbrowser.open("olx.html")


def refresh(url):
    """ Renders a new page with offers based on a url """
    
    print(f"\nWczytywanie nowych ofert na olx")
    print(url)

    # Get all offers from the site
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    offers = get_offers(soup)
    offer_count = len(offers)

    for i in range(offer_count):
        # Get original price for each offer
        price_tag = get_price(offers[i])
        price = extract_price(price_tag)
        original_price = price
        # Skip if already too expensive
        if price <= config['cost_limit']:
            # Get the link for each offer
            offer_link = get_offer_link(offers[i])  # this  works for all supported sites so far
            print(f"{i + 1}/{offer_count}: " + offer_link)
            # Get the hidden price
            hidden_price = get_hidden_price(offer_link)
            price += hidden_price
        # Reject offers exceeding budget
        if price > config['cost_limit'] and not config['cost_limit'] == 0:
            print(f"Odrzucam ogłoszenie {i + 1}, {price} zł\n")
            offers[i].parent.extract()
            continue

        # Printouts
        print(f"{original_price} + {hidden_price} -> {price} zł")
        print()

        # Replace the price tag on the listing
        price_tag.string.replace_with(str(price) + " zł")

    # Save the edited site to a file
    f = open(f"olx.html", 'w', encoding='utf-8')
    f.write(str(soup))
    f.close()


def get_hidden_price(url):
    """Returns the hidden price from an offer url

    For some reason these are displayed in two different ways,
    this function tries both before concluding there is no hidden price
    """

    # The sites sometimes partner up and link to each other's offers, so check again what the domain is
    site = get_domain(url)

    # Don't make requests too quickly (results in a ban on the ip)
    time.sleep(config['sleep_time'])

    offer_r = requests.get(url)
    offer_soup = BeautifulSoup(offer_r.text, 'html.parser')
    hidden_price_tag = None

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
        hidden_price_parent = offer_soup.find("div", attrs={"aria-label": "Czynsz - dodatkowo"})
        if hidden_price_parent:
            hidden_price_tag = hidden_price_parent.find("div", class_="css-1ytkscc ev4i3ak0", title=re.compile("zł"))

    if hidden_price_tag:
        hidden_price = extract_price(hidden_price_tag)
        if hidden_price:
            return hidden_price

    return 0


def get_offers(soup):
    """ Returns a list of offer tags """
    offers = soup.find_all("div", class_="offer-wrapper")
    return offers


def get_offer_link(offer):
    """ Returns link to an offer included in a listing"""
    link = offer.find("a")['href']
    return link


def get_price(offer):
    """ Returns a regular price from an offer listing, which is named differently on each site """
    price_tag = offer.find("p", class_="price").strong
    return price_tag


def extract_price(tag):
    """ Returns an integer from a string representing a monetary value """
    e_price_str = tag.contents[0]
    e_price_str = e_price_str.split(',')[0]  # cut off any cents in the price
    e_price = int(re.sub("\D", '', e_price_str))
    return e_price


def get_domain(url):
    """ Returns the domain name (without top level) from a url """
    for domain in SITES:
        if domain + '.pl' in url:
            return domain


def load_settings():
    """ Reads the 'config.txt' file and saves the settings to a global array """
    global config

    # Load file
    try:
        config_file = open('config.txt', 'r').readlines()
        assert len(config_file) == 3  # There should be three lines in the file
    except (AssertionError, FileNotFoundError):
        recover_config()  # Load the default settings
        config_file = open('config.txt', 'r').readlines()

    # Save each setting
    for s in config_file:
        setting = s.split("=", maxsplit=1)
        val = setting[1].replace('\n', '')
        config[setting[0]] = int(val) if val.isnumeric() else val

    # Cost limit set to '0' means no limit (infinity)
    if config['cost_limit'] == 0:
        config['cost_limit'] = float('inf')


def change_url(url):
    """ Saves the url to the config file and reloads settings """
    site = get_domain(url)
    if not site:
        print("Niepoprawny link")
        return None
    lines = {"olx": 2}
    old_config = open("config.txt", 'r').readlines()
    new_config = open("config.txt", 'w')
    for l in range(len(old_config)):
        if l == lines[site]:
            new_config.write(f"{site}_url={url}\n")
        else:
            new_config.write(old_config[l])
    new_config.close()
    load_settings()


def recover_config():
    """ Recovers default settings file """
    config_file = open('config.txt', 'w')
    config_file.write(
        """sleep_time=1\ncost_limit=0\nolx_url=https://www.olx.pl/nieruchomosci/mieszkania/wynajem/""")
    print("Przywracanie domyślnych ustawień")


def print_help():
    print("""Czynszododawacz v1.2:
    (link)                  Wczytuje i otwiera podany link 
    open                    Otwiera ostatnią wczytaną stronę na olx lub otodom
    refresh                 Wczytuje nową stronę na podstawie linku w ustawieniach
    link (link)             Zmienia url do odświeżenia
    help                    Pokazuje tą wiadomość""")
    print("Ustawienia:")
    print(f"    Maksymalna cena ------------------ {'brak' if config['cost_limit'] == float('inf') else (str(config['cost_limit']) + ' zł')}")
    print(f"    Opóźnienie ----------------------- {config['sleep_time']} sekundy")
    print(f"    Link do olx ---------------------- {config['olx_url']}")


if __name__ == "__main__":
    main()
