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
    global trojsten
    global warnings
    global weird_messages
    # global timeouts
    global subscribers
    global seminars
    global udaje
    global ready
    ready = True

    logging.info("Bot loaded as {0}#{1}".format(bot.user.name, str(bot.user.discriminator)))

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
            "rules":   cn.DEFAULT_RULES,
            "faq":   cn.DEFAULT_FAQ_CONTENT
        }
        pickle.dump(udaje, filehandler)
    filehandler = open(cn.MAIN_DATA_FILE, "wb+")
    try:			 # loading
        reader = open(cn.MAIN_DATA_FILE, "rb")
        seminars = pickle.load(reader)
        reader.close()
    except EOFError:  # if there is no file, create them
        seminars = [Seminar("kms", 598481957285920778, "https://kms.sk"),
                    Seminar("ksp", 598481977938542603, "https://ksp.sk"),
                    Seminar("fks", 598482014324129803, "https://fks.sk"),
                    Seminar("ufo", 598482065708548126, "https://ufo.fks.sk"),
                    Seminar("prask", 598482110616961054, "https://prask.ksp.sk")]

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

# Define basic methods


def save(what="inf"):
    if what == "inf":
        fh = open(cn.MAIN_DATA_FILE, "wb")
        pickle.dump(seminars, fh)
        fh.close()
    elif what == "con":
        fh = open(cn.CONTENT_FILE, "wb")
        pickle.dump(udaje, fh)
        fh.close()
    elif what == "sub":
        fh = open(cn.SUBSCRIBER_FILE, "wb")
        pickle.dump(subscribers, fh)
        fh.close()


# ###############################
# ###### MESSAGE HANDLING #######
# ###############################

# region Messages

async def welcome_message():
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    _rules, _faq = "", ""
    for i in range(len(udaje["rules"])):
        _rules += "{0}. {1}\n".format(i+1, udaje["rules"][i])
    for i in udaje["faq"]:
        _faq += "- {0}\n{1}\n".format(i[0], i[1])
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
    _message = "Nižšie si môžeš vybrať zo seminárov, ktoré riešiš alebo ťa zaujímajú:"
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
        await msg.add_reaction(bot.get_emoji(cn.KMS_EMOJI))
        await msg.add_reaction(bot.get_emoji(cn.FKS_EMOJI))
        await msg.add_reaction(bot.get_emoji(cn.KSP_EMOJI))
        await msg.add_reaction(bot.get_emoji(cn.UFO_EMOJI))
        await msg.add_reaction(bot.get_emoji(cn.PRASK_EMOJI))
    else:
        logging.info("React msg stat - OK")
        for react in message.reactions:
            async for reactor in react.users():
                if react.emoji == bot.get_emoji(cn.KSP_EMOJI):
                    ksp_r = trojsten.get_role(cn.KSP_ROLE)
                    if ksp_r not in reactor.roles:
                        await reactor.add_roles(ksp_r)
                elif react.emoji == bot.get_emoji(cn.KMS_EMOJI):
                    kms_r = trojsten.get_role(cn.KMS_ROLE)
                    if kms_r not in reactor.roles:
                        await reactor.add_roles(kms_r)
                elif react.emoji == bot.get_emoji(cn.FKS_EMOJI):
                    fks_r = trojsten.get_role(cn.FKS_ROLE)
                    if fks_r not in reactor.roles:
                        await reactor.add_roles(fks_r)
                elif react.emoji == bot.get_emoji(cn.PRASK_EMOJI):
                    prask_r = trojsten.get_role(cn.PRASK_ROLE)
                    if prask_r not in reactor.roles:
                        await reactor.add_roles(prask_r)
                elif react.emoji == bot.get_emoji(cn.UFO_EMOJI):
                    ufo_r = trojsten.get_role(cn.UFO_ROLE)
                    if ufo_r not in reactor.roles:
                        await reactor.add_roles(ufo_r)
        logging.info("React <-> Role sync - OK")

_C = None


