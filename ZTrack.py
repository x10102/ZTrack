import requests
from datetime import datetime
from argparse import ArgumentParser
from math import ceil
from enum import Enum
from bs4 import BeautifulSoup


class Lang(Enum):
    en = 0
    cs = 1


_lang = Lang.en


def get_dates(tab_rows):
    dates = []

    for row in tab_rows:
        date_text = row.th.text.strip()
        date = datetime.now()
        if _lang == Lang.cs:
            date = datetime.strptime(date_text, "%d. %m. %Y %H:%M:%S")
        else:
            date = datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
        dates.append(date)

    return dates


def max_msg_length(track_info):
    messages = []
    for row in track_info.find_all("tr"):
        messages.append(row.td.text.strip())

    return len(max(messages, key=len))


def print_tracking_tab(track_info, status):
    msglen = max_msg_length(track_info)+5
    msg_center_offset = ceil(msglen/2)-4 if _lang == Lang.en else ceil(msglen/2)-3

    table_top = "\u2554" + (msglen+28)*"\u2550" + "\u2557"
    table_bottom = "\u255a" + 14*"\u2550" + "\u2567" + 12*"\u2550" + "\u2569" + msglen*"\u2550" + "\u255d"
    table_separator = "\u255f"+ 14*"\u2550" + "\u256a" + 12*"\u2550" + "\u256c" + msglen*"\u2550" + "\u2562"
    table_sep_2 = "\u2560" + 14*"\u2550" + "\u2564" + 12*"\u2550" + "\u2566" + msglen*"\u2550" + "\u2563"
    table_titles_en = "\u2551     " + "DATE" + "     \u2502    " + "TIME" + "    \u2551" + msg_center_offset*" " + "MESSAGE" + msg_center_offset*" " + "\u2551"
    table_titles_cs = "\u2551     " + "DATUM" + "    \u2502     " + "ČAS" + "    \u2551" + msg_center_offset*" " + "ZPRÁVA" + msg_center_offset*" " + "\u2551"
    text_status = ("STATUS: " if _lang == Lang.en else "STAV: ") + status

    print(table_top)
    print("\u2551  {status}{spaces}\u2551".format(status=text_status, spaces=(msglen+26-len(text_status))*" "))
    print(table_sep_2)
    print(table_titles_cs if _lang == Lang.cs else table_titles_en)
    print(table_separator)

    rows = track_info.find_all("tr")
    dates = get_dates(rows)

    for index, row in enumerate(rows):

        date = dates[index].strftime("%d.%m.%Y") if _lang == Lang.cs else dates[index].strftime("%Y-%m-%d")
        time = dates[index].strftime("%H:%M:%S")

        row_format = "\u2551  {date}  \u2502  {time}  \u2551  {message}{spaces}\u2551".format(date=date, time=time, message=row.td.text.strip(), spaces=(msglen - len(row.td.text)-2)*" ")

        print(row_format)

        if index != len(dates)-1 and dates[index].day != dates[index+1].day:
            print(table_separator)

    print(table_bottom)


argparser = ArgumentParser()
argparser.add_argument("number", type=int, help="The number of the package to be tracked")
argparser.add_argument("-l", "--language", type=str, choices=["en", "cs"], help="The tracking info language", metavar="cs|en")
args = argparser.parse_args()

package_id = args.number
if args.language is not None:
    _lang = Lang[args.language]

url = "https://tracking.packeta.com/" + _lang.name + "/?id=" + str(package_id)

try:
    page = requests.get(url)
except Exception as err:
    print("Error while requesting tracking page. Check your internet connection.")
    exit(1)

soup = BeautifulSoup(page.text, "html.parser")

if soup.find("div", {"class": "alert-danger"}) is not None:     # Check for the invalid package number alert
    print("Error: Invalid Tracking Number!")
    exit(1)

tables = soup.find_all("table", class_="table")
shop_info = tables[0]
tracking_info = tables[1]

package_status = soup.find("h3").text.split("\n")[1].strip()

print_tracking_tab(tracking_info, package_status)
