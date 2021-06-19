"""Contains some tasks/async loops"""

import asyncio
import csv
import json

import discord
import toml
from discord.ext import tasks

import botutils
from botutils import bot_text
from config import (ALIVE_ROLE_ID, BACKUP_INTERVAL_MIN, LOBBY_TIMEOUT, PREFIX,
                    START_CLEAR, STATUS_CYCLE, TOKEN_RESET, VOTESTOP_CLEAR)

lobby_timeout_str = bot_text["system"]["lobby_timeout"]
not_enough_votes_to_start = bot_text["system"]["not_enough_votes_to_start"]
not_enough_votestop_votes = bot_text["system"]["not_enough_votestop_votes"]

VERSION = "v0.4.0-beta"

@tasks.loop(seconds = TOKEN_RESET, count = None)
async def rate_limit_commands():
    """Rate limit the frequency of commands"""
    import globvars
    for user in globvars.ratelimit_dict:
        globvars.ratelimit_dict[user] = 0


@tasks.loop(seconds = LOBBY_TIMEOUT, count = 1)
async def lobby_timeout():
    """Lobby timeout loop"""
    pass


@lobby_timeout.after_loop
async def after_lobby_timeout():
    """After lobby timeout"""
    import globvars

    # Don't cancel the game if it just started
    if globvars.master_state.game:
        return
    # Only send the lobby timeout message if someone is still in the game
    if not lobby_timeout.is_being_cancelled():
        await botutils.send_lobby(lobby_timeout_str.format(botutils.make_role_ping(ALIVE_ROLE_ID)))
    # Remove the alive role from everyone
    await botutils.remove_all_alive_roles_pregame()
    # Clear the master pregame state
    globvars.master_state.pregame.clear()
    botutils.update_state_machine()

update_status = False
current_status_index = 0
@tasks.loop(count = None)
async def cycling_bot_status():
    """A task to cycle bot status messages"""

    import globvars
    global current_status_index
    global update_status

    update_status = False

    if globvars.master_state.game:
        ingame_messages = [
            "Blood on the Clocktower",
            "a{n} {count} player {gamemode} game".format(
                                                            count = len(globvars.master_state.game.sitting_order),
                                                            gamemode = globvars.master_state.game.gamemode.value,
                                                            n = ("n" if len(globvars.master_state.game.sitting_order) in [8, 11] else "")
                                                        ),
        ]

        message = ingame_messages[current_status_index % len(ingame_messages)]
    elif globvars.master_state.session == botutils.BotState.pregame:
        pregame_messages = [
            "Blood on the Clocktower",
            "{p}join | {count} player{s} in lobby".format(
                                                            p = PREFIX,
                                                            count = len(globvars.master_state.pregame),
                                                            s = ("" if len(globvars.master_state.pregame) == 1 else "s")
                                                        ),
            VERSION
        ]

        message = pregame_messages[current_status_index % len(pregame_messages)]
    else:
        empty_messages = [
            "Blood on the Clocktower",
            "{p}help | {p}join".format(p = PREFIX),
            VERSION
        ]

        message = empty_messages[current_status_index % len(empty_messages)]

    activity = discord.Activity(name = message, type = discord.ActivityType.playing)
    await globvars.client.change_presence(activity = activity)

    current_status_index += 1

    for _ in range(STATUS_CYCLE):
        if update_status:
            break
        await asyncio.sleep(1)


@tasks.loop(count = 1)
async def start_votes_timer():
    """A task to clear start votes periodically"""

    import globvars
    await asyncio.sleep(START_CLEAR)
    globvars.start_votes.clear()
    await botutils.send_lobby(not_enough_votes_to_start)

@tasks.loop(count = 1)
async def votestop_votes_timer():
    """A task to clear votestop votes periodically"""

    import globvars
    await asyncio.sleep(VOTESTOP_CLEAR)
    globvars.votestop_votes.clear()
    await botutils.send_lobby(not_enough_votestop_votes)
