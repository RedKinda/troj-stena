import logging
import constants as cn
import strings as st
import database as db


async def find_message(channel, starts_with):
    async for message in channel.history():
        if message.author.bot and message.content.startswith(starts_with):
            logging.info("Found")
            return message
            break
    return None


def load_default_data(faq=True, rules=True):
    ret = []
    if faq:
        db.load_to_map(cn.FB_MSGS, u'faq', u'list', st.DEFAULT_FAQ_CONTENT)
        ret.append("faq")
    if rules:
        db.load_to_map(cn.FB_MSGS, u'rules', u'list', st.DEFAULT_RULES)
        ret.append("rules")
    return ret
