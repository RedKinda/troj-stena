import discord
from discord.ext import commands
import strings as st
import traceback
import logging
import globals
import sys

# Import project constants module
if globals.TESTVERSION:
    import testconstants as cn
else:
    import constants as cn


# Logging
command_log = logging.getLogger('commands')
event_log = logging.getLogger('events')


# Declare some decorators for restrictig commands
# Check functions used by commands
def in_channel(self, *args):
    def channel_check(ctx):
        channels = [globals.server.get_channel(channel) for channel in args]
        if ctx.channel not in channels:
            raise self.WrongChannel()
        else:
            return True
    return commands.check(channel_check)


class AbstractCommand(commands.Cog):
    """Parrent class for all command cogs"""

    def __init__(self, name):
        self.bot = globals.bot
        self.server = globals.server
        self.bot.add_cog(self)
        event_log.info(f"Cog {name} loaded.")

    # Provides usage information for each command
    async def help_command(self, ctx):
        help_header = st.HELP_HEADER.format(ctx.prefix, ctx.command.name)
        msg_string = f"```{help_header}\n{cn.SEPARATOR_COUNT*cn.SEPARATOR}\n"
        for usage in st.COMMANDS_HELP[ctx.command.name]:
            if usage.startswith("*"):
                msg_string += f"{usage}\n"
            else:
                msg_string += f" - {ctx.prefix}{ctx.command.name} {usage}\n"
        msg_string += "```"
        await ctx.channel.send(msg_string)

    # Define error classes
    class WrongChannel(commands.CommandError):
        pass

    class RuleNotFound(commands.CommandError):
        pass

    class FaqNotFound(commands.CommandError):
        pass

    # Handle possible command errors
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

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
            await self.help_command(ctx)
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

        if isinstance(error, self.WrongChannel):
            await ctx.send(st.CHANNEL_ERROR.format(ctx.prefix, ctx.command.name))
            return

        if isinstance(error, self.RuleNotFound):
            await ctx.send(st.RULE_NOT_FOUND)
            return

        if isinstance(error, self.FaqNotFound):
            await ctx.channel.send(st.FAQ_NOT_FOUND)

        # ignore all other exception types, but print them
        command_log.error(f"Unhandled exception occurred while running command {ctx.command.name}!", exc_info=True)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    # Command debug events
    @globals.bot.event
    async def on_command(ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            event_log.info(f"{ctx.message.author} used command {ctx.command.name} in {ctx.channel.name} channel.")
        else:
            event_log.info(f"{ctx.message.author} used command {ctx.command.name} in DM channel.")

    @globals.bot.event
    async def on_command_completion(_):
        event_log.debug("Command executed successfully.")
