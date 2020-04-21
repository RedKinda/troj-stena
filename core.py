from __future__ import annotations
from typing import List
import strings as st
import helpers as hp
import database as db
import globals
from datetime import datetime
import discord
import logging
import re
import aiohttp
import asyncio
import bs4

# Import project constants module
if globals.TESTVERSION:
    import testconstants as cn
else:
    import constants as cn


users = {}

# Logging
event_log = logging.getLogger('events')
management_log = logging.getLogger('management')
web_log = logging.getLogger('web')

# ###############################
# ###### WEB INFORMATION  #######
# ###############################


# ####### Seminar update loop ####### #
async def updateloop(rnd: Round):
    """Loop responsible for updating seminar countdowns, etc ..."""

    event_log.info(f"Entering updateloop for seminar {rnd.sem.name} ...")
    await globals.bot.wait_until_ready()
    while not globals.bot.is_closed():
        # Garbage collector
        if rnd.remaining.total_seconds() <= 0:
            event_log.info(f"Exiting updateloop for seminar {rnd.sem.name} ... the round has ended.")
            await rnd.end()
            rnd.sem.rounds.pop(rnd.id)
            db.load(cn.FB_SEMINARS, rnd.sem.name, rnd.sem.to_dict())
            del(rnd)  # remove round
            return
        await asyncio.sleep(cn.UPDATE_DELAY)
        try:
            await rnd.check_round_message()
        except Exception as e:
            event_log.warning(f"{rnd.sem.name} >>> Error occured while updating {e}", exc_info=True)


# region Web
class Task:
    """Task object representing one seminar task.

    Args:
        name (str): Name of the task.
        link (str): Web adress to the task list.
        category (str): Category of task (Alfa/Beta/A/B).
        points (int): Number of points received for task.
    """

    def __init__(self, name: str, link: str, category: str, points: int):
        self.name = name
        self.link = link
        self.category = category
        self.points = points

    @staticmethod
    def from_dict(source) -> Task:
        """Method for converting dict object to Task.

        Note:
            Used for converting dicts pulled from database.

        Args:
            source (dict): Dictionary used to form Task object.
        """
        return Task(source["name"], source["link"], source["category"], source["points"])

    def print_contents(self) -> None:
        """Debug method for printing information about Task."""
        web_log.debug([self.name, self.link, self.category, self.points])


class Person:
    """Person object representing one person in seminar result table.

    Args:
        stat (str): Status of person's movement in results table.
        name (str): Name of person.
        year (int): School year which the person is attending.
        school (str): Name of school which the person is attending.
        level (int): Level or coefficient for task solving.
        points_bf (int): Points from past rounds.
        points (int): Current number of points.
        points_sum (int): Total count of points from all rounds including present.

    """

    def __init__(self, stat: str, name: str, year: int, school: str, level: int, points_bf: int, points: int,
                 points_sum: int):
        self.stat = stat
        self.name = name
        self.year = year
        self.school = school
        self.level = level
        self.points_bf = points_bf
        self.points = points
        self.points_sum = points_sum

    @staticmethod
    def from_dict(source) -> Person:
        """Method for converting dict object to Person.

        Note:
            Used for converting dicts pulled from database.

        Args:
            source (dict): Dictionary used to form Person object.
        """

        return Person(source["stat"], source["name"], source["year"], source["school"],
                      source["level"], source["points_bf"], source["points"], source["points_sum"])

    def print_contents(self) -> None:
        """Debug method for printing information about Person."""
        web_log.debug([self.stat, self.name, self.year, self.school,
                      self.level, self.points_bf, self.points, self.points_sum])


