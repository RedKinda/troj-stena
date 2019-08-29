import asyncio
import logging
import os
import re
import sys
import time
import typing
import traceback
import collections
from datetime import datetime

import discord
import lxml
import lxml.etree
import aiohttp
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

import constants as cn
import strings as st
import helpers as hp
import database as db


bot = Bot(command_prefix="$", status=discord.Status.online, activity=discord.Game(name=cn.BOT_MSG))
bot.remove_command("help")  # delete existing help command
trojsten = discord.Guild
ready = False
FIRST_CHECK = False
load_dotenv()

# Set global variables
weird_messages = {}
# timeouts = {}
seminars = []
users = {}
message_data = {}

color_msg = None
white = discord.Role
orange = discord.Role
green = discord.Role
blue = discord.Role
colors = []
roles_and_emojis = []

admin = discord.Role
veduci = discord.Role

# logging
logscope = logging.INFO if not cn.DEBUG_MODE else logging.DEBUG
logging.basicConfig(level=logscope)
command_log = logging.getLogger('commands')
event_log = logging.getLogger('events')
management_log = logging.getLogger('management')
web_log = logging.getLogger('web')
loggers = [command_log, event_log, management_log, web_log]


class User:
    def __init__(self, warnings, subscribtions):
        self.warnings = warnings
        self.subscribtions = subscribtions

    @staticmethod
    def from_dict(source):
        return User(source["warnings"], source["subscribtions"])


@bot.event
async def on_ready():
    global trojsten, ready
    global white, orange, green, blue, colors
    global admin, veduci
    # global timeouts

    ready = True

    logging.info(f"Bot loaded as {bot.user.name}#{str(bot.user.discriminator)}")

    trojsten = bot.get_guild(cn.GUILD_ID)
    if trojsten is None:
        logging.critical("Guild not recognized! Change its ID in constants file")
        await bot.close()
        sys.exit(1)

    white = trojsten.get_role(cn.WHITE_ROLE)
    orange = trojsten.get_role(cn.ORANGE_ROLE)
    green = trojsten.get_role(cn.GREEN_ROLE)
    blue = trojsten.get_role(cn.BLUE_ROLE)
    colors = [(white, cn.WHITE_EMOJI), (orange, cn.ORANGE_EMOJI), (green, cn.GREEN_EMOJI), (blue, cn.BLUE_EMOJI)]

    admin = trojsten.get_role(cn.ADMIN_ROLE)
    veduci = trojsten.get_role(cn.VEDUCI_ROLE)

    # get message message_data
    msgs = {"rules", "faq"}
    for msg in msgs:
        if db.check_document(cn.FB_MSGS, msg):
            result = db.get_document(cn.FB_MSGS, msg).to_dict()["list"]
            message_data[msg] = collections.OrderedDict(sorted(result.items()))
    loader = hp.load_default_data("faq" not in message_data.keys(), "rules" not in message_data.keys())
    if len(loader) == 0:
        logging.info("Loaded message database!")
    else:
        for msg in loader:
            message_data[msg] = db.get_document(cn.FB_MSGS, msg).to_dict()["list"]
        logging.info("Loaded and uploaded default message database!")

    # add existin1g users to message_database, load saved
    member_debug = {"l": 0, "c": 0}
    for member in trojsten.members:
        if member.id != bot.user.id:
            if db.check_document(cn.FB_USERS, str(member.id)):
                member_debug["l"] += 1
                users[member.id] = User.from_dict(db.get_document(cn.FB_USERS, str(member.id)).to_dict())
            else:
                member_debug["c"] += 1
                db.load(cn.FB_USERS, str(member.id), vars(User({"number": 0, "reasons": []}, [])))
    logging.info(f"Loaded member database!\n - Loaded:{member_debug['l']} +:{member_debug['c']}")

    # load saved info about seminars
    sem_list = ["kms", "fks", "ksp", "ufo", "prask"]
    for sem in sem_list:
        if db.check_document(cn.FB_SEMINARS, sem):
            seminars.append(Seminar.from_dict(db.get_document(cn.FB_SEMINARS, sem).to_dict()))
        else:
            seminar = Seminar(sem)
            seminars.append(seminar)
            db.load(cn.FB_SEMINARS, sem, seminar.to_dict())
    logging.info("Loaded seminar database!")

    # setup classes
    for sem in seminars:
        sem.m_channel = bot.get_channel(sem.m_channel)
        sem.role = trojsten.get_role(sem.role)
        sem.emoji = bot.get_emoji(sem.emoji)
        if sem.active:
            try:
                sem.message = await hp.find_message(sem.m_channel, sem.msg_id)
                bot.loop.create_task(updateloop(sem))
            except Exception:
                management_log.warning(f"Main seminar mesage of {sem.name} was removed or not found!")
        roles_and_emojis.append((sem.role, sem.emoji))

    # MSGS #
    await welcome_message()
    await role_message()
    await color_message()

    bot.loop.create_task(permaloop())


