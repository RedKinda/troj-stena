import logging
import constants as cn
import strings as st
import database as db


class MessageNotFoundException(Exception):
    pass


async def find_message(channel, query):

    if isinstance(query, int):
        return find_message_by_id(channel, query)
    if isinstance(query, str):
        return find_message_by_content_prefix(channel, query)
    raise ValueError("Invalid query type")


async def find_message_by_id(channel, msg_id):
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