class Round:

    def __init__(self, seminar: Seminar, id: int, num: int, part: int, year: int, endtime: datetime,
                 tasks: List[Task], results=list(), msg=None):
        self.id = id
        self.num = num
        self.part = part
        self.year = year
        self.endtime = endtime
        self.tasks = tasks
        self.results = results
        self.sem = seminar
        self.msg = msg

        self.message = None

    @staticmethod
    def from_dict(sem: Seminar, source) -> Round:
        """Method for converting dict object to Round.

        Note:
            Used for converting dicts pulled from database.

        Args:
            source (dict): Dictionary used to form Round object.

        """

        task_dict = [
            Task.from_dict(task) for task in source['tasks']
        ] if isinstance(source['tasks'][0], dict) else source['tasks'],
        result_dict = [
            {int(k): Person.from_dict(v) for k, v in table.items()} for table in source['r_table']
        ] if isinstance(source['r_table'][0]['0'], dict) else [
            {int(k): v for k, v in table.items()} for table in source['r_table']
        ],
        endtime = datetime.strptime(source['endtime'], "%m/%d/%Y %H:%M:%S")

        return Round(sem, source['id'], source['num'], source['part'], source['year'], endtime, task_dict, result_dict,
                     source["message"])

    def to_dict(self):
        """Method for converting person object to dict.

        Note:
            Used for converting Seminar objects to dicts that are beeing pushed to database.

        """
        return {
            "id": self.id,
            "num": self.num,
            "year": self.year,
            "part": self.part,
            "tasks": [vars(task) for task in self.tasks] if isinstance(self.tasks[0], Task) else self.tasks,
            "r_table": [
                {str(k): vars(person) for k, person in r_nav.items()} for r_nav in self.results
            ] if isinstance(self.results[0][0], Person) else [
                {str(k): person for k, person in r_nav.items()} for r_nav in self.results
            ],
            "message": self.msg,
            "endtime": self.endtime.strftime("%m/%d/%Y %H:%M:%S"),
        }

    # # Announcments and voting messages # #
    async def announcement(self, atype: str) -> None:
        """Method for announcing start, end and solution release of seminar.

        Args:
            atype (str): Can be one of 'release' - for round start and task reaease announcement
                                       'end' - for round end announcement
                                       'solutions' - for solution release announcement

        """
        a_channel = globals.server.get_channel(cn.ANNOUNCEMENTS_CHANNEL)
        if atype == "release":
            e = discord.Embed(
                title=f"Úlohy {self.sem.name}",
                url=f"{self.sem.url}/ulohy/{self.id}",
                colour=discord.Colour(cn.SEMINAR_COLOURS[self.sem.name])
            )
            e.set_thumbnail(url=f"https://static.ksp.sk/images/{self.sem.name}/{cn.SEMINAR_IMAGES[self.sem.name]}")
            await a_channel.send(st.TASKS_ANNOUNCEMENT.format(self.sem.role.mention), embed=e)
        elif atype == "end":
            await a_channel.send(st.TASK_END_ANNOUNCEMENT.format(self.sem.role.mention))
        elif atype == "solutions":
            await a_channel.send(st.SOLUTIONS_RELEASE.format(self.sem.role.mention))

    async def voting(self):
        vote_channel = globals.server.get_channel(cn.VOTING_CHANNEL)
        content = ""
        for n in range(self.p_length):
            content += (f"{str(n+1)}. [{self.tasks[n].name}]({self.tasks[n].link})\n")
        v_msg = await vote_channel.send(f"{self.emoji_name()}\n{st.VOTE_MESSAGE}\n{content}")
        await globals.bot.add_reaction(v_msg, emoji=":one:")

    # # Countdown message methods # #

    # region Helpers
    def update_time(self):
        self.remaining = self.endtime - datetime.now()

    async def get_time(self):
        """Get remaining time to round end or round ended message in form of formatted string"""
        time_str = f"{self.remaining.days}d {self.remaining.seconds//3600}h {(self.remaining.seconds//60)%60}m"
        return f"{time_str if self.remaining.total_seconds() > 0 else st.ROUND_END}  •  {self.endtime.strftime('%d/%m/%Y')}"

    async def get_round_message_embed(self):
        """Get round countdown embed"""
        e = discord.Embed(colour=discord.Colour(cn.SEMINAR_COLOURS[self.sem.name]),
                          description=st.TASKS_RELEASE[2].format(self.sem.url))
        e.set_author(name=st.TASKS_RELEASE[1].format(self.sem.name), url=self.sem.url,
                     icon_url=f"https://cdn.discordapp.com/emojis/{cn.SEMINAR_EMOJIS[self.sem.name]}.png?v=1")
        e.set_footer(text=await self.get_time(), icon_url=cn.HOURGLASS)
        return e
    # endregion

    async def check_round_message(self):
        """Check if round message exists and asigns it, else creates new."""
        if self.message is None:
            self.update_time()
            try:
                event_log.info(f"Checking for round message for {self.sem.name}#{self.id}")
                self.message = await hp.find_message_by_id(self.sem.m_channel, self.msg)
                event_log.info(f"Round message found!")
                await self.update_round_message()
                if (self.remaining.total_seconds() <= 0):
                    await self.end_round_message()
            except hp.MessageNotFoundException:
                event_log.info(f"Round message couldn't be found, creating new!")
                self.message = await self.new_round_message()
                self.msg = self.message.id
                if (len(await self.sem.m_channel.pins()) < 50):
                    await self.message.pin()
                else:
                    event_log.error("Cannot pin message due to channel pin limit")
            globals.bot.loop.create_task(updateloop(self))
        else:
            self.update_time()
            await self.update_round_message()
            if (self.remaining.total_seconds() <= 0):
                await self.end_round_message()

    async def new_round_message(self):
        """Message for round countdown message."""
        return await self.sem.m_channel.send(st.TASKS_RELEASE[0].format(self.sem.role.mention),
                                             embed=await self.get_round_message_embed())

    async def update_round_message(self):
        """Update round countdown message."""
        event_log.debug(f"Updating round message for {self.sem.name}#{self.id}")
        await self.message.edit(embed=await self.get_round_message_embed())

    async def end_round_message(self):
        """Mark as ended and reset round countdown message."""
        await self.message.edit(content=st.TASKS_ROUND_END.format(
            self.sem.role.mention, self.sem.url+"/vysledky/"+self.id.__str__()+"/")
        )
        await self.message.unpin()
        self.msg = None
        self.message = None

    # # user notify system # # WIP
    async def update_on_results(self):
        for user in users:
            for subscriber in user.subscribtions:
                try:
                    if self.result_table.index(subscriber) != self.last_results.index(subscriber):
                        await globals.bot.get_user(int(user)).dm_channel.send(st.SUB_CHANGE.format(
                            subscriber, self.url
                        ))
                except Exception:
                    web_log.exception(
                        f"Couldn't notify {globals.bot.get_user(int(user)).name} about change in results table")

    # #################################
    # ######## Round actions ##########
    # #################################

    async def release(self):
        management_log.info(f"Task relase ocured in -> {self.sem.name}#{self.id}")
        await self.check_round_message()
        await self.announcement("release")
        # await s.voting() - wip

    async def end(self):
        management_log.info(f"Round of {self.sem.name}#{self.id} has ended")
        await self.announcement("end")


