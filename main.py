#!/usr/bin/env python3

"""

STORYTELLER BOT
-------------------------
[2020] Code by Xinverse

NOTICE: The copyrights of the games belong to their respective holders,
unless otherwise specified. This project is an independent adaptation
of commercial board games into Discord bot format; the Developer is not
affiliated with them in any way.

"""

import atexit
import os
import sys
from datetime import datetime

import discord
import psutil
from discord.ext import commands
import demoji
import pytz

import globvars  # isort: split

import cmd # type: ignore

import botc
import botutils
from botutils import bot_text
from config import DISABLE_PINGS, OWNER_ID, PREFIX, TOKEN

if __name__ == "__main__":
    try:
        with open("botc.pid") as fd:
            pid = int(fd.read())
    except (FileNotFoundError, ValueError):
        pass
    else:
        if psutil.pid_exists(pid):
            print(f"Error: Another instance of the bot is already running (PID {pid}). Please close it before starting a new instance.")
            sys.exit(1)
        else:
            print("PID file is stale, removing")
            os.unlink("botc.pid")

    with open("botc.pid", "w") as fd:
        fd.write(str(os.getpid()))

    def remove_pidfile():
        os.unlink("botc.pid")

    atexit.register(remove_pidfile)

    
    last_downloaded = demoji.last_downloaded_timestamp()
    if last_downloaded is None or (datetime.now(pytz.utc) - last_downloaded).days > 100:
        # Download emojis
        print(f"===== DOWNLOADING EMOJI DATA =====")
        demoji.download_codes()

    globvars.init_client()
    globvars.init_master_state()

    def command_prefix(bot, message):
        if message.guild is None:
            return (PREFIX, "")
        else:
            return PREFIX

    # The help command
    help_command = cmd.Help(
        verify_checks = False,
        show_hidden = False,
        dm_help = True,
        dm_help_threshold = 700,
        no_category = bot_text["system"]["others_cog"],
        command_attrs = {
            "brief" : bot_text["doc"]["help"]["brief"],
            "help" : bot_text["doc"]["help"]["help"],
            "description" : bot_text["doc"]["help"]["description"]
        }
    )

    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True

    if DISABLE_PINGS:
        allowed_mentions = discord.AllowedMentions.none()
    else:
        allowed_mentions = discord.AllowedMentions(everyone=False)

    # The bot
    globvars.client = commands.Bot(
        command_prefix = command_prefix,
        owner_id = OWNER_ID,
        case_insensitive = True,
        description = "〘 Blood on the Clocktower Storyteller Bot 〙 - by Xinverse#4011",
        paginator = commands.Paginator(),
        help_command = help_command,
        intents = intents,
        allowed_mentions = allowed_mentions,
    )

    globvars.client.add_check(botutils.check_if_not_ignored)
    botutils.rate_limit_commands.start()

    # Loading game packs
    print("===== LOADING GAME PACKS =====")
    botc.load_pack(globvars.master_state)
    print(globvars.master_state.game_packs)

    extensions = ["admin", "gameplay", "miscellaneous", "listeners"]

    # Loading command extensions
    print("===== LOADING COMMAND EXTENSIONS =====")

    for extension in extensions:
        globvars.client.load_extension(f"cmd.{extension}")
        print(f"> {extension} cog successfully loaded")

    print("===== LOGGING IN =====")
    globvars.client.run(TOKEN)