# ###############################
# ###### MESSAGE HANDLING #######
# ###############################


# region Messages    role_msg = await hp.find_message(general, _message)
async def welcome_message():
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    _rules, _faq = "", ""
    keys = list(message_data['rules'].keys())
    for i in range(len(message_data["rules"])):
        _rules += f"{i+1}. {message_data['rules'][keys[i]]}\n"
    for i in message_data["faq"].keys():
        key = list(message_data['faq'][i].keys())[0]
        _faq += f"> __*{key}*__\n{message_data['faq'][i][key]}\n"
    add = st.ADDITIONAL_CONTENT.format(bot.get_user(cn.ZAJO_ID).mention)
    _message = st.DEFAULT_WELCOME_MESSAGE.format(st.WELCOME_HEADER, _rules, _faq) + add
    management_log.info("searching for welcome message ...")
    message = await hp.find_message(general, _message)
    if message is not None:
        if message.content != _message:
            await message.edit(content=_message)
            management_log.info("Changed")
        management_log.info("Welcome msg stat - OK")
    else:
        management_log.info("Generating new")
        await general.send(_message)


role_msg = None


async def role_message():
    global role_msg
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    _message = st.ROLE_MESSAGE
    management_log.info("Searching for role message ...")
    role_msg = await hp.find_message(general, _message)
    if role_msg is not None:
        management_log.info("React msg stat - OK")
        for react in role_msg.reactions:
            async for reactor in react.users():
                for role, emoji in roles_and_emojis:
                    if react.emoji == emoji and role not in reactor.roles:
                        logging.info(f"Added role {role.name} to {reactor.name}")
                        await reactor.add_roles(role)
        management_log.info("React -> Role sync - OK")
    else:
        management_log.info("Generating new")
        msg = await general.send(_message)
        role_msg = msg
        for sem in seminars:
            await msg.add_reaction(bot.get_emoji(sem.emoji))

color_msg = None


async def color_message():
    global color_msg
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    _message = st.COLOR_MESSAGE
    management_log.info("Searching for color message ...")
    color_msg = await hp.find_message(general, _message)
    if color_msg is not None:
        management_log.info("Color msg stat - OK")
        for react in color_msg.reactions:
            async for reactor in react.users():
                for role, emoji in colors:
                    if role not in reactor.roles and react.emoji == emoji:
                        event_log.info(f"Added role {role.name} to {reactor.name}")
                        await reactor.add_roles(role)
        management_log.info("React -> Role sync - OK")
    else:
        management_log.info("Generating new ...")
        msg = await general.send(_message)
        color_msg = msg
        reactions = [x[1] for x in colors]
        for emoji in reactions:
            await msg.add_reaction(emoji=emoji)

# endregion

# ##############################
# ###### EVENT HANDLING  #######
# ##############################

# region Events


# used for uncached message_data :

