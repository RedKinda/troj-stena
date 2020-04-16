import bs4
import aiohttp
import logging
import asyncio
import re
from datetime import datetime

# Will be imported from constants
MONTHS = {
    "január": "january",
    "február": "february",
    "marec": "march",
    "apríl": "april",
    "máj": "may",
    "jún": "june",
    "júl": "july",
    "august": "august",
    "september": "september",
    "október": "october",
    "december": "december"
}


# Helper function
def convert_month(mnt):
    for month in MONTHS.keys():
        if month in mnt:
            return mnt.replace(month, MONTHS[month])


async def request():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://kms.sk/ulohy/") as r:
                output = await get_tasks(r)
                return output
    except Exception:
        logging.exception(f"Connectivity error occured in ")


async def get_tasks(r):
    sourceCode = await r.text()
    try:
        soup = bs4.BeautifulSoup(sourceCode, 'html.parser')
    except Exception:
        logging.exception(f"Web parsing error occured in ")
    try:
        main_content = soup.find("div", {"class": "main-content"})
        task_lists = main_content.find_all("table", {"class": "task-list"})
        p_bars = main_content.find_all("div", {"class": "roundprogressbar"})
        headlines = main_content.find_all("h2")
    except Exception:
        logging.exception(f"Web is not compatible ")
    try:
        for h, b, t in zip(headlines, p_bars, task_lists):
            s_round, s_part, s_year = [int(x) for x in re.findall("([0-9]+?)\.", h.contents[1].next)]
            s_ending_time = datetime.strptime(convert_month(b.find("em").next[13:]), "%d. %B %Y %H:%M")
            s_id = int(t.attrs['id'][-3:])
            print(f"-=[ Round {s_round} | {s_part}. part of {s_year}. year ]=- ends at: {s_ending_time} ({s_id})")
            # Start scraping the task table
            for tr in t.find_all("tr")[1:]:
                td = tr.find_all("td")
                num = re.findall("[0-9]+", td[0].next)[0]
                name = td[1].a.next
                link = "self.url"+td[1].a.attrs['href']
                category = td[2].span.next if len(td) > 3 else "all"
                points = [re.findall("[0-9]+", x.next)[0] for x in td[-1].find_all("span")]
                print(f"    {num} {name} {link} {category} {points}")

    except Exception:
        logging.exception(f"Structure or formatting is not compatible ")


loop = asyncio.get_event_loop()
loop.run_until_complete(request())
