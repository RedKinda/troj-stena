import asyncio
import logging
import os
import pickle
import re
import time
from datetime import datetime

import discord
import discord.ext.commands as commands
import lxml
import lxml.etree
import requests
from discord.ext.commands import Bot
from dotenv import load_dotenv

import constants as cn
import strings as st

# from aioconsole import ainput

bot = Bot(command_prefix="$", status=discord.Status.online, activity=discord.Game(name=cn.BOT_MSG))
trojsten = discord.Guild
ready = False
load_dotenv()

# Set global variables
warnings = {}
weird_messages = {}
subscribers = {}
# timeouts = {}
seminars = []
udaje = {}
logscope = logging.INFO if not cn.DEBUG_MODE else logging.DEBUG
logging.basicConfig(level=logscope)


@bot.event
async def on_ready():
    global trojsten, warnings, weird_messages, subscribers, seminars, udaje, ready
    # global timeouts

    ready = True

    logging.info(f"Bot loaded as {bot.user.name}#{str(bot.user.discriminator)}")

    trojsten = bot.get_guild(cn.GUILD_ID)
    if (trojsten is None):
        logging.error("Guild not recognized! Change its ID in constants file")
        await bot.close()
        exit()

    # loading files
    filehandler = open(cn.SUBSCRIBER_FILE, "wb+")
    try:			# load last saved subscriber list
        reader = open(cn.SUBSCRIBER_FILE, "rb")
        subscribers = pickle.load(reader)
        reader.close()
    except Exception:
        logging.warning("Loading subscriber file failed")
    filehandler.close()
    filehandler = open(cn.CONTENT_FILE, "wb+")
    try:			# loading data
        reader = open(cn.CONTENT_FILE, "rb")
        udaje = pickle.load(reader)
        reader.close()
    except EOFError:  # if there is no file, create it
        udaje = {
            "rules": cn.DEFAULT_RULES,
            "faq": cn.DEFAULT_FAQ_CONTENT
        }
        pickle.dump(udaje, filehandler)
    filehandler = open(cn.MAIN_DATA_FILE, "wb+")
    try:			 # loading
        reader = open(cn.MAIN_DATA_FILE, "rb")
        seminars = pickle.load(reader)
        reader.close()
    except EOFError:  # if there is no file, create them
        seminars = [Seminar("kms"),
                    Seminar("fks"),
                    Seminar("ksp"),
                    Seminar("ufo"),
                    Seminar("prask")]

        # Debug web gathering --> print first contestant in result table for seminar x
        # print(seminars[1].result_table[0].print_contents())
        pickle.dump(seminars, filehandler)
    filehandler.close()

    # setup classes
    for sem in seminars:
        sem.m_channel = bot.get_channel(sem.m_channel)

    # MSGS #
    await welcome_message()
    await role_message()
    await color_message()


# ###############################
# ###### MESSAGE HANDLING #######
# ###############################

# region Messages

async def welcome_message():
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    _rules, _faq = "", ""
    for i in range(len(udaje["rules"])):
        _rules += f"{i+1}. {udaje['rules'][i]}\n"
    for i in udaje["faq"]:
        _faq += f"- {i[0]}\n{i[1]}\n"
    add = st.ADDITIONAL_CONTENT.format(bot.get_user(cn.ZAJO_ID).mention)
    _message = st.DEFAULT_WELCOME_MESSAGE.format(st.WELCOME_HEADER, _rules, _faq) + add
    found = False
    logging.info("searching for welcome message ...")
    async for message in general.history():
        if message.author.bot and message.content.startswith(st.WELCOME_HEADER):
            logging.info("Found")
            found = True
            if (message.content != _message):
                await message.edit(content=_message)
                logging.info("Changed")
                pickle.dump(udaje, open(cn.CONTENT_FILE, "wb"))
                logging.info("Saved -> Checking")
                if pickle.load(open(cn.CONTENT_FILE, "rb")) == udaje:
                    logging.info("Check - OK")
            break
    if not found:
        logging.info("Generating new")
        await general.send(_message)
    else:
        logging.info("Welcome msg stat - OK")


_M = None


