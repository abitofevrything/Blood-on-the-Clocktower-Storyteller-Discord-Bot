"""Contains the github command cog"""

import json

from discord.ext import commands

import botutils
from botutils import bot_text

from ._miscellaneous import Miscellaneous

github_str = bot_text["cmd"]["github"]


class Github(Miscellaneous, name = bot_text["system"]["miscellaneous_cog"]):

    @commands.command(
        pass_context = True,
        name = "github",
        aliases = ["git"],
        brief = bot_text["doc"]["github"]["brief"],
        help = bot_text["doc"]["github"]["help"],
        description = bot_text["doc"]["github"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def github(self, ctx):
        await ctx.send(github_str)