async def color_message():
    global _C
    general = trojsten.get_channel(cn.WELCOME_CHANNEL)
    found = False
    _message = "A farbu tvojho mena:"
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
        reactions = [cn.WHITE_EMOJI, cn.ORANGE_EMOJI, cn.GREEN_EMOJI, cn.BLUE_EMOJI]
        for emoji in reactions:
            await msg.add_reaction(emoji=emoji)
    else:
        logging.info("Color msg stat - OK")
        for react in message.reactions:
            white = trojsten.get_role(cn.WHITE_ROLE)
            orange = trojsten.get_role(cn.ORANGE_ROLE)
            green = trojsten.get_role(cn.GREEN_ROLE)
            blue = trojsten.get_role(cn.BLUE_ROLE)
            async for reactor in react.users():
                if (white or orange or green or blue) not in reactor.roles:
                    if react.emoji == cn.WHITE_EMOJI:
                        await reactor.add_roles(white)
                    elif react.emoji == cn.ORANGE_EMOJI:
                        await reactor.add_roles(orange)
                    elif react.emoji == cn.GREEN_EMOJI:
                        await reactor.add_roles(green)
                    elif react.emoji == cn.BLUE_EMOJI:
                        await reactor.add_roles(blue)
        logging.info("React <-> Role sync - OK")

# endregion

# ##############################
# ###### EVENT HANDELING #######
# ##############################

# region Events


# used for uncached data :

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == cn.WELCOME_CHANNEL and _M.id == payload.message_id and _M.author.bot:
        user = trojsten.get_member(payload.user_id)
        if payload.emoji == bot.get_emoji(cn.KSP_EMOJI):
            await user.add_roles(trojsten.get_role(cn.KSP_ROLE))
        elif payload.emoji == bot.get_emoji(cn.KMS_EMOJI):
            await user.add_roles(trojsten.get_role(cn.KMS_ROLE))
        elif payload.emoji == bot.get_emoji(cn.FKS_EMOJI):
            await user.add_roles(trojsten.get_role(cn.FKS_ROLE))
        elif payload.emoji == bot.get_emoji(cn.PRASK_EMOJI):
            await user.add_roles(trojsten.get_role(cn.PRASK_ROLE))
        elif payload.emoji == bot.get_emoji(cn.UFO_EMOJI):
            await user.add_roles(trojsten.get_role(cn.UFO_ROLE))
    elif payload.channel_id == cn.WELCOME_CHANNEL and _C.id == payload.message_id and _C.author.bot:
        user = trojsten.get_member(payload.user_id)
        white = trojsten.get_role(cn.WHITE_ROLE)
        orange = trojsten.get_role(cn.ORANGE_ROLE)
        green = trojsten.get_role(cn.GREEN_ROLE)
        blue = trojsten.get_role(cn.BLUE_ROLE)
        if white not in user.roles and orange not in user.roles and green not in user.roles and blue not in user.roles:
            if payload.emoji.name == cn.WHITE_EMOJI:
                await user.add_roles(white)
            elif payload.emoji.name == cn.ORANGE_EMOJI:
                await user.add_roles(orange)
            elif payload.emoji.name == cn.GREEN_EMOJI:
                await user.add_roles(green)
            elif payload.emoji.name == cn.BLUE_EMOJI:
                await user.add_roles(blue)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id == cn.WELCOME_CHANNEL and _M.id == payload.message_id and _M.author.bot:
        user = trojsten.get_member(payload.user_id)
        if payload.emoji == bot.get_emoji(cn.KSP_EMOJI):
            ksp_r = trojsten.get_role(cn.KSP_ROLE)
            if ksp_r in user.roles:
                await user.remove_roles(ksp_r)
        elif payload.emoji == bot.get_emoji(cn.KMS_EMOJI):
            kms_r = trojsten.get_role(cn.KMS_ROLE)
            if kms_r in user.roles:
                await user.remove_roles(kms_r)
        elif payload.emoji == bot.get_emoji(cn.FKS_EMOJI):
            fks_r = trojsten.get_role(cn.FKS_ROLE)
            if fks_r in user.roles:
                await user.remove_roles(fks_r)
        elif payload.emoji == bot.get_emoji(cn.PRASK_EMOJI):
            prask_r = trojsten.get_role(cn.PRASK_ROLE)
            if prask_r in user.roles:
                await user.remove_roles(prask_r)
        elif payload.emoji == bot.get_emoji(cn.UFO_EMOJI):
            ufo_r = trojsten.get_role(cn.UFO_ROLE)
            if ufo_r in user.roles:
                await user.remove_roles(ufo_r)
    elif payload.channel_id == cn.WELCOME_CHANNEL and _C.id == payload.message_id and _C.author.bot:
        user = trojsten.get_member(payload.user_id)
        white = trojsten.get_role(cn.WHITE_ROLE)
        orange = trojsten.get_role(cn.ORANGE_ROLE)
        green = trojsten.get_role(cn.GREEN_ROLE)
        blue = trojsten.get_role(cn.BLUE_ROLE)
        if payload.emoji.name == cn.WHITE_EMOJI:
            if white in user.roles:
                await user.remove_roles(white)
        elif payload.emoji.name == cn.ORANGE_EMOJI:
            if orange in user.roles:
                await user.remove_roles(orange)
        elif payload.emoji.name == cn.GREEN_EMOJI:
            if green in user.roles:
                await user.remove_roles(green)
        elif payload.emoji.name == cn.BLUE_EMOJI:
            if blue in user.roles:
                await user.remove_roles(blue)


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
        log_msg = "{0} got warning because of {1}. They have {2} warnings."
        logging.info(log_msg.format(user.name, reason, str(warnings[user.id][0])))
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

    if react.message.channel == cn.TASKS_CHANNEL and react.emoji == '✅' and react.message.pinned:
        comm = "{0}new".format(bot.get_prefix(react.message))
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
    msg_string = "```{0}\n{1}\n".format(help_header, cn.SEPARATOR_COUNT*cn.SEPARATOR)
    for usage in st.COMMANDS_HELP[ctx.command.name]:
        if usage.startswith("*"):
            msg_string += "{0}\n".format(usage)
        else:
            msg_string += " - {0}{1} {2}\n".format(ctx.prefix, ctx.command.name, usage)
    msg_string += "```"
    await ctx.channel.send(msg_string)


