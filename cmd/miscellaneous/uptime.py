"""Contains the uptime command cog"""

import json
from datetime import timedelta
from time import time

from discord.ext import commands

import botutils
from botutils import bot_text

from ._miscellaneous import Miscellaneous

uptime_str = bot_text["cmd"]["uptime"]


class Uptime(Miscellaneous, name = bot_text["system"]["miscellaneous_cog"]):
    """Uptime command"""

    @commands.command(
        pass_context = True,
        name = "uptime",
        brief = bot_text["doc"]["uptime"]["brief"],
        help = bot_text["doc"]["uptime"]["help"],
        description = bot_text["doc"]["uptime"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def uptime(self, ctx):
        """Check the uptime."""

        import globvars
        uptime = time() - globvars.master_state.boottime
        uptime = round(uptime)
        uptime_formatted = str(timedelta(seconds=uptime))
        msg = uptime_str.format(botutils.BotEmoji.alarmclock, uptime_formatted)
        await ctx.send(msg)
