"""Contains the deop command cog"""

import json

from discord.ext import commands

import botutils

from ._admin import Admin

from botutils import bot_text


class Deop(Admin, name = bot_text["system"]["admin_cog"]):
    """Deop command"""

    @commands.command(
        pass_context = True,
        name = "deop",
        aliases = ["fdeop"],
        brief = bot_text["doc"]["deop"]["brief"],
        help = bot_text["doc"]["deop"]["help"],
        description = bot_text["doc"]["deop"]["description"]
    )
    async def deop(self, ctx):
        """Remove the admin role from the user"""
        await botutils.remove_admin_role(ctx.author)
        await ctx.send(f"{ctx.author.mention} {botutils.BotEmoji.success}")

