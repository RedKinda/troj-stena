import asyncio
import logging
import os
import time
import collections
import datetime as datetime_whole
import core
import strings as st
import helpers as hp
import database as db
import messages
from datetime import datetime
from dotenv import load_dotenv
import globals
# Cogs
from commands.main import Main

# Start loading timer
start_time = time.time()

# Load enviroment variables
load_dotenv()

# Import project constants module
if globals.TESTVERSION:
    import testconstants as cn
else:
    import constants as cn

globals.bot.remove_command("help")  # delete existing help command

# Logging
log_level = logging.INFO if not cn.DEBUG_MODE else logging.DEBUG
log_format = '%(asctime)-15s %(name)s:[%(levelname)s] %(message)s'
logging.basicConfig(level=log_level, format=log_format)

command_log = logging.getLogger('commands')
event_log = logging.getLogger('events')
management_log = logging.getLogger('management')
web_log = logging.getLogger('web')


# First event after bot launches
@globals.bot.event
async def on_ready():

    logging.info(f"Bot loaded as {globals.bot.user.name}#{str(globals.bot.user.discriminator)}")

    # Set global variables / setup bot + server
    await globals.setup()

    c = globals.bot.cogs
    for cog in c:
        globals.bot.remove_cog(cog)

    # Load message data [Currently -> rules and faq] from database
    msgs = {"rules", "faq"}
    # region Message loading
    for msg in msgs:
        if db.check_document(cn.FB_MSGS, msg):
            result = db.get_document(cn.FB_MSGS, msg).to_dict()["list"]
            globals.message_data[msg] = collections.OrderedDict(sorted(result.items()))
    loader = hp.load_default_data("faq" not in globals.message_data.keys(), "rules" not in globals.message_data.keys())
    if len(loader) == 0:
        logging.info("Loaded message database!")
    else:
        for msg in loader:
            globals.message_data[msg] = db.get_document(cn.FB_MSGS, msg).to_dict()["list"]
        logging.info("Loaded and uploaded default message database!")
    # endregion

    # Add existing users to database and load already saved
    member_debug = {"l": 0, "c": 0}
    # region User loading
    for member in globals.server.members:
        if member.id != globals.bot.user.id:
            if db.check_document(cn.FB_USERS, str(member.id)):
                try:
                    globals.users[member.id] = hp.User.from_dict(db.get_document(cn.FB_USERS, str(member.id)).to_dict())
                    member_debug["l"] += 1
                except Exception:
                    management_log.warning("Synced userdata was not compatible! Overwriting.", exc_info=True)
                    member_debug["c"] += 1
                    db.load(cn.FB_USERS, str(member.id), vars(hp.User({"number": 0, "reasons": []}, [])))
            else:
                member_debug["c"] += 1
                db.load(cn.FB_USERS, str(member.id), vars(hp.User({"number": 0, "reasons": []}, [])))
    logging.info(f"Loaded member database!\n - Loaded:{member_debug['l']} +:{member_debug['c']}")
    # endregion

    # Load saved info about seminars from database
    sem_list = ["kms", "fks", "ksp", "ufo", "prask"]
    # region Seminar loading
    for sem in sem_list:
        # Load from db or create
        if db.check_document(cn.FB_SEMINARS, sem):
            try:
                seminar = core.Seminar.from_dict(db.get_document(cn.FB_SEMINARS, sem).to_dict())
            except Exception:
                err = "Could not load existing seminars from database. Data might be missing or corrupted."
                management_log.error(err)
                seminar = core.Seminar(sem)
                db.load(cn.FB_SEMINARS, sem, seminar.to_dict())
        else:
            seminar = core.Seminar(sem)
            db.load(cn.FB_SEMINARS, sem, seminar.to_dict())
        # First syncing with web will ocur in permaloop
        globals.seminars.append(seminar)
        globals.roles_and_emojis.append((seminar.role, seminar.emoji))
    logging.info("Loaded seminar database!")
    # endregion

    # Mark bot's satate as ready after loading
    globals.ready = True

    for s in globals.seminars:
        for r in s.rounds.values():
            if r.msg is not None:
                await r.check_round_message()

    # Managment MSGS #
    await messages.welcome_message()
    await messages.role_message()
    await messages.color_message()

    # Initialize cogs #
    Main()

    # Enter permaloop
    globals.bot.loop.create_task(permaloop())

    # FINISH LOADING
    logging.info(f"DONE! - Bot loaded in {round(time.time() - start_time, 2)}s")
    print("-=[=================================================================]=-")

