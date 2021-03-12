"""Contains the notify command cog"""

import botutils
import json
import time
import traceback
import configparser
from ._gameplay import Gameplay
from discord.ext import commands
from discord import Status
from library import display_time

Config = configparser.ConfigParser()
Config.read("config.INI")
SERVER_ID = int(Config["user"]["SERVER_ID"])

Preferences = configparser.ConfigParser()
Preferences.read("preferences.INI")
NOTIFY_COOLDOWN = int(Preferences["duration"]["NOTIFY_COOLDOWN"])

with open('botutils/bot_text.json') as json_file:
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

            pings = []

            users_to_ping = sorted(set(globvars.notify_list) - set(globvars.ignore_list))

            for userid in users_to_ping:
                member = globvars.client.get_guild(SERVER_ID).get_member(userid)

                # member found, only ping them if they are not offline
                if member:
                    if member.status != Status.offline and \
                        member.id not in globvars.master_state.pregame and \
                        member.id != ctx.author.id:
                        pings.append(member.mention)

                # member not present in server, remove their id
                else:
                    globvars.notify_list.remove(userid)

            msg = f"{ctx.author.mention} {botutils.BotEmoji.mention} {' '.join(pings)}"
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

        import globvars
        if ctx.author.id in globvars.notify_list:
            msg = already_in_notify.format(ctx.author.mention, botutils.BotEmoji.x_emoji)
            await ctx.send(msg)
        else:
            globvars.notify_list.append(ctx.author.id)
            msg = add_notify.format(botutils.BotEmoji.check)
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

        import globvars
        if ctx.author.id in globvars.notify_list:
            globvars.notify_list.remove(ctx.author.id)
            msg = remove_notify.format(botutils.BotEmoji.check)
            await ctx.send(msg)
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
