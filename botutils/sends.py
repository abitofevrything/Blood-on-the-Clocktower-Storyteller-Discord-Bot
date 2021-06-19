"""Contains functions to send messages"""

import enum
import math

import globvars
from botutils import bot_text
from config import (LOBBY_CHANNEL_ID, LOGGING_CHANNEL_ID, MAX_MESSAGE_LENGTH,
                    OWNER_ID, REPLAY_CHANNEL_ID, SERVER_ID)

from .helpers import make_ping

stats_pregame_header = bot_text["cmd"]["stats_pregame_header"]


class Level(enum.Enum):
    """Level of logging"""
    info = "[INFO]"
    warning = "**[WARNING]**"
    error = "**[ERROR]**"


async def __send_log(message):
    """Send a message to the logs"""
    log_channel = globvars.client.get_channel(LOGGING_CHANNEL_ID)
    await log_channel.send(message)


def __create_python_code_block(message):
    """Create a python code block"""
    return f"```python\n{message}```"


def create_code_block(message):
    """Create a code block"""
    return f"```\n{message}```"


async def send_pregame_stats(ctx, id_list):
    """Send the pregame stats board"""
    msg = ctx.author.mention + " " + stats_pregame_header.format(len(id_list))
    temp = "\n"
    for userid in id_list:
        member = globvars.client.get_guild(SERVER_ID).get_member(int(userid))
        name = member.display_name
        temp += f"{name} ({userid})\n"
    temp = create_code_block(temp)
    msg += temp
    await ctx.send(msg)


async def send_replay(post, depth = 0):
    """Send the replay and break it down if it goes over the Discord message limit"""
    max_len = int(MAX_MESSAGE_LENGTH) - 50
    replay_channel = globvars.client.get_channel(int(REPLAY_CHANNEL_ID))
    if len(post) <= max_len:
        if depth:
            await replay_channel.send("[CONTINUED] ```asciidoc\n" + post)
        else:
            await replay_channel.send(post)
    else:
        if depth:
            await replay_channel.send("[CONTINUED] ```asciidoc\n" + post[:max_len] + "\n```")
        else:
            await replay_channel.send(post[:max_len] + "\n```")
        await send_replay(post[max_len:], depth + 1)


async def __send_long_error(post, depth=0):
    """Send a message and break it down if it goes over the Discord message limit"""
    max = int(MAX_MESSAGE_LENGTH) - 50
    if len(post) <= max:
        if depth:
            await __send_log("[CONTINUED] " + "```py\n" + post[:max])
        else:
            await __send_log(post)
            return
    else:
        if depth:
            await __send_log("[CONTINUED] " + "```py\n" + post[:max] + "```")
        else:
            await __send_log(post[:max] + "```")
        await __send_long_error(post[max:], depth + 1)


async def log(level, message):
    """Send a message to the logs with a header"""
    if level == Level.error:
        msg = f"{level.value} {make_ping(OWNER_ID)}\n{__create_python_code_block(message)}"
        await __send_long_error(msg)
    else:
        msg = f"{level.value} {message}"
        await __send_log(msg)


async def send_lobby(message, embed = None, file = None, delete_after = None):
    """Send a message to the lobby"""
    lobby_channel = globvars.client.get_channel(LOBBY_CHANNEL_ID)
    ret = await lobby_channel.send(message, embed = embed, file = file, delete_after = delete_after)
    return ret

async def send_long_message(channel, message, make_code = False, *, embed = None, file = None, delete_after = None):
    max = int(MAX_MESSAGE_LENGTH) - (6 if make_code else 0)
    ptr = 0
    for _ in range(0, math.ceil(len(message) / max)):
        msg = message[ptr:ptr+max]
        if make_code:
            if not msg.startswith('```'):
                msg = '```' + msg
            if not msg.endswith('```'):
                msg = msg + '```'

        await channel.send(msg, embed = embed, file = file, delete_after = delete_after)
        ptr += max