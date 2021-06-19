"""Contains the coin command cog"""

import json
import random

from discord.ext import commands

import botutils
from botutils import bot_text

from ._miscellaneous import Miscellaneous


class Coin(Miscellaneous, name = bot_text["system"]["miscellaneous_cog"]):
    """Coin command"""

    @commands.command(
        pass_context = True,
        name = "coin",
        brief = bot_text["doc"]["coin"]["brief"],
        help = bot_text["doc"]["coin"]["help"],
        description = bot_text["doc"]["coin"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def coin(self, ctx):
        """Flip a coin."""

        coin_replies = bot_text["doc"]["coin"]["outputs"]
        coin_weights = bot_text["doc"]["coin"]["weights"]
        coin_reply = random.choices(
            coin_replies,
            weights=coin_weights
        )
        coin_reply = coin_reply[0]

        await ctx.send(coin_reply)

