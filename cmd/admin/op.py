"""Contains the op command cog"""

import json

from discord.ext import commands

import botutils

from ._admin import Admin

from botutils import bot_text


class Op(Admin, name = bot_text["system"]["admin_cog"]):
    """Op command"""

    @commands.command(
        pass_context = True,
        name = "op",
        aliases = ["fop"],
        brief = bot_text["doc"]["op"]["brief"],
        help = bot_text["doc"]["op"]["help"],
        description = bot_text["doc"]["op"]["description"]
    )
    async def op(self, ctx):
        """Give the admin role to the user"""
        await botutils.add_admin_role(ctx.author)
        await ctx.send(f"{ctx.author.mention} {botutils.BotEmoji.success}")
