"""Contains the notify command cog"""

import json
import sqlite3
import time
import traceback

import toml
from discord import Status
from discord.ext import commands

import botutils
from library import display_time

from ._gameplay import Gameplay

with open("config.toml") as fd:
    config = toml.load(fd)

    SERVER_ID = config["ids"]["server_id"]

with open("preferences.toml") as fd:
    preferences = toml.load(fd)

    NOTIFY_COOLDOWN = preferences["duration"]["notify_cooldown"]

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

    error_str = language["system"]["error"]
    cooldown_str = language["errors"]["cmd_cooldown"]
    already_in_notify = language["errors"]["already_in_notify"]
    already_not_notify = language["errors"]["already_not_notify"]
    add_notify = language["cmd"]["add_notify"]
    remove_notify = language["cmd"]["remove_notify"]


class Notify(Gameplay, name = language["system"]["gameplay_cog"]):
    """Notify command cog"""

    @commands.group(
        pass_context = True,
        name = "notify",
        brief = language["doc"]["notify"]["notify"]["brief"],
        help = language["doc"]["notify"]["notify"]["help"],
        description = language["doc"]["notify"]["notify"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    @commands.check(botutils.check_if_not_in_game)
    async def notify(self, ctx):
        """Notify command"""
        if ctx.invoked_subcommand is None:
            import globvars

            delta = time.time() - globvars.last_notify
            if delta < NOTIFY_COOLDOWN:
                await ctx.send(cooldown_str.format(ctx.author.mention, botutils.BotEmoji.x_emoji, display_time(int(NOTIFY_COOLDOWN - delta))))
                return

            if botutils.check_if_lobby(ctx):
                globvars.last_notify = time.time()

            users_to_ping = []

            with sqlite3.connect("data.sqlite3") as conn:
                c = conn.cursor()

                c.execute("SELECT user_id FROM notify")
                for row in c.fetchall():
                    userid = row[0]
                    users_to_ping.append(userid)

                c.execute("SELECT user_id FROM ignore")
                for row in c.fetchall():
                    userid = row[0]
                    if userid in users_to_ping:
                        users_to_ping.remove(userid)

            pings = []

            for userid in users_to_ping:
                member = globvars.client.get_guild(SERVER_ID).get_member(userid)

                # Only ping if in server and not offline, already joined or the user who's calling !notify
                if (member and
                        member.status != Status.offline and
                        member.id not in globvars.master_state.pregame and
                        member.id != ctx.author.id):
                    pings.append(member.mention)

            pings = " ".join(pings)

            msg = f"{ctx.author.mention} {botutils.BotEmoji.mention} {pings}"
            await ctx.send(msg)

    @notify.command(
        pass_context = True,
        name = "add",
        aliases = ["+", "true"],
        brief = language["doc"]["notify"]["add"]["brief"],
        help = language["doc"]["notify"]["add"]["help"],
        description = language["doc"]["notify"]["add"]["description"]
    )
    async def add(self, ctx):
        """Add the user to the notify list"""
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("INSERT OR IGNORE INTO notify (user_id) VALUES (:user_id)", {"user_id": ctx.author.id})

            if c.rowcount:
                msg = add_notify.format(botutils.BotEmoji.check)
            else:
                msg = already_in_notify.format(ctx.author.mention, botutils.BotEmoji.x_emoji)

        await ctx.send(msg)

    @notify.command(
        pass_context = True,
        name = "remove",
        aliases = ["-", "false"],
        brief = language["doc"]["notify"]["remove"]["brief"],
        help = language["doc"]["notify"]["remove"]["help"],
        description = language["doc"]["notify"]["remove"]["description"]
    )
    async def remove(self, ctx):
        """Remove the user from the notify list"""
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("DELETE FROM notify WHERE user_id = :user_id", {"user_id": ctx.author.id})

            if c.rowcount:
                msg = remove_notify.format(botutils.BotEmoji.check)
            else:
                msg = already_not_notify.format(ctx.author.mention, botutils.BotEmoji.x_emoji)

        await ctx.send(msg)

    @notify.error
    async def notify_error(self, ctx, error):
        """Error handling of the notify command"""

        # Case: check failure
        if isinstance(error, commands.CheckFailure):
            return

        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