async def role_message():
    global _M
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    found = False
    _message = st.ROLE_MESSAGE
    logging.info("Searching for role message ...")
    async for message in general.history():
        if message.author.bot and message.content == _message:
            logging.info("Found")
            _M = message
            found = True
            break

    if not found:
        logging.info("Generating new")
        msg = await general.send(_message)
        _M = msg
        for sem in seminars:
            await msg.add_reaction(bot.get_emoji(sem.emoji))
    else:
        logging.info("React msg stat - OK")
        for react in message.reactions:
            async for reactor in react.users():
                for sem in seminars:
                    if react.emoji == bot.get_emoji(sem.emoji) and trojsten.get_role(sem.role) not in reactor.roles:
                        await reactor.add_roles(sem.role)
                        logging.info(f"Added role {trojsten.get_role(sem.role).name} to {reactor.name}")
        logging.info("React -> Role sync - OK")


_C = None
white = trojsten.get_role(cn.WHITE_ROLE)
orange = trojsten.get_role(cn.ORANGE_ROLE)
green = trojsten.get_role(cn.GREEN_ROLE)
blue = trojsten.get_role(cn.BLUE_ROLE)
colors = [(white, cn.WHITE_EMOJI), (orange, cn.ORANGE_EMOJI), (green, cn.GREEN_EMOJI), (blue, cn.BLUE_EMOJI)]


async def color_message():
    global _C
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    found = False
    _message = st.COLOR_MESSAGE
    logging.info("Searching for color message ...")
    async for message in general.history():
        if message.author.bot and message.content == _message:
            logging.info("Found")
            _C = message
            found = True
            break

    if not found:
        logging.info("Generating new ...")
        msg = await general.send(_message)
        _C = msg
        reactions = [x[1] for x in colors]
        for emoji in reactions:
            await msg.add_reaction(emoji=emoji)
    else:
        logging.info("Color msg stat - OK")
        for react in message.reactions:
            async for reactor in react.users():
                for role, emoji in colors:
                    if role in reactor.roles and react.emoji == emoji:
                        await reactor.add_roles(emoji)
                        logging.info(f"Added role {trojsten.get_role(role).name} to {reactor.name}")
        logging.info("React -> Role sync - OK")

# endregion

# ##############################
# ###### EVENT HANDLING  #######
# ##############################

# region Events


# used for uncached data :

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == cn.WELCOME_CHANNEL and _M.id == payload.message_id and _M.author.bot:
        user = trojsten.get_member(payload.user_id)
        for sem in seminars:
            if payload.emoji == bot.get_emoji(sem.emoji):
                await user.add_roles(trojsten.get_role(sem.role))
    elif payload.channel_id == cn.WELCOME_CHANNEL and _C.id == payload.message_id and _C.author.bot:
        user = trojsten.get_member(payload.user_id)
        if all(color_role not in user.roles for color_role in [x[1] for x in colors]):
            for role, emoji in colors:
                if payload.emoji.name == emoji:
                    await user.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id == cn.WELCOME_CHANNEL and _M.id == payload.message_id and _M.author.bot:
        user = trojsten.get_member(payload.user_id)
        for sem in seminars:
            if payload.emoji == bot.get_emoji(sem.emoji) and sem.role in user.roles:
                await user.remove_roles(sem.role)
    elif payload.channel_id == cn.WELCOME_CHANNEL and _C.id == payload.message_id and _C.author.bot:
        for role, emoji in colors:
            if payload.emoji.name == emoji:
                if role in user.roles:
                    await user.remove_roles(role)


# used for cached data  :

# events moderation commands wip
async def react_iter(look, iterator):
    async for user in iterator():
        if user == look:
            return True
    return False


async def add_warning(user, reason):
    if user.name not in warnings:
        warnings[user.id] = [1, reason]
    else:
        warnings[user.id][0] += 1
        warnings[user.id].append(reason)
        logging.info(f"{user.name} got warning because of {reason}. They have {str(warnings[user.id][0])} warnings.")
    if warnings[user.id][0] >= cn.WARNINGS_TO_BAN:
        try:
            await trojsten.ban(user, reason=", ".join(warnings[user.id][1:]), delete_message_days=0)
            await user.dm_channel.send(st.BAN_MSG.format(cn.WARNINGS_TO_BAN))
        except Exception:
            await user.dm_channel.send(st.BAN_ERROR_U)
            await trojsten.get_channel(cn.ADMIN_CHANNEL).send(st.BAN_ERROR_A.format(user.name))
            logging.exception("Error while issuing ban")
    else:
        await user.dm_channel.send(st.WARNING_MSG.format(str(warnings[user.id][0]), str(cn.WARNINGS_TO_BAN)))


