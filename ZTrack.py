import requests
from datetime import datetime
from argparse import ArgumentParser
from math import ceil
from enum import Enum
from bs4 import BeautifulSoup
import colorama
from colorama import Fore, Back, Style


dateformat_cs = "%d. %m. %Y %H:%M:%S"
dateformat_en = "%Y-%m-%d %H:%M:%S"

colors_enabled = True

class InvalidPackageError(Exception):
    pass


class Lang(Enum):
    en = 0
    cs = 1


class ExtraInfo:

    def __init__(self, sender, order, cod, pickup_name, pickup_address):
        self.sender = sender
        self.order = order
        self.cod = cod
        self.pickup_name = pickup_name
        self.pickup_address = pickup_address


class TrackingMessage:

    def __init__(self, date, message, lang = Lang.en):
        self.date = date
        self.text = message
        self.lang = lang

    def __str__(self):
        return datetime.strftime(self.date, dateformat_cs if lang == Lang.cs else dateformat_en) + " " + self.text


class PacketaPackage:

    def __init__(self, number, lang=Lang.en):
        self.number = number
        self.lang = lang
        self.status = ""
        self.tracking = []
        self.info = None
        self.url = "https://tracking.packeta.com/" + self.lang.name + "/?id=" + str(self.number)

    def __scrape_tracking_tab(self, table_raw):

        for row in table_raw.find_all("tr"):
            date = datetime.strptime(row.th.text.strip(), dateformat_en if self.lang == Lang.en else dateformat_cs)
            self.tracking.append(TrackingMessage(date, row.td.text.strip(), self.lang))

    def __scrape_info_tab(self, table):
        pass

    def update(self):
        try:
            page = requests.get(self.url)
        except Exception as err:
            raise ConnectionError("Tracking page unavailable: " + str(err))

        soup = BeautifulSoup(page.text, "html.parser")

        if soup.find("div", {"class": "alert-danger"}) is not None:  # Check for the invalid package number alert
            raise InvalidPackageError("Invalid Tracking Number")

        self.status = str(soup.find("h3")).split("\n")[1].strip()   # Find the status text, extract it and strip spaces

        tables = soup.find_all("table")

        self.__scrape_info_tab(tables[0])
        self.__scrape_tracking_tab(tables[1])

class TestingPackage(PacketaPackage):

    def __init__(self, lang):
        super().__init__(000, lang)
        if lang == Lang.cs:
            self.status = 'Doruceno'
            self.info = None
            self.tracking.append(TrackingMessage(datetime.now(), "Testovací zpráva číslo 1000", lang=Lang.cs))
            self.tracking.append(TrackingMessage(datetime.now(), "Testovací zpráva číslo 2000", lang=Lang.cs))
            self.tracking.append(TrackingMessage(datetime.now(), "Testovací zpráva číslo 3000", lang=Lang.cs))
            self.tracking.append(TrackingMessage(datetime.now(), "Testovací zpráva číslo 4000", lang=Lang.cs))
            self.tracking.append(TrackingMessage(datetime.now(), "Testovací zpráva číslo 5000", lang=Lang.cs))
        else:
            self.status = 'Delivered'
            self.info = None
            self.tracking.append(TrackingMessage(datetime.now(), "Testing message #10", lang=Lang.en))
            self.tracking.append(TrackingMessage(datetime.now(), "Testing message #20", lang=Lang.en))
            self.tracking.append(TrackingMessage(datetime.now(), "Testing message #30", lang=Lang.en))
            self.tracking.append(TrackingMessage(datetime.now(), "Testing message #40", lang=Lang.en))
            self.tracking.append(TrackingMessage(datetime.now(), "Testing message #50", lang=Lang.en))
    
    def update(self):
        pass
        

def print_error(err):
    if colors_enabled:
        print(Fore.RED + "ERROR: " + Fore.RESET + err)
    else:
        print("ERROR: " + err)

def table_get_offset(message):
    pass

def print_tracking_tab(package):

    # TODO: Make this at least a little readable

    bigmsg = max([m.text for m in package.tracking], key=len)
    maxlen = len(bigmsg) + 5 if len(bigmsg) % 2 == 1 else len(bigmsg) + 4
    if(package.lang == Lang.en):
        maxlen += 1
    msg_center_offset = ceil(maxlen/2)-4 if package.lang == Lang.en else ceil(maxlen/2)-3


    # TODO: Add colors for different statuses

    table_top = "\u2554" + (maxlen+28)*"\u2550" + "\u2557"
    table_bottom = "\u255a" + 14*"\u2550" + "\u2567" + 12*"\u2550" + "\u2569" + maxlen*"\u2550" + "\u255d"
    table_separator = "\u255f"+ 14*"\u2550" + "\u256a" + 12*"\u2550" + "\u256c" + maxlen*"\u2550" + "\u2562"
    table_sep_2 = "\u2560" + 14*"\u2550" + "\u2564" + 12*"\u2550" + "\u2566" + maxlen*"\u2550" + "\u2563"
    table_titles_en = "\u2551     " + "DATE" + "     \u2502    " + "TIME" + "    \u2551" + msg_center_offset*" " + "MESSAGE" + msg_center_offset*" " + "\u2551"
    table_titles_cs = "\u2551     " + "DATUM" + "    \u2502     " + "ČAS" + "    \u2551" + msg_center_offset*" " + "ZPRÁVA" + msg_center_offset*" " + "\u2551"
    text_status = ("STATUS: " if package.lang == Lang.en else "STAV: ") + package.status

    print(table_top)
    print("\u2551  {status}{spaces}\u2551".format(status=text_status, spaces=(maxlen+26-len(text_status))*" "))
    print(table_sep_2)
    print(table_titles_cs if package.lang == Lang.cs else table_titles_en)
    print(table_separator)

    for index, msg in enumerate(package.tracking):

        date = msg.date.strftime("%d.%m.%Y") if package.lang == Lang.cs else msg.date.strftime("%Y-%m-%d")
        time = msg.date.strftime("%H:%M:%S")

        row_format = "\u2551  {date}  \u2502  {time}  \u2551  {message}{spaces}\u2551"\
            .format(date=date, time=time, message=msg.text, spaces=(maxlen - len(msg.text) - 2) * " ")

        print(row_format)

        if index != len(package.tracking)-1 and msg.date.day != package.tracking[index+1].date.day:     # Group messages from the same day together
            print(table_separator)

    print(table_bottom)


if __name__ == "__main__":

    # Init colorama on Windows
    colorama.init()

    argparser = ArgumentParser()
    argparser.add_argument("number", type=str, help="The package ID to be tracked")
    argparser.add_argument("-l", "--language", type=str, choices=["en", "cs"], help="The tracking info language", metavar="cs|en")
    argparser.add_argument("-n", "--no-colors", action='store_false', help="Disable colored output")
    argparser.add_argument('-x', '--test', action='store_true', help="Enable testmode")
    args = argparser.parse_args()

    package_id = str(args.number).strip().replace(' ', '')
    if package_id[0] == 'Z':
        package_id = package_id[1:]

    if args.language is not None:
        lang = Lang[args.language]
    else:
        lang = Lang.en
 
    colors_enabled = args.no_colors

    if args.test:
        print_tracking_tab(TestingPackage(lang))
        exit(0)

    pack = PacketaPackage(package_id, lang)
    try:
        pack.update()
    except InvalidPackageError:
        print_error("Invalid package ID")
        exit(-1)
    except ConnectionError:
        print_error("Could not connect to tracking service. Check your internet connection.")
        exit(-1)

    print_tracking_tab(pack)