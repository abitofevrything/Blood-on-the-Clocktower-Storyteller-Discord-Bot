"""Contains the notify command cog"""

import re
import sqlite3
import time
import traceback

from discord import Status
from discord.ext import commands

import botutils
from botc import game_text
from botutils import bot_text
from botutils.emoji import BotEmoji
from config import NOTIFY_COOLDOWN, SERVER_ID
from library import display_time

from ._gameplay import Gameplay

error_str = bot_text["system"]["error"]
no_users_to_notify = bot_text["errors"]["no_users_to_notify"]
already_not_notify = bot_text["errors"]["already_not_notify"]
notify_cooldown = bot_text["errors"]["notify_cooldown"]
add_notify = bot_text["cmd"]["add_notify"]
remove_notify = bot_text["cmd"]["remove_notify"]

notify_map = {}
cooldown_map = {}

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

            if cooldown_map.get(len(globvars.master_state.pregame), 0) > time.time():
                min_next_no_cd_players = 20
                while cooldown_map.get(min_next_no_cd_players, None) is None or cooldown_map[min_next_no_cd_players] < time.time():
                    min_next_no_cd_players -= 1
                
                return await ctx.send(notify_cooldown.format(ctx.author.mention, BotEmoji.x_emoji, display_time(int(cooldown_map[len(globvars.master_state.pregame)] - time.time())), min_next_no_cd_players))

            # Set cooldowns
            for i in range(len(globvars.master_state.pregame), -1, -1):
                if cooldown_map.get(i, None) is None or cooldown_map[i] < time.time():
                    cooldown_map[i] = time.time() + NOTIFY_COOLDOWN

            users_to_ping = []

            with sqlite3.connect("data.sqlite3") as conn:
                c = conn.cursor()

                c.execute("""
                SELECT user_id, min_playercount, cooldown, always_notify
                    FROM notify
                """)

                for user_id, min_playercount, cooldown, always_notify in c.fetchall():
                    member = globvars.client.get_guild(SERVER_ID).get_member(user_id)

                    # Do not ping the person that ran the command
                    notify_map[ctx.author.id] = time.time()

                    if (
                        member and
                        member.id not in globvars.master_state.pregame and
                        len(globvars.master_state.pregame) >= min_playercount and
                        time.time() - notify_map.get(member.id, 0) > cooldown and
                        (always_notify == 1 or member.status != Status.offline) and
                        member.id != ctx.author.id
                    ):
                        notify_map[member.id] = time.time()

                        users_to_ping.append(member.id)

                c.execute("SELECT user_id FROM ignore")
                for user_id, in c.fetchall():
                    if user_id in users_to_ping:
                        users_to_ping.remove(user_id)

            if len(users_to_ping) > 0:
                pings = []
                for user_id in users_to_ping:
                    pings.append(botutils.make_ping(user_id))

                pings = ' '.join(pings)
                msg = f"{ctx.author.mention} {BotEmoji.mention} {pings}"
            else:
                msg = no_users_to_notify.format(ctx.author.mention, BotEmoji.x_emoji)
            await ctx.send(msg)

    @notify.command(
        pass_context = True,
        name = "add",
        aliases = ["+", "true"],
        brief = bot_text["doc"]["notify"]["add"]["brief"],
        help = bot_text["doc"]["notify"]["add"]["help"],
        description = bot_text["doc"]["notify"]["add"]["description"]
    )
    async def add(self, ctx, min_playercount: int = 0, always_notify: bool = False, cooldown: str = '1h'):
        """Add the user to the notify list"""
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            if not re.fullmatch(r"(\d+(hours|h|hour|hrs)|)( *)(\d+(minutes|mins|mins|minute|mn|mns|m|min)|)( *)(\d+(seconds|second|secs|sec|s)|)( *)", cooldown):
                raise commands.BadArgument()
            
            cooldown = ''.join(re.split(' +', cooldown)).lower()
            splits = re.split('(?<=[a-z])(?=\d)', cooldown)

            parsed_cooldown = 0

            for split in splits:
                if re.search(r'(hours|h|hour|hrs)$', split):
                    hrs_parsed = int(re.search(r'\d+', split).group())
                    parsed_cooldown += hrs_parsed * 3600
                elif re.search(r'(minutes|mins|mins|minute|mn|mns|m|min)$', split):
                    mns_parsed = int(re.search(r'\d+', split).group())
                    parsed_cooldown += mns_parsed * 60
                else:
                    scs_parsed = int(re.search(r'\d+', split).group())
                    parsed_cooldown += scs_parsed

            c.execute("INSERT OR REPLACE INTO notify (user_id, min_playercount, always_notify, cooldown) VALUES (:user_id, :min_playercount, :always_notify, :cooldown)", {
                "user_id": ctx.author.id,
                "min_playercount": min_playercount,
                "always_notify": (1 if always_notify else 0),
                "cooldown": parsed_cooldown
            })

        msg = add_notify.format(botutils.BotEmoji.check)
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
    @add.error
    @remove.error
    async def notify_error(self, ctx, error):
        """Error handling of the notify command"""

        # Case: check failure
        if isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.BadArgument):
            msg = game_text["cmd_warnings"]["bad_argument"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))

        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