@bot.event
async def on_reaction_add(react, user):
    global trojsten
    global warnings
    global weird_messages

    if react.message.channel == cn.TASKS_CHANNEL and react.emoji == cn.CHECKMARK_EMOJI and react.message.pinned:
        comm = f"{bot.get_prefix(react.message)}new"
        if react.message.content.startswith(comm) and await react_iter(react.message.author, react.users):
            task_name = react.message.content[5:]
            await react.message.channel.send(st.TASK_COMPLETED.format(react.message.author.name, task_name))
            await react.message.unpin()

    elif react.emoji == bot.get_emoji(cn.CHEATALERT_EMOJI):  # cheat alert
        if react.message.channel == trojsten.get_channel(cn.MODERATING_CHANNEL):  # moderating channel
            nafetch = weird_messages[react.message.id]
            react.message = await trojsten.get_channel(nafetch[1]).fetch_message(nafetch[0])
            if react.message.author.dm_channel is None:
                await react.message.author.create_dm()
            await react.message.author.dm_channel.send(st.DELETE_NOTICE.format(react.message.author.mention))
            hour = react.message.created_at.time().hour + 2
            minute = react.message.created_at.time().minute
            second = react.message.created_at.time().second
            sent = datetime.time(hour=hour, minute=minute, second=second)
            # react.message.created_at.time().hour += 2
            timestr = sent.isoformat(timespec="seconds")
            r_chan = react.message.channel.name
            r_msg = react.message.content
            details = st.DELETE_DETAILS.format(timestr, st.UTC_STRING, r_chan, r_msg)
            await react.message.author.dm_channel.send(details)

        # elif user in trojsten.get_role(598517418968743957).members and react.message.channel
        # != trojsten.get_channel(599249382038044703): #role: Veducko, channel: isnt #moderating
        # await react.message.channel.send(react.message.author +
        # "!!! Your message was deleted because of serious rules violation.")
        await react.message.delete()
        await add_warning(react.message.author, "CHEAT alert emoji")

    elif react.emoji == bot.get_emoji(cn.QUESTIONABLE_EMOJI):
        chan = trojsten.get_channel(cn.MODERATING_CHANNEL)
        s_message = st.SUSPICIOUS_MESSAGES(react.message.channel.name, react.message.content, react.message.jump_url)
        newmsg = await chan.send(s_message)
        weird_messages[newmsg.id] = (react.message.id, react.message.channel.id)

    global ready
    if not ready or react.message.author == bot:
        return
    # slowmode ????
    """
    slowmode = 10
    if message.author in trojsten.get_role(id_bank["timeOut role"]).members: #timeOut role
        if message.author.name not in timeouts:
            timeouts[message.author.name] = time.time()
        elif timeouts[message.author.name] + slowmode > time.time():
            await message.delete()
            return
        else:
            timeouts[message.author.name] = time.time()
    """
# endregion

# ###############################
# ###### COMMAND HANDLING #######
# ###############################

# region Commands


# provides usage information for each command
async def help_command(ctx):
    help_header = st.HELP_HEADER.format(ctx.prefix, ctx.command.name)
    msg_string = f"```{help_header}\n{cn.SEPARATOR_COUNT*cn.SEPARATOR}\n"
    for usage in st.COMMANDS_HELP[ctx.command.name]:
        if usage.startswith("*"):
            msg_string += f"{usage}\n"
        else:
            msg_string += f" - {ctx.prefix}{ctx.command.name} {usage}\n"
    msg_string += "```"
    await ctx.channel.send(msg_string)


# check functions used by commands
def in_admin_channel():
    def channel_check(ctx):
        channels = [trojsten.get_channel(channel) for channel in [cn.DEV_CHANNEL, cn.ADMIN_CHANNEL, cn.TESTING_CHANNEL]]
        if ctx.channel not in channels:
            raise WrongChannel()
        else:
            return True
    return commands.check(channel_check)