@bot.event
async def on_raw_reaction_add(payload):
    user = trojsten.get_member(payload.user_id)
    if payload.channel_id == cn.WELCOME_CHANNEL and role_msg.id == payload.message_id and not user.bot:
        for role, emoji in roles_and_emojis:
            if payload.emoji == emoji:
                event_log.info(f"User {user.name}#{user.id} added reaction on {role.name}")
                await user.add_roles(role)
    elif payload.channel_id == cn.WELCOME_CHANNEL and color_msg.id == payload.message_id and not user.bot:
        if all(color_role not in user.roles for color_role in [x for x, _ in colors]):
            for role, emoji in colors:
                if payload.emoji.name == emoji:
                    event_log.info(f"User {user.name}#{user.id} added reaction on {role.name}")
                    await user.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    user = trojsten.get_member(payload.user_id)
    if payload.channel_id == cn.WELCOME_CHANNEL and role_msg.id == payload.message_id:
        for role, emoji in roles_and_emojis:
            if payload.emoji == emoji and (role in user.roles):
                event_log.info(f"User {user.name}#{user.id} removed reaction on {role.name}")
                await user.remove_roles(role)
    elif payload.channel_id == cn.WELCOME_CHANNEL and color_msg.id == payload.message_id:
        for role, emoji in colors:
            if payload.emoji.name == emoji:
                if role in user.roles:
                    event_log.info(f"User {user.name}#{user.id} removed reaction on {role.name}")
                    await user.remove_roles(role)


# used for cached message_data  :

# events moderation commands wip
async def react_iter(look, iterator):
    async for user in iterator():
        if user == look:
            return True
    return False


async def add_warning(user, reason):
    if user.name not in users:
        users.append(User({"number": 1, "reasons": [reason]}, []))
    else:
        users[user.id].warnings["number"] += 1
        users[user.id].warnings["reasons"].append(reason)
        event_log.info(f"{user.name} got warning because of {reason}."
                       f"They have {str(users[user.id].warnings['number'])} warnings.")
    if users[user.id].warnings["number"] >= cn.WARNINGS_TO_BAN:
        try:
            await trojsten.ban(user, reason=", ".join(users[user.id].warnings["reasons"]), delete_message_days=0)
            await user.dm_channel.send(st.BAN_MSG.format(cn.WARNINGS_TO_BAN))
        except Exception:
            await user.dm_channel.send(st.BAN_ERROR_U)
            await trojsten.get_channel(cn.ADMIN_CHANNEL).send(st.BAN_ERROR_A.format(user.name))
            event_log.exception("Error while issuing ban")
    else:
        await user.dm_channel.send(st.WARNING_MSG.format(str(users[user.id].warnings["number"]),
                                                         str(cn.WARNINGS_TO_BAN)))


@bot.event
async def on_reaction_add(react, user):
    global trojsten
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


# define error classes
class WrongChannel(commands.CommandError):
    pass


class RuleNotFound(commands.CommandError):
    pass


class FaqNotFound(commands.CommandError):
    pass


# check functions used by commands
def in_channel(*args):
    def channel_check(ctx):
        channels = [trojsten.get_channel(channel) for channel in args]
        if ctx.channel not in channels:
            raise WrongChannel()
        else:
            return True
    return commands.check(channel_check)

# COMMANDS ::

# wip command
@bot.command(enabled=False)
@in_channel(cn.TASKS_CHANNEL, cn.ADMIN_CHANNEL)
async def new(self, ctx):
    if ctx.channel == trojsten.get_channel(cn.ADMIN_CHANNEL):
        tchannel = self.bot.get_channel(cn.TASKS_CHANNEL)
    await tchannel.send(st.TASK_SUBMITED.format(ctx.author.name, cn.TASK_DONE_EMOJI))
    await ctx.pin()


@bot.command(name='purge', enabled=False)
@commands.has_role(cn.ADMIN_ROLE)
async def admin_purge(ctx, channel):
    # purges channel
    if channel is not None:
        await trojsten.get_channel(int(channel)).purge(limit=None)
    else:
        await ctx.channel.send(st.PURGE_EMPTY_CHANNEL)


