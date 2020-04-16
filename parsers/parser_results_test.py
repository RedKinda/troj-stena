import bs4
import aiohttp
import logging
import asyncio
import re

ids = [376]


async def request(id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://prask.ksp.sk/vysledky/{id}") as r:
                output = await get_tasks(r, id)
                return output
    except Exception:
        logging.exception(f"Connectivity error occured in ")


async def get_tasks(r, id):
    sourceCode = await r.text()
    try:
        soup = bs4.BeautifulSoup(sourceCode, 'html.parser')
    except Exception:
        logging.exception(f"Web parsing error occured in ")
    try:
        results_table = soup.find_all("table", {"class": "results-table"})
        nav_tabs = soup.find("ul", {"class": "nav-tabs"}).find_all("li")
    except Exception:
        logging.exception(f"Web is not compatible ")
    try:
        for table, nav in zip(results_table, nav_tabs):
            num_holder = 0
            print(f"-=[ Table {nav.a.next.strip()} ]=- ({id})")
            for tr in table.find_all("tr")[1:]:
                td = tr.find_all("td")
                if len(td) == 1:
                    print(f"    {td[0].next}")
                    break
                class_to_state = {
                    'glyphicon-asterisk': 'new',
                    'glyphicon-chevron-down': 'dropped',
                    'glyphicon-chevron-up': 'advanced',
                    'glyphicon-pushpin': 'pinned'
                }
                num = num_holder if td[0].strong is None else re.findall("[0-9]+", td[0].strong.next)[0]
                state = "NaN" if td[0].span is None else class_to_state[td[0].span.attrs["class"][2]]
                name = td[1].next
                year = td[2].next
                school = td[3].next.strip() if td[3].abbr is None else td[3].abbr.next.strip()
                # Pattern end #
                o = 5
                try:
                    level = td[4].span.next.strip()
                    if "?" in level:
                        raise Exception
                except Exception:
                    level = -1
                    o = 4
                points_bf = 0 if state == "NaN" else td[o].span.next.strip()
                points = {}
                for i in range(len(td)-(o+1 if state == "NaN" else o+2)):
                    q = isinstance(td[(o if state == "NaN" else o+1)+i].span.next, str)  # check if not blank
                    points[i+1] = td[(o if state == "NaN" else o+1)+i].span.next.strip() if q else ''
                points_sum = td[-1].span.next.strip()
                # Refresh num holder
                num_holder = num
                print((f"    ({state}) {num}. {name} | {year} {school} k:{level} P:{points_bf} | {points}",
                       f" | SUM:{points_sum}"))
    except Exception:
        logging.exception(f"Structure or formatting is not compatible ")


loop = asyncio.get_event_loop()
for id in ids:
    loop.run_until_complete(request(id))