# COMMANDS ::


# wip command
@bot.command(enabled=False)
async def new(ctx):
    if ctx.channel == trojsten.get_channel(cn.TASKS_CHANNEL) or ctx.channel == trojsten.get_channel(cn.ADMIN_CHANNEL):
        if ctx.channel == trojsten.get_channel(cn.ADMIN_CHANNEL):
            tchannel = bot.get_channel(cn.TASKS_CHANNEL)
        await tchannel.send(st.TASK_SUBMITED.format(ctx.author.name, cn.TASK_DONE_EMOJI))
        await ctx.pin()


@bot.command(name='purge')
async def admin_purge(ctx, channel):
    # purges server
    if ctx.author.role == trojsten.get_role(cn.ADMIN_ROLE):
        if channel is not None:
            await trojsten.get_channel(int(channel)).purge(limit=None)
        else:
            await ctx.channel.send(st.PURGE_EMPTY_CHANNEL)


@bot.command(name='rule')
@in_admin_channel()
@commands.guild_only()
@commands.has_any_role(cn.ADMIN_ROLE, cn.VEDUCI_ROLE)
async def admin_rule(ctx, *args):
    global udaje

    async def complete():
        await welcome_message()
        await ctx.message.add_reaction(emoji=cn.CHECKMARK_EMOJI)

    if len(args) != 0:
        logging.info(ctx.message.content)
        if args[0] == "add" and len(args) == 2:
            udaje["rules"].append(args[1])
            await complete()
        elif args[0] == "remove" and len(args) == 2:
            try:
                del udaje["rules"][int(args[1])-1]
                await complete()
            except Exception:
                raise RuleNotFound
        elif args[0] == "edit" and len(args) == 3:
            try:
                udaje["rules"][int(args[1])-1] = args[2]
                await complete()
            except Exception:
                raise RuleNotFound
    else:
        raise commands.UserInputError()


@bot.command(name='faq')
@in_admin_channel()
@commands.guild_only()
@commands.has_any_role(cn.ADMIN_ROLE, cn.VEDUCI_ROLE)
async def admin_faq(ctx, *args):
    global udaje

    async def complete():
        await welcome_message()
        await ctx.message.add_reaction(emoji=cn.CHECKMARK_EMOJI)

    if len(args) != 0:
        if args[0] == "add" and len(args) == 3:
            udaje["faq"].append([args[1], args[2]])
            await complete()
        elif args[0] == "remove" and len(args) == 2:
            try:
                del udaje["faq"][int(args[1])-1]
                await complete()
            except Exception:
                raise FaqNotFound
        elif args[0] == "edit" and len(args) == 4:
            try:
                question = args[2] if args[2] != "-" else udaje["faq"][int(args[1])-1][0]
                answer = args[3] if args[3] != "-" else udaje["faq"][int(args[1])-1][1]
                udaje["faq"][int(args[1])-1] = [question, answer]
                await complete()
            except Exception:
                raise FaqNotFound
    else:
        raise commands.UserInputError


# wip cpmmand
@bot.command(name='subscribe', aliases=['sub'], enabled=False)
@commands.dm_only()
async def subscribe(ctx, arg):
    global subscribers
    if arg == "list":
        await ctx.channel.send(st.SUB_LIST.format('\n'.join(subscribers[str(ctx.author.id)])))
    else:
        subscribers[str(ctx.author.id)].append(arg)
        await ctx.channel.send(st.SUB_RESPONSE.format(arg))


# define error classes
class WrongChannel(commands.CommandError):
    def __init__(self):
        return super().__init__()


class RuleNotFound(commands.CommandError):
    def __init__(self):
        return super().__init__()


class FaqNotFound(commands.CommandError):
    def __init__(self):
        return super().__init__()