@bot.command(name='rule')
@commands.guild_only()
@in_channel(cn.DEV_CHANNEL, cn.ADMIN_CHANNEL, cn.TESTING_CHANNEL)
@commands.has_any_role(cn.ADMIN_ROLE, cn.VEDUCI_ROLE)
async def admin_rule(ctx, *args):

    async def complete():
        await welcome_message()
        await ctx.message.add_reaction(emoji=cn.CHECKMARK_EMOJI)

    if len(args) != 0:
        data = message_data['rules']
        keys = list(data.keys())
        if args[0] == "add" and len(args) == 2:
            data[str(int(keys[-1])+1)] = args[1]
            db.load_to_map(cn.FB_MSGS, "rules", "list", {str(int(keys[-1])+1): args[1]})
            await complete()
        elif args[0] == "remove" and len(args) == 2:
            try:
                del data[keys[int(args[1])-1]]
                db.remove_from_map(cn.FB_MSGS, "rules", "list", keys[int(args[1])-1])
                await complete()
            except Exception:
                raise RuleNotFound
        elif args[0] == "edit" and len(args) == 3:
            try:
                data[keys[int(args[1])-1]] = args[2]
                db.load_to_map(cn.FB_MSGS, "rules", "list", {keys[int(args[1])-1]: args[2]})
                await complete()
            except Exception:
                raise RuleNotFound
        else:
            raise commands.UserInputError()
    else:
        raise commands.UserInputError()


@bot.command(name='faq')
@commands.guild_only()
@in_channel(cn.DEV_CHANNEL, cn.ADMIN_CHANNEL, cn.TESTING_CHANNEL)
@commands.has_any_role(cn.ADMIN_ROLE, cn.VEDUCI_ROLE)
async def admin_faq(ctx, *args):

    async def complete():
        await welcome_message()
        await ctx.message.add_reaction(emoji=cn.CHECKMARK_EMOJI)

    if len(args) != 0:
        data = message_data["faq"]
        keys = list(data.keys())
        if args[0] == "add" and len(args) == 3:
            data[str(int(keys[-1])+1)] = {args[1]: args[2]}
            db.load_to_map(cn.FB_MSGS, "faq", "list", {str(int(keys[-1])+1): {args[1]: args[2]}})
            await complete()
        elif args[0] == "remove" and len(args) == 2:
            try:
                del data[keys[int(args[1])-1]]
                db.remove_from_map(cn.FB_MSGS, "faq", "list", keys[int(args[1])-1])
                await complete()
            except Exception:
                raise FaqNotFound
        elif args[0] == "edit" and len(args) == 4:
            try:
                key = list(data[keys[int(args[1])-1]].keys())[0]
                question = args[2] if args[2] != "-" else key
                answer = args[3] if args[3] != "-" else data[keys[int(args[1])-1]][key]
                data[keys[int(args[1])-1]] = {question: answer}
                db.update_map(cn.FB_MSGS, "faq", "list", keys[int(args[1])-1], {question: answer})
                await complete()
            except Exception:
                raise FaqNotFound
        else:
            raise commands.UserInputError
    else:
        raise commands.UserInputError


# wip cpmmand
@bot.command(name='subscribe', aliases=['sub'], enabled=False)
@commands.dm_only()
async def subscribe(ctx, arg):
    if arg == "list":
        await ctx.channel.send(st.SUB_LIST.format('\n'.join(users[str(ctx.author.id)].subscribtions)))
    else:
        users[str(ctx.author.id)].subscribtions.append(arg)
        await ctx.channel.send(st.SUB_RESPONSE.format(arg))


@bot.command(name='lead')
async def lead(ctx, seminar: typing.Optional[str], ):
    for sem in seminars:
        if sem.name == seminar or sem.name == ctx.channel.name:
            msg = (f"👑 {sem.result_table[0].name}\n"
                   f"  2.   {sem.result_table[1].name}\n"
                   f"  3.   {sem.result_table[2].name}\n")
            await ctx.channel.send(msg)
            return
    raise commands.UserInputError


@bot.event
async def on_command_error(ctx, error):

    command_log.info("Command ended with error.")

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
    command_log.error(f"Unhandled exception occured while running command {ctx.command.name}!")
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