# ##############################
# ###### EVENT HANDLING  #######
# ##############################

# used for uncached message_data :
# region uncached data events
@globals.bot.event
async def on_raw_reaction_add(payload):
    user = globals.server.get_member(payload.user_id)
    if payload.channel_id == cn.WELCOME_CHANNEL and not user.bot:
        if globals.role_msg and globals.role_msg.id == payload.message_id:
            for role, emoji in globals.roles_and_emojis:
                if payload.emoji == emoji:
                    event_log.info(f"User {user.name}#{user.id} added reaction on {role.name}")
                    await user.add_roles(role)
        elif globals.color_msg and globals.color_msg.id == payload.message_id:
            if all(color_role not in user.roles for color_role in [x for x, _ in globals.colors]):
                for role, emoji in globals.colors:
                    if payload.emoji.name == emoji:
                        event_log.info(f"User {user.name}#{user.id} added reaction on {role.name}")
                        await user.add_roles(role)


@globals.bot.event
async def on_raw_reaction_remove(payload):
    user = globals.server.get_member(payload.user_id)
    if payload.channel_id == cn.WELCOME_CHANNEL:
        if globals.role_msg and globals.role_msg.id == payload.message_id:
            for role, emoji in globals.roles_and_emojis:
                if payload.emoji == emoji and (role in user.roles):
                    event_log.info(f"User {user.name}#{user.id} removed reaction on {role.name}")
                    await user.remove_roles(role)
        elif globals.color_msg and globals.color_msg.id == payload.message_id:
            for role, emoji in globals.colors:
                if payload.emoji.name == emoji:
                    if role in user.roles:
                        event_log.info(f"User {user.name}#{user.id} removed reaction on {role.name}")
                        await user.remove_roles(role)
# endregion


# used for cached message_data  :
# region cached data events
# events moderation commands wip
async def react_iter(look, iterator):
    async for user in iterator():
        if user == look:
            return True
    return False


async def add_warning(user, reason):
    if user.id not in globals.users:
        hp.create_user(str(user.id))
    else:
        globals.users[user.id].warnings["number"] += 1
        globals.users[user.id].warnings["reasons"].append(reason)
        event_log.info(f"{user.name} got warning because of {reason}."
                       f"They have {str(globals.users[user.id].warnings['number'])} warnings.")
    if globals.users[user.id].warnings["number"] >= cn.WARNINGS_TO_BAN:
        try:
            await server.ban(user, reason=", ".join(globals.users[user.id].warnings["reasons"]), delete_message_days=0)
            await user.dm_channel.send(st.BAN_MSG.format(cn.WARNINGS_TO_BAN))
        except Exception:
            await user.dm_channel.send(st.BAN_ERROR_U)
            await server.get_channel(cn.ADMIN_CHANNEL).send(st.BAN_ERROR_A.format(user.name))
            event_log.exception("Error while issuing ban", exc_info=True)
    else:
        await user.dm_channel.send(st.WARNING_MSG.format(str(globals.users[user.id].warnings["number"]),
                                                         str(cn.WARNINGS_TO_BAN)))