@bot.event
async def on_command_error(ctx, error):

    logging.info("Command ended with error.")

    # if command has local error handler, return
    if hasattr(ctx.command, "on_error"):
        return

    # get the original exception
    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.send(st.CMD_NONEXISTENT)
        return

    if isinstance(error, commands.DisabledCommand):
        await ctx.channel.send(st.DISABLED_ERROR)
        return

    if isinstance(error, commands.UserInputError):
        await help_command(ctx)
        return

    if isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send(st.ONLY_GUILD_ERROR)
        except discord.Forbidden:
            pass
        return

    if isinstance(error, commands.PrivateMessageOnly):
        await ctx.send(st.ONLY_DM_ERROR)
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send(st.PERMISSION_ERROR)
        return

    if isinstance(error, WrongChannel):
        await ctx.send(st.CHANNEL_ERROR.format(ctx.prefix, ctx.command.name))
        return

    if isinstance(error, RuleNotFound):
        await ctx.send(st.RULE_NOT_FOUND)
        return

    if isinstance(error, FaqNotFound):
        await ctx.channel.send(st.FAQ_NOT_FOUND)

    # ignore all other exception types, but print them
    logging.warning(f"Ignoring exception in command {ctx.command.name}:")
    logging.exception("Unhandled exception occured while running command!")

# ####### MAIN LOOP ####### #

# Command ebug events


@bot.event
async def on_command(ctx):
    logging.info(f"{ctx.message.author} used command {ctx.command.name} in {ctx.channel.name} channel.")


@bot.event
async def on_command_completion(ctx):
    logging.debug("Execution of command was succesfull.")
# endregion


async def permaloop():
    # global last_update
    last_update = 0
    while True:
        await asyncio.sleep(2)
        if last_update + cn.MINIMAL_UPDATE_DELAY < time.time():
            last_update = time.time()
            for s in seminars:
                res = s.get_info()
                for change in res:
                    if change == "new problems":
                        s.newroundmessage()
                        s.voting("release")
                    elif change == "new solutions":
                        s.voting("ideal solutions")
                    elif change == "new results":
                        s.update_on_results()
                    elif change == "end of turn":
                        s.end_message()


# #######################################
# ###### WEB INFORMATION DOWNLOAD #######
# #######################################

# region Web


class Problem:
    def __init__(self, name, link, points):
        self.name = name
        self.link = link
        self.points = points

    def print_contents(self):
        logging.info([self.name, self.link, self.points])


class Person:
    def __init__(self, stat, name, year, school, level, points_bf, points, points_sum):
        self.stat = stat
        self.name = name
        self.year = year
        self.school = school
        self.level = level
        self.points_bf = points_bf
        self.points = points
        self.points_sum = points_sum

    def print_contents(self):
        logging.info([self.stat, self.name, self.year, self.school,
                      self.level, self.points_bf, self.points, self.points_sum])