# Command debug events
@bot.event
async def on_command(ctx):
    event_log.info(f"{ctx.message.author} used command {ctx.command.name} in {ctx.channel.name} channel.")


@bot.event
async def on_command_completion(ctx):
    event_log.debug("Command executed succesfully.")
# endregion


# ####### MAIN LOOP ####### #
async def permaloop():
    event_log.info("Entering permaloop ...")
    await bot.wait_until_ready()
    while not bot.is_closed():
        checkpoint = time.time()
        for s in seminars:
            for res in await s.make_request("ulohy"):
                if res == "NT":
                    management_log.info(f"Task relase ocured in -> {s.name}")
                    await s.new_message()
                    await s.announcement("release")
                    # await s.voting() - wip
                    db.load(cn.FB_SEMINARS, s.name, s.to_dict())
                elif res == "NS":  # wip
                    management_log.info(f"Solution relase ocured in -> {s.name}")
                    await s.announcement("end")
                    # await s.voting("solutions") - wip
                elif res == "END":
                    management_log.info(f"Round of {s.name} has ended")
                    await s.end_message()
                    await s.announcement("end")
                db.load(cn.FB_SEMINARS, s.name, s.to_dict())
            if await s.make_request("vysledky") == "NR":
                management_log.info(f"Result table in {s.name} changed")
                # await s.update_on_results()
                db.load(cn.FB_SEMINARS, s.name, s.to_dict())
        management_log.info(f"permaloop updated in {int((time.time()-checkpoint)*1000)}ms")
        await asyncio.sleep(cn.MINIMAL_CHECKING_DELAY)
    event_log.error("Exited infinite loop")


async def updateloop(seminar):
    event_log.info(f"Entering updateloop for seminar {seminar.name} ...")
    await bot.wait_until_ready()
    while not bot.is_closed():
        if seminar.active:
            await seminar.update_message()
        else:
            return
        await asyncio.sleep(cn.UPDATE_DELAY)
# #######################################
# ###### WEB INFORMATION DOWNLOAD #######
# #######################################

# region Web


class Task:
    def __init__(self, name, link, category, points):
        self.name = name
        self.link = link
        self.category = category
        self.points = points

    @staticmethod
    def from_dict(source):
        return Task(source["name"], source["link"], source["category"], source["points"])

    def print_contents(self):
        web_log.debug([self.name, self.link, self.category, self.points])


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

    @staticmethod
    def from_dict(source):
        return Person(source["stat"], source["name"], source["year"], source["school"],
                      source["level"], source["points_bf"], source["points"], source["points_sum"])

    def print_contents(self):
        web_log.debug([self.stat, self.name, self.year, self.school,
                      self.level, self.points_bf, self.points, self.points_sum])


