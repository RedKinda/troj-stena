import logging


async def find_message(channel, starts_with):
    async for message in channel.history():
        if message.author.bot and message.content.startswith(starts_with):
            logging.info("Found")
            return message
            break
    return None