class Seminar:

    # Set variables
    def __init__(self, name):
        self.name = name
        self.m_channel = cn.SEMINAR_CHANNELS[self.name]
        self.role = cn.SEMINAR_ROLES[self.name]
        self.url = cn.SEMINAR_URLS[self.name]
        self.emoji = cn.SEMINAR_EMOJIS[self.name]
        self.active = False
        self.year = 0
        self.round = 0
        self.part = 0
        self.problems = []
        self.result_table = []
        self.get_info()
        self.p_length = len(self.problems)

    def emoji_name(self):
        textA = "" if self.name == "fks" else ("K" if self.name == "kms" else "KS")
        textB = "" if self.name == "ksp" else ("S" if self.name == "kms" else "KS")
        return f"{textA}<:{self.name}:{self.emoji}>{textB}"

    # # Announcments and voting messages
    async def announcement(self, type):
        a_channel = trojsten.get_channel(cn.VOTING_CHANNEL)
        if type == "release":
            await a_channel.send(st.TASKS_RELEASE.format(trojsten.get_role(self.role).mention, self.url))
        elif type == "end":
            await a_channel(st.TASK_ROUND_END.format(trojsten.get_role(self.role)))
        elif type == "ideal solutions":
            await a_channel.send(st.SOLUTIONS_RELEASE.format(trojsten.get_role(self.role).mention, self.url))

    async def voting(self):
        self.get_info()
        if self.active:
            vote_channel = trojsten.get_channel(cn.VOTING_CHANNEL)
            await vote_channel.send(self.emoji_name())
            await vote_channel.send(st.VOTE_MESSAGE)
            for n in range(self.p_length):
                await vote_channel.send(str(n+1) + ". " + self.problems[n].name)

    # # user notify system ##
    def set_result_table(self, dict):
        self.last_results = self.result_table
        self.result_table = dict

    async def update_on_results(self):
        global subscribers
        for key in subscribers:
            try:
                if self.result_table.index(key) != self.last_results.index(key):
                    await bot.get_user(subscribers[key]).dm_channel.send(st.SUB_CHANGE.format(key, self.url))
            except Exception:
                logging.exception(f"Couldn't notify {bot.get_user.name} about change in results table")

    # WILL BE CHANGED
    def get_info(self):
        try:
            responseP = requests.get(self.url+"/ulohy", allow_redirects=True)
            responseR = requests.get(self.url+"/vysledky/", allow_redirects=True)
            sourceCodeP = responseP.content
            sourceCodeR = responseR.content
        except Exception:
            logging.exception(f"Connectivity error occured in {self.name}")
        try:
            treeP = lxml.etree.HTML(sourceCodeP)
            treeR = lxml.etree.HTML(sourceCodeR)
        except Exception:
            logging.exception(f"Web parsing error occured in {self.name}")
        try:
            task_list = treeP.find(".//table")
            result_list = treeR.find('.//table[@class="table table-hover table-condensed results-table"]')
        except Exception:
            logging.exception(f"Web is not compatible {self.name}")
        try:
            output = []

            def get_results():
                rows = result_list.findall(".//tr")
                row_type = rows[0].findall(".//th")
                results = []
                for per in rows[1:]:
                    clovek = per.findall(".//td")
                    pointers = []
                    level = None
                    for i in range(len(clovek)):
                        rt = str(row_type[i].text).strip()
                        if rt is None or rt == "":
                            rt = str(row_type[i][0].text).strip()
                        if "#" in rt:
                            cLass = clovek[i].find(".//span").attrib["class"]
                            if "glyphicon-asterisk" in cLass:
                                state = "new"
                            elif "glyphicon-chevron-down" in cLass:
                                state = "dropped"
                            elif "glyphicon-chevron-up" in cLass:
                                state = "advanced"
                            elif "glyphicon-pushpin" in cLass:
                                state = "pinned"
                            else:
                                state = "none"
                        elif "Meno" in rt:
                            name = clovek[i].text.strip()
                        elif "kola" in rt:
                            school = clovek[i][0].text.strip()
                        elif "R" in rt:
                            year = clovek[i].text.strip()
                        elif "Level" in rt or "K" in rt:
                            level = clovek[i][0].text.strip()
                        elif "P" in rt:
                            points_before = clovek[i][0].text.strip()
                        elif "∑" in rt:
                            points_sum = clovek[i][0].text.strip()
                        elif re.match(r"[1-9]", rt):
                            pointers.append(None if clovek[i][0].text is None else clovek[i][0].text.strip())
                    results.append(Person(state, name, year, school, level, points_before, pointers, points_sum))
                if (self.result_table != results):
                    output.append("new results")
                self.set_result_table(results)
            if("task-list" in task_list.attrib["class"]):
                self.active = True
                round_info = treeP.find(".//small").text.replace("\n", "").replace(" ", "").split(",")
                # check for changes
                round = round_info[0].split(".")[0]
                part = round_info[1].split(".")[0]
                year = round_info[2].split(".")[0]
                self.problems = []
                for node in task_list.findall("tr"):
                    pointers = []
                    for pointer in node[2].findall("span"):
                        pointers.append(pointer.text.replace("\xa0", "").split(":")[1])
                    self.problems.append(Problem(node[1][0].text, self.url+node[1][0].attrib["href"], pointers))
                self.p_length = len(self.problems)
                get_results()
                if ((self.round != round or self.part != part or self.year != year) and len(self.problems) > 0):
                    output.append("new problems")
                self.round = round
                self.part = part
                self.year = year
                # self.remaining = treeP.find(".//div[@class='progress-bar']").text
                self.r_datetime = datetime.strptime(treeP.find(".//em").text[12:], "%d. %B %Y %H:%M")
                return output
            else:
                if (self.active is False):
                    output.append("end of round")
                self.active = False
                self.remaining = "Round not active"
                get_results()
                return output
        except Exception:
            logging.exception(f"Pulling error occured in {self.name}")
# endregion


bot.run(os.getenv('TOKEN'))
