import logging
import strings as st
import helpers as hp
import globals

# Import project constants module
if globals.TESTVERSION:
    import testconstants as cn
else:
    import constants as cn

# Logging
management_log = logging.getLogger('management')
event_log = logging.getLogger('events')

# ###############################
# ###### MESSAGE HANDLING #######
# ###############################


# region Messages
async def welcome_message():
    """Method responsible for checking, updating and manageing the welcome message"""
    general = globals.server.get_channel(cn.WELCOME_CHANNEL)
    _rules, _faq = "", ""
    keys = list(globals.message_data['rules'].keys())
    for i in range(len(globals.message_data["rules"])):
        _rules += f"{i+1}. {globals.message_data['rules'][keys[i]]}\n"
    for i in globals.message_data["faq"].keys():
        key = list(globals.message_data['faq'][i].keys())[0]
        _faq += f"> __*{key}*__\n{globals.message_data['faq'][i][key]}\n"
    add = st.ADDITIONAL_CONTENT.format(globals.bot.get_user(cn.ZAJO_ID).mention)
    _message = st.DEFAULT_WELCOME_MESSAGE.format(st.WELCOME_HEADER, _rules, _faq) + add
    management_log.info("searching for welcome message ...")
    try:
        message = await hp.find_message(general, st.WELCOME_HEADER)
        if message.content != _message:
            await message.edit(content=_message)
            management_log.info("Changed")
        management_log.info("Welcome msg stat - OK")
    except hp.MessageNotFoundException:
        management_log.info("Generating new", exc_info=True)
        await general.send(_message)


globals.role_msg = None


async def role_message():
    """Method responsible for checking, updating and manageing the role selection message"""
    general = globals.server.get_channel(cn.WELCOME_CHANNEL)
    _message = st.ROLE_MESSAGE
    management_log.info("Searching for role message ...")
    try:
        globals.role_msg = await hp.find_message(general, _message)
        management_log.info("React msg stat - OK")
        for react in globals.role_msg.reactions:
            async for reactor in react.users():
                for role, emoji in globals.roles_and_emojis:
                    if react.emoji == emoji and role not in reactor.roles:
                        logging.info(f"Added role {role.name} to {reactor.name}")
                        await reactor.add_roles(role)
        management_log.info("React -> Role sync - OK")
    except hp.MessageNotFoundException:
        management_log.info("Generating new")
        msg = await general.send(_message)
        globals.role_msg = msg
        for sem in globals.seminars:
            await msg.add_reaction(emoji=sem.emoji)

globals.color_msg = None


async def color_message():
    """Method responsible for checking, updating and manageing the color selection message"""
    general = globals.server.get_channel(cn.WELCOME_CHANNEL)
    _message = st.COLOR_MESSAGE
    management_log.info("Searching for color message ...")
    try:
        globals.color_msg = await hp.find_message(general, _message)
        management_log.info("Color msg stat - OK")
        for react in globals.color_msg.reactions:
            async for reactor in react.users():
                for role, emoji in globals.colors:
                    if role not in reactor.roles and react.emoji == emoji:
                        event_log.info(f"Added role {role.name} to {reactor.name}")
                        await reactor.add_roles(role)
        management_log.info("React -> Role sync - OK")
    except hp.MessageNotFoundException:
        management_log.info("Generating new ...")
        msg = await general.send(_message)
        globals.color_msg = msg
        reactions = [x[1] for x in globals.colors]
        for emoji in reactions:
            await msg.add_reaction(emoji=emoji)

# endregion
