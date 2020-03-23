"""Command cog"""
import commands.command as cmd
from discord.ext import commands
import database as db
import helpers as hp
import strings as st
import typing
import globals
import os
import logging

event_log = logging.getLogger('events')

# Import project constants module
if globals.TESTVERSION:
    import testconstants as cn
else:
    import constants as cn


class Main(cmd.AbstractCommand):
    """Main component containing core commands and features"""

    def __init__(self):
        event_log.info(f"Loading cog {os.path.basename(__file__)}")
        super().__init__(os.path.basename(__file__))

    @commands.command(enabled=False)
    @cmd.in_channel(cn.TASKS_CHANNEL, cn.ADMIN_CHANNEL)
    async def new(self, ctx):
        if ctx.channel == self.server.get_channel(cn.ADMIN_CHANNEL):
            tchannel = self.bot.get_channel(cn.TASKS_CHANNEL)
        await tchannel.send(st.TASK_SUBMITED.format(ctx.author.name, cn.TASK_DONE_EMOJI))
        await ctx.pin()

    @commands.command(name='purge', enabled=False)
    @commands.has_role(cn.ADMIN_ROLE)
    async def admin_purge(self, ctx, channel):
        # purges channel
        if channel is not None:
            await self.server.get_channel(int(channel)).purge(limit=None)
        else:
            await ctx.channel.send(st.PURGE_EMPTY_CHANNEL)

    @commands.command(name='rule')
    @commands.guild_only()
    @cmd.in_channel(cn.DEV_CHANNEL, cn.ADMIN_CHANNEL, cn.TESTING_CHANNEL)
    @commands.has_any_role(cn.ADMIN_ROLE, cn.VEDUCI_ROLE)
    async def admin_rule(self, ctx, *args):

        async def complete():
            # await welcome_message()
            await ctx.message.add_reaction(emoji=cn.CHECKMARK_EMOJI)

        if len(args) != 0:
            data = globals.message_data['rules']
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
                    raise self.RuleNotFound
            elif args[0] == "edit" and len(args) == 3:
                try:
                    data[keys[int(args[1])-1]] = args[2]
                    db.load_to_map(cn.FB_MSGS, "rules", "list", {keys[int(args[1])-1]: args[2]})
                    await complete()
                except Exception:
                    raise self.RuleNotFound
            else:
                raise commands.UserInputError()
        else:
            raise commands.UserInputError()

    @commands.command(name='faq')
    @commands.guild_only()
    @cmd.in_channel(cn.DEV_CHANNEL, cn.ADMIN_CHANNEL, cn.TESTING_CHANNEL)
    @commands.has_any_role(cn.ADMIN_ROLE, cn.VEDUCI_ROLE)
    async def admin_faq(self, ctx, *args):

        async def complete():
            # await welcome_message()
            await ctx.message.add_reaction(emoji=cn.CHECKMARK_EMOJI)

        if len(args) != 0:
            data = globals.message_data["faq"]
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
                    raise self.FaqNotFound
            elif args[0] == "edit" and len(args) == 4:
                try:
                    key = list(data[keys[int(args[1])-1]].keys())[0]
                    question = args[2] if args[2] != "-" else key
                    answer = args[3] if args[3] != "-" else data[keys[int(args[1])-1]][key]
                    data[keys[int(args[1])-1]] = {question: answer}
                    db.update_map(cn.FB_MSGS, "faq", "list", keys[int(args[1])-1], {question: answer})
                    await complete()
                except Exception:
                    raise self.FaqNotFound
            else:
                raise commands.UserInputError
        else:
            raise commands.UserInputError

    # wip cpmmand
    @commands.command(name='subscribe', aliases=['sub'], enabled=True)
    @commands.dm_only()
    async def subscribe(self, ctx):
        hp.create_user(str(ctx.author.id))
        arg = " ".join(ctx.message.content.split()[1:])  # parses text after command
        if arg == "list":
            await ctx.channel.send(st.SUB_LIST.format('\n'.join(globals.users[str(ctx.author.id)].subscribtions)))
        else:
            if arg not in globals.users[str(ctx.author.id)].subscribtions:
                globals.users[str(ctx.author.id)].subscribtions.append(arg)
                await ctx.channel.send(st.SUB_RESPONSE.format(arg))
            else:
                await ctx.channel.send(st.SUB_ERROR_EXISTING)

    @commands.command(name='lead')
    async def lead(self, ctx, seminar: typing.Optional[str]):
        for sem in globals.seminars:
            if sem.name == seminar or sem.name == ctx.channel.name:
                msg = (f"👑 {sem.result_table[0].name}\n"
                       f"  2.   {sem.result_table[1].name}\n"
                       f"  3.   {sem.result_table[2].name}\n")
                await ctx.channel.send(msg)
                return
        raise commands.UserInputError