class Seminar:

    # Set variables
    def __init__(self, name, autoloadData=True):
        self.name = name
        self.m_channel = cn.SEMINAR_CHANNELS[self.name]
        self.role = cn.SEMINAR_ROLES[self.name]
        self.url = cn.SEMINAR_URLS[self.name]
        self.emoji = cn.SEMINAR_EMOJIS[self.name]
        self.message = None
        if autoloadData:
            self.active = False
            self.info = {
                "year": 0,
                "round": 0,
                "part": 0
            }
            self.tasks = []
            self.tasks_id = None
            self.pb_stat = None
            self.result_table = []
            self.p_length = len(self.tasks)
            self.msg_id = None
            self.r_datetime = datetime.now()

    @staticmethod
    def from_dict(source):
        sem = Seminar(source['name'], False)
        sem.active = source['active']
        sem.info = source['info']
        sem.tasks = [Task.from_dict(task) for task in source['tasks']]
        sem.result_table = [Person.from_dict(person) for person in source['r_table']]
        sem.msg_id = source['message']
        sem.r_datetime = datetime.strptime(source['datetime'], "%m/%d/%Y %H:%M:%S")
        return sem

    def to_dict(self):
        return {
            "name": self.name,
            "active": self.active,
            "info": self.info,
            "tasks": [vars(task) for task in self.tasks],
            "r_table": [vars(person) for person in self.result_table],
            "message": self.msg_id,
            "datetime": self.r_datetime.strftime("%m/%d/%Y %H:%M:%S")
        }

    def emoji_name(self):
        textA = "" if self.name == "fks" else ("K" if self.name == "kms" else "KS")
        textB = "" if self.name == "ksp" else ("S" if self.name == "kms" else "KS")
        return f"{textA}{self.emoji}{textB}"

    # # Announcments and voting messages
    async def announcement(self, atype):
        a_channel = trojsten.get_channel(cn.ANNOUNCEMENTS_CHANNEL)
        e = discord.Embed(title=f"Úlohy {self.name}",
                          url=f"{self.url}ulohy/",
                          colour=discord.Colour(cn.SEMINAR_COLOURS[self.name]))
        e.set_thumbnail(url=f"https://static.ksp.sk/images/{self.name}/{cn.SEMINAR_IMAGES[self.name]}")
        if atype == "release":
            await a_channel.send(st.TASKS_ANNOUNCEMENT.format(self.role.mention), embed=e)
        elif atype == "end":
            await a_channel(st.TASK_END_ANNOUNCEMENT.format(self.role))
        elif atype == "solutions":
            await a_channel.send(st.SOLUTIONS_RELEASE.format(self.role.mention))

    async def voting(self):
        vote_channel = trojsten.get_channel(cn.VOTING_CHANNEL)
        content = ""
        for n in range(self.p_length):
            content += (f"{str(n+1)}. [{self.tasks[n].name}]({self.tasks[n].link})\n")
        v_msg = await vote_channel.send(f"{self.emoji_name()}\n{st.VOTE_MESSAGE}\n{content}")
        await bot.add_reaction(v_msg, emoji=":one:")

    def get_time(self):
        duration = (self.r_datetime - datetime.now()).total_seconds()
        days = duration // 86400
        duration -= days*86400
        hours = duration // 3600
        duration -= hours*3600
        minutes = duration // 60
        duration -= minutes*60
        return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(duration)}s"

    def get_msg_embed(self):
        e = discord.Embed(colour=discord.Colour(cn.SEMINAR_COLOURS[self.name]),
                          description=st.TASKS_RELEASE[2].format(self.url+"/"),
                          timestamp=self.r_datetime)
        e.set_author(name=st.TASKS_RELEASE[1].format(self.name), url=self.url,
                     icon_url=f"https://cdn.discordapp.com/emojis/{cn.SEMINAR_EMOJIS[self.name]}.png?v=1")
        e.set_footer(text=self.get_time(), icon_url=cn.HOURGLASS)
        return e

    async def new_message(self):
        self.message = await self.m_channel.send(st.TASKS_RELEASE[0].format(self.role.mention),
                                                 embed=self.get_msg_embed())
        await self.message.pin()
        self.msg_id = self.message.id
        bot.loop.create_task(updateloop(self))

    async def update_message(self):
        await self.message.edit(embed=self.get_msg_embed())

    async def end_message(self):
        await self.message.edit(
            content=st.TASKS_ROUND_END.format(self.role.mention, self.url+self.tasks_id+"/")
        )
        self.msg_id = None
        self.message = None

    # # user notify system ##
    def set_result_table(self, dict):
        self.last_results = self.result_table
        self.result_table = dict

    async def update_on_results(self):
        for user in users:
            for subscriber in user.subscribtions:
                try:
                    if self.result_table.index(subscriber) != self.last_results.index(subscriber):
                        await bot.get_user(int(user)).dm_channel.send(st.SUB_CHANGE.format(subscriber, self.url))
                except Exception:
                    event_log.exception(f"Couldn't notify {bot.get_user.name} about change in results table")

    def get_person(self, clovek, row_type):
        pointers = []
        level = None
        for i in range(len(clovek)):
            rt = str(row_type[i].text).strip()
            if rt is None or rt == "":
                rt = str(row_type[i][0].text).strip()
            if "#" in rt:
                cLass = clovek[i].find(".//span").attrib["class"]
                class_to_state = {
                    'glyphicon-asterisk': 'new',
                    'glyphicon-chevron-down': 'dropped',
                    'glyphicon-chevron-up': 'advanced',
                    'glyphicon-pushpin': 'pinned'
                }
                state = "none"
                for icon in class_to_state:
                    if icon in cLass:
                        state = class_to_state[icon]
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
        return Person(state, name, year, school, level, points_before, pointers, points_sum)

    def get_time_data(self, tree):
        pb = tree.find(".//div[@data-precision='DAY']")
        self.tasks_id = pb.attrib["data-id"]
        pb_stats = pb.find(".//div[@class='progress']")[0].attrib['class']
        if "progress-bar-info" in pb_stats:
            self.pb_stat = "info"
        elif "progress-bar-warning" in pb_stats:
            self.pb_stat = "warn"
        elif "progress-bar-danger" in pb_stats:
            self.pb_stat = "danger"
        self.r_datetime = datetime.strptime(tree.find(".//em").text[12:], " %d. %B %Y %H:%M")

    async def make_request(self, to):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url+"/"+to+"/") as r:
                    output = None
                    if to == "ulohy":
                        output = await self.get_tasks(r)
                    elif to == "vysledky":
                        output = await self.get_results(r)
                    await session.close()
                    return output
        except Exception:
            web_log.exception(f"Connectivity error occured in {self.name}")

    async def get_results(self, request):
        sourceCode = await request.text()
        try:
            tree = lxml.etree.HTML(sourceCode)
        except Exception:
            web_log.exception(f"Web parsing error occured in {self.name}")
        try:
            result_list = tree.find('.//table[@class="table table-hover table-condensed results-table"]')
        except Exception:
            web_log.exception(f"Web is not compatible - {self.name}")
        try:
            output = None
            rows = result_list.findall(".//tr")
            row_type = rows[0].findall(".//th")
            results = []
            for per in rows[1:]:
                clovek = per.findall(".//td")
                results.append(self.get_person(clovek, row_type))
            if self.result_table != results:
                output = "NR"
            self.set_result_table(results)
            web_log.info(f"Succesfully loaded results for seminar {self.name}")
            return output
        except Exception:
            web_log.exception(f"Pulling error occured in {self.name}")

    async def get_tasks(self, request):
        sourceCode = await request.text()
        try:
            tree = lxml.etree.HTML(sourceCode)
        except Exception:
            web_log.exception(f"Web parsing error occured in {self.name}")
        try:
            task_list = tree.find(".//table")
        except Exception:
            web_log.exception(f"Web is not compatible {self.name}")
        try:
            output = []
            if "task-list" in task_list.attrib["class"]:
                if self.active is not True:
                    self.active = True
                    output.append("NT")
                elif self.message is None:
                    output.append("NT")
                round_info = tree.find(".//small").text.replace("\n", "").replace(" ", "").split(",")
                # set info
                info = {
                    "year": round_info[2].split(".")[0],
                    "round": round_info[0].split(".")[0],
                    "part": round_info[1].split(".")[0]
                }
                self.tasks = []
                task_rows = task_list.findall("tr")
                for node in task_rows:
                    pointers = []
                    for pointer in node[len(node.findall("td"))-1].findall("span"):
                        line = pointer.text.replace("\xa0", "").split(":")
                        pointers.append({line[0]: line[1]})
                    self.tasks.append(Task(node[1][0].text, self.url+node[1][0].attrib["href"],
                                           node[2][0].text if len(task_rows) > 2 else None, pointers))
                self.p_length = len(self.tasks)
                self.get_time_data(tree)
                # check for changes
                self.info = info
                web_log.info(f"Succesfully loaded tasks for seminar {self.name}")
                return output
            else:
                if self.active is True:
                    output.append("END")
                    self.active = False
                    self.remaining = "Round not active"
                web_log.info(f"Tasks for {self.name} are not available")
                return output
        except Exception:
            web_log.exception(f"Pulling error occured in {self.name}")
# endregion


bot.run(os.getenv('TOKEN'))
