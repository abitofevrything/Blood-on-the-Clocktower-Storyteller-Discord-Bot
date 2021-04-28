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
import json
import os
import sys

import discord
import psutil
import toml
from discord.ext import commands

import globvars  # isort: split

import botc
import botutils

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

    with open("config.toml") as fd:
        config = toml.load(fd)

        TOKEN = config["bot"]["token"]
        OWNER_ID = config["ids"]["owner_id"]
        PREFIX = config["bot"]["prefix"]

    globvars.init_client()
    globvars.init_master_state()

    def command_prefix(bot, message):
        if message.guild is None:
            return (PREFIX, "")
        else:
            return PREFIX

    # The help command
    with open('botutils/bot_text.json') as json_file:
        language = json.load(json_file)

    help_command = commands.DefaultHelpCommand(
        verify_checks = False,
        show_hidden = False,
        dm_help = None,
        dm_help_threshold = 700,
        no_category = language["system"]["others_cog"],
        command_attrs = {
            "brief" : language["doc"]["help"]["brief"],
            "help" : language["doc"]["help"]["help"],
            "description" : language["doc"]["help"]["description"]
        }
    )

    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True

    if config["debug"].get("disable_pings", False):
        allowed_mentions = discord.AllowedMentions.none()
    else:
        allowed_mentions = discord.AllowedMentions(everyone=False)

    # The bot
    globvars.client = commands.Bot(
        command_prefix = command_prefix,
        owner_id = int(OWNER_ID),
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
