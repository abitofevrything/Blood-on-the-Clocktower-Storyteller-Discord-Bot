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
from botutils import bot_text

from ._gameplay import Gameplay

from config import SERVER_ID, NOTIFY_COOLDOWN

error_str = bot_text["system"]["error"]
cooldown_str = bot_text["errors"]["cmd_cooldown"]
already_in_notify = bot_text["errors"]["already_in_notify"]
already_not_notify = bot_text["errors"]["already_not_notify"]
add_notify = bot_text["cmd"]["add_notify"]
remove_notify = bot_text["cmd"]["remove_notify"]


class Notify(Gameplay, name = bot_text["system"]["gameplay_cog"]):
    """Notify command cog"""

    @commands.group(
        pass_context = True,
        name = "notify",
        brief = bot_text["doc"]["notify"]["notify"]["brief"],
        help = bot_text["doc"]["notify"]["notify"]["help"],
        description = bot_text["doc"]["notify"]["notify"]["description"]
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
        brief = bot_text["doc"]["notify"]["add"]["brief"],
        help = bot_text["doc"]["notify"]["add"]["help"],
        description = bot_text["doc"]["notify"]["add"]["description"]
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
        brief = bot_text["doc"]["notify"]["remove"]["brief"],
        help = bot_text["doc"]["notify"]["remove"]["help"],
        description = bot_text["doc"]["notify"]["remove"]["description"]
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