@globals.bot.event
async def on_reaction_add(react, _):
    global server
    global weird_messages

    if react.message.channel == cn.TASKS_CHANNEL and react.emoji == cn.CHECKMARK_EMOJI and react.message.pinned:
        comm = f"{globals.bot.get_prefix(react.message)}new"
        if react.message.content.startswith(comm) and await react_iter(react.message.author, react.users):
            task_name = react.message.content[5:]
            await react.message.channel.send(st.TASK_COMPLETED.format(react.message.author.name, task_name))
            await react.message.unpin()

    elif react.emoji == globals.bot.get_emoji(cn.CHEATALERT_EMOJI):  # cheat alert
        if react.message.channel == server.get_channel(cn.MODERATING_CHANNEL):  # moderating channel
            nafetch = weird_messages[react.message.id]
            react.message = await server.get_channel(nafetch[1]).fetch_message(nafetch[0])
            if react.message.author.dm_channel is None:
                await react.message.author.create_dm()
            await react.message.author.dm_channel.send(st.DELETE_NOTICE.format(react.message.author.mention))
            hour = react.message.created_at.time().hour + 2
            minute = react.message.created_at.time().minute
            second = react.message.created_at.time().second
            sent = datetime_whole.time(hour=hour, minute=minute, second=second)
            # react.message.created_at.time().hour += 2
            timestr = sent.isoformat(timespec="seconds")
            r_chan = react.message.channel.name
            r_msg = react.message.content
            details = st.DELETE_DETAILS.format(timestr, st.UTC_STRING, r_chan, r_msg)
            await react.message.author.dm_channel.send(details)

        # elif user in server.get_role(598517418968743957).members and react.message.channel
        # != server.get_channel(599249382038044703): #role: Veducko, channel: isnt #moderating
        # await react.message.channel.send(react.message.author +
        # "!!! Your message was deleted because of serious rules violation.")
        await react.message.delete()
        await add_warning(react.message.author, "CHEAT alert emoji")

    elif react.emoji == globals.bot.get_emoji(cn.QUESTIONABLE_EMOJI):
        chan = server.get_channel(cn.MODERATING_CHANNEL)
        s_message = st.SUSPICIOUS_MESSAGES(react.message.channel.name, react.message.content, react.message.jump_url)
        newmsg = await chan.send(s_message)
        weird_messages[newmsg.id] = (react.message.id, react.message.channel.id)

    if not globals.ready or react.message.author == globals.bot:
        return
    # slowmode ????
    """
    slowmode = 10
    if message.author in server.get_role(id_bank["timeOut role"]).members: #timeOut role
        if message.author.name not in timeouts:
            timeouts[message.author.name] = time.time()
        elif timeouts[message.author.name] + slowmode > time.time():
            await message.delete()
            return
        else:
            timeouts[message.author.name] = time.time()
    """
# endregion


# ####### MAIN LOOP ####### #
async def permaloop():
    event_log.info("Entering permaloop ...")
    await globals.bot.wait_until_ready()
    while not globals.bot.is_closed():
        checkpoint = time.time()
        modification = False
        for s in globals.seminars:
            modification = await s.make_request("ulohy")  # check tasks
            for rnd in s.rounds.values():
                modification = await s.make_request("vysledky", rnd.id)  # check results for each round
            if modification:
                db.load(cn.FB_SEMINARS, s.name, s.to_dict())  # load to database if changes
                management_log.info("Changes loaded to database!")
        management_log.info(f"permaloop updated in {int((time.time()-checkpoint)*1000)}ms")
        # users update
        management_log.info("Creating and uploading {0} users".format(len(globals.server.members)-len(globals.users)))
        for mem in globals.server.members:
            hp.create_user(str(mem.id))
        for userid in globals.users.keys():
            db.load(cn.FB_USERS, str(userid), vars(globals.users[userid]))
        await asyncio.sleep(cn.MINIMAL_CHECKING_DELAY)
    event_log.error("Exited infinite loop")


globals.bot.run(os.getenv('TOKEN'))