# check functions used by commands
def in_admin_channel():
    def channel_check(ctx):
        channels = [trojsten.get_channel(cn.DEV_CHANNEL),
                    trojsten.get_channel(cn.ADMIN_CHANNEL),
                    trojsten.get_channel(cn.TESTING_CHANNEL)]
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
        await ctx.message.add_reaction(emoji="✅")

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
        await ctx.message.add_reaction(emoji="✅")

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
    logging.warning("Ignoring exception in command {0}:".format(ctx.command.name))
    logging.exception("Unhandled exception occured while running command!")

# ####### MAIN LOOP ####### #

# Command ebug events


@bot.event
async def on_command(ctx):
    logging.info("{0} used command {1} in {2} channel.".format(ctx.message.author, ctx.command.name, ctx.channel.name))


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


class problem:
    def __init__(self, name, link, points):
        self.name = name
        self.link = link
        self.points = points

    def print_contents(self):
        logging.info([self.name, self.link, self.points])


class person:
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
    def __init__(self, name, outchan, url):
        self.name = name
        self.m_channel = outchan
        self.role = cn.SEMINAR_ROLES[self.name]
        self.url = url
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
        return "{0}<:{1}:{2}>{3}".format(textA, self.name, cn.SEMINAR_EMOJIS[self.name], textB)

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
                logging.exception("Couldn't notify {0} about change in results table".format(bot.get_user.name))

    def get_info(self):
        try:
            responseP = requests.get(self.url+"/ulohy", allow_redirects=True)
            responseR = requests.get(self.url+"/vysledky/", allow_redirects=True)
            sourceCodeP = responseP.content
            sourceCodeR = responseR.content
        except Exception:
            logging.exception("Connectivity error occured in {0}".format(self.name))
        try:
            treeP = lxml.etree.HTML(sourceCodeP)
            treeR = lxml.etree.HTML(sourceCodeR)
        except Exception:
            logging.exception("Web parsing error occured in {0}".format(self.name))
        try:
            task_list = treeP.find(".//table")
            result_list = treeR.find('.//table[@class="table table-hover table-condensed results-table"]')
        except Exception:
            logging.exception("Web is not compatible {0}".format(self.name))
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
                    results.append(person(state, name, year, school, level, points_before, pointers, points_sum))
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
                    self.problems.append(problem(node[1][0].text, self.url+node[1][0].attrib["href"], pointers))
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
            logging.exception("Pulling error occured in {0}".format(self.name))
# endregion


bot.run(os.getenv('TOKEN'))
