import logging
import constants as cn
import strings as st
import database as db


async def find_message(channel, msg_id):
    async for message in channel.history():
        if isinstance(msg_id, int):
            if message.author.bot and message.id == msg_id:
                logging.info("Found")
                return message
                break
        elif isinstance(msg_id, str):
            if message.author.bot and message.content.startswith(msg_id):
                logging.info("Found")
                return message
                break
    raise Exception


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
