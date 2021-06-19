"""Contains the ping command cog"""

import json

from discord.ext import commands

import botutils
from botutils import bot_text

from ._miscellaneous import Miscellaneous

ping_str = bot_text["cmd"]["ping"]


class Ping(Miscellaneous, name = bot_text["system"]["miscellaneous_cog"]):
    """Ping command"""

    @commands.command(
        pass_context = True,
        name = "ping",
        aliases = ["pong"],
        brief = bot_text["doc"]["ping"]["brief"],
        help = bot_text["doc"]["ping"]["help"],
        description = bot_text["doc"]["ping"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def ping(self, ctx):
        """Check the latency."""
        msg = ping_str.format(botutils.BotEmoji.beating_heart, round(self.client.latency, 4))
        await ctx.send(msg)
