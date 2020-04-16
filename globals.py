from discord.ext.commands import Bot
import discord
import logging
import sys

# Defines if bot uses constant list for testing servers
TESTVERSION = True

# Import project constants module
if TESTVERSION:
    import testconstants as cn
else:
    import constants as cn


# Initialize client(bot) / server
bot = Bot(command_prefix="$", status=discord.Status.online, activity=discord.Game(name=cn.BOT_MSG))
server = discord.Guild
ready = False

# Set global variables
weird_messages = {}
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
role_msg = discord.Message
color_msg = discord.Message


async def setup():
    global server, white, orange, green, blue, colors, admin, veduci
    # Setup server and check if it exists
    server = bot.get_guild(cn.GUILD_ID)
    if server is None:
        logging.critical("Guild not recognized! Change its ID in constants file")
        await bot.close()
        sys.exit(1)

    # Load variables from constants according to server data
    white = server.get_role(cn.WHITE_ROLE)
    orange = server.get_role(cn.ORANGE_ROLE)
    green = server.get_role(cn.GREEN_ROLE)
    blue = server.get_role(cn.BLUE_ROLE)
    colors = [(white, cn.WHITE_EMOJI), (orange, cn.ORANGE_EMOJI), (green, cn.GREEN_EMOJI), (blue, cn.BLUE_EMOJI)]

    admin = server.get_role(cn.ADMIN_ROLE)
    veduci = server.get_role(cn.VEDUCI_ROLE)
