import logging
import discord
import constants as cn
import strings as st
import database as db
import globals


class MessageNotFoundException(Exception):
    pass


async def find_message(channel: discord.channel.TextChannel, query):

    if isinstance(query, int):
        return await find_message_by_id(channel, query)
    if isinstance(query, str):
        return await find_message_by_content_prefix(channel, query)
    raise ValueError("Invalid query type")


async def find_message_by_id(channel: discord.channel.TextChannel, msg_id: int):
    if msg_id is not None:
        async for message in channel.history():
            if message.author.bot and message.id == msg_id:
                logging.info(f'Found bot message {msg_id}!')
                return message
    raise MessageNotFoundException


async def find_message_by_content_prefix(channel, content_prefix):
    async for message in channel.history():
        if message.author.bot and message.content.startswith(content_prefix):
            logging.info(f'Found bot message starting {content_prefix[:5]}..!')
            return message
    raise MessageNotFoundException


def load_default_data(faq=True, rules=True):
    ret = []
    if faq:
        db.load_to_map(cn.FB_MSGS, u'faq', u'list', st.DEFAULT_FAQ_CONTENT)
        ret.append("faq")
    if rules:
        db.load_to_map(cn.FB_MSGS, u'rules', u'list', st.DEFAULT_RULES)
        ret.append("rules")
    return ret


def convert_month(mnt):
    for month in cn.MONTHS.keys():
        if month in mnt:
            return mnt.replace(month, cn.MONTHS[month])


def create_user(id):
    if str(id) not in globals.users.keys():
        globals.users[str(id)] = User({"number": 0, "reasons": []}, [])


class User:
    def __init__(self, warnings, subscribtions):
        self.warnings = warnings
        self.subscribtions = subscribtions

    @staticmethod
    def from_dict(source):
        return User(source["warnings"], source["subscribtions"])