class Seminar:
    """Seminar object representing one seminar.

    Args:
        name (str): Name of seminar.
        autoloadData (bool, optional): Specify if you want to create seminar preset or include relevant data yourself.

    """

    def __init__(self, name: str, autoloadData=True):
        self.name = name

        self.m_channel = globals.bot.get_channel(cn.SEMINAR_CHANNELS[self.name])
        self.role = globals.server.get_role(cn.SEMINAR_ROLES[self.name])
        self.url = cn.SEMINAR_URLS[self.name]
        self.emoji = globals.bot.get_emoji(cn.SEMINAR_EMOJIS[self.name])

        # Autoload some variables for seminar preset
        if autoloadData:
            # rounds -> round -> id, tasks, msg_id, message, endtime, result_tabs, round, part, year
            self.rounds = dict()

    async def init(self):
        # Get web data
        await self.get_tasks()
        await self.get_results()

    @staticmethod
    def from_dict(source) -> Seminar:
        """Method for converting dict object to Seminar.

        Note:
            Used for converting dicts pulled from database.

        Args:
            source (dict): Dictionary used to form Person object.

        """
        sem = Seminar(source['name'], False)
        sem.rounds = {int(k): Round.from_dict(sem, v) for k, v in source["rounds"].items()}
        return sem

    def to_dict(self):
        """Method for converting person object to dict.

        Note:
            Used for converting Seminar objects to dicts that are beeing pushed to database.

        """

        return {
            "name": self.name,
            "rounds": {str(k): v.to_dict() for k, v in self.rounds.items()},
        }

    def emoji_name(self) -> str:
        """Get name of the seminar composed from its emoji and letters."""
        textA = "" if self.name == "fks" else ("K" if self.name == "kms" else "KS")
        textB = "" if self.name == "ksp" else ("S" if self.name == "kms" else "KS")
        return f"{textA}{self.emoji}{textB}"

    # # # WEB CRAWLING # # #
    async def make_request(self, to: str, id="") -> None:
        try:
            mod = False
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.url}/{to}/{id}") as r:
                    if to == "ulohy":
                        mod = await self.get_tasks(r)
                    elif to == "vysledky":
                        mod = await self.get_results(r, id)
                    await session.close()
            return mod
        except Exception:
            web_log.exception(f"Connectivity error occured in {self.name}")

    async def get_tasks(self, request) -> None:
        """Load task objects and basic info about seminar"""
        sourceCode = await request.text()
        # Parse raw html to bs4 object
        try:
            soup = bs4.BeautifulSoup(sourceCode, 'html.parser')
        except Exception:
            logging.exception(f"Web parsing error occured in {self.name}")
        # Check for required ResultSets
        try:
            main_content = soup.find("div", {"class": "main-content"})
            task_lists = main_content.find_all("table", {"class": "task-list"})
            p_bars = main_content.find_all("div", {"class": "roundprogressbar"})
            headlines = main_content.find_all("h2")
        except Exception:
            logging.exception(f"Web is not compatible - {self.name}")
        # Scraping operation
        try:
            rounds_found, change = [], False
            if (len(task_lists) > 0):
                # Get tasks for each round
                for h, b, t in zip(headlines, p_bars, task_lists):
                    # Round info scraping
                    s_round, s_part, s_year = [int(x) for x in re.findall('([0-9]+?)\.', h.contents[1].next)]
                    s_ending_time = datetime.strptime(hp.convert_month(b.find("em").next[13:]), "%d. %B %Y %H:%M")
                    s_id = int(t.attrs['id'][-3:])
                    s_tasks = []
                    # Start scraping the task table
                    for tr in t.find_all("tr")[1:]:
                        td = tr.find_all("td")
                        name = td[1].a.next
                        link = self.url+td[1].a.attrs['href']
                        category = td[2].span.next if len(td) > 3 else "all"
                        points = [re.findall("[0-9]+", x.next)[0] for x in td[-1].find_all("span")]
                        s_tasks.append(Task(name, link, category, points))
                        web_log.debug(f"Task '{name}' sucessfully loaded.")
                    # Managing
                    rounds_found.append(s_id)
                    if not self.rounds.__contains__(s_id):
                        # Automatic release triggered
                        self.rounds[s_id] = Round(self, s_id, s_round, s_part, s_year, s_ending_time, s_tasks)
                        change = True
                        await self.rounds[s_id].release()
                    else:
                        self.rounds[s_id].num = s_round
                        self.rounds[s_id].part = s_part
                        self.rounds[s_id].year = s_year
                        self.rounds[s_id].endtime = s_ending_time
                        self.rounds[s_id].tasks = s_tasks
                    web_log.info(f"Succesfully loaded tasks for seminar {self.name}:{s_id}")
            else:
                web_log.info(f"Tasks for {self.name} are not available")
            # Ending existing rounds
            for id_, round_ in self.rounds.items():
                if id_ not in rounds_found:
                    await round_.end()
                    web_log.warn(f"Cleared round data for {self.name}#{id_}")
            return change
        except Exception:
            logging.exception(f"Structure or formatting is not compatible - {self.name}")

    async def get_results(self, request, id):
        sourceCode = await request.text()
        try:
            soup = bs4.BeautifulSoup(sourceCode, 'html.parser')
        except Exception:
            logging.exception(f"Web parsing error occured in {self.name}")
        try:
            results_table = soup.find_all("table", {"class": "results-table"})
            nav_tabs = soup.find("ul", {"class": "nav-tabs"}).find_all("li")
        except Exception:
            logging.exception(f"Web is not compatible - {self.name}")
        try:
            result_tabs, change = [], False
            for table, nav in zip(results_table, nav_tabs):
                results = {}
                num_holder = 0
                for tr in table.find_all("tr")[1:]:
                    td = tr.find_all("td")
                    if len(td) == 1:
                        results[len(results)] = f"    {td[0].next}"
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
                        points[str(i+1)] = td[(o if state == "NaN" else o+1)+i].span.next.strip() if isinstance(
                            td[(o if state == "NaN" else o+1)+i].span.next, str) else 'X'
                    points_sum = td[-1].span.next.strip()
                    # Refresh num holder
                    num_holder = num
                    results[len(results)] = Person(state, name, year, school, level, points_bf, points, points_sum)
                result_tabs.append(results)
            # Register changes
            if self.rounds[id].results != result_tabs:
                self.rounds[id].results = result_tabs
                management_log.info(f"Result table in {self.name}#{id} changed")
                change = True
            web_log.info(f"Succesfully loaded result tabs for seminar {self.name}")
            return change
        except Exception:
            logging.exception(f"Structure or formatting is not compatible - {self.name}")
        except Exception:
            web_log.exception(f"Pulling error occured in {self.name}")
# endregion
