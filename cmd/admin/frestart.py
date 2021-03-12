"""Contains the frestart command cog"""

import json
import os
import sys
import traceback

from discord.ext import commands

import botutils
import globvars

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

error_str = language["system"]["error"]


class Frestart(commands.Cog, name = language["system"]["admin_cog"]):
    """Frestart command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- FRESTART command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "frestart",
        hidden = False,
        brief = language["doc"]["frestart"]["frestart"]["brief"],
        help = language["doc"]["frestart"]["frestart"]["help"],
        description = language["doc"]["frestart"]["frestart"]["description"]
    )
    async def frestart(self, ctx, arg=None):
        """Frestart command"""

        if globvars.master_state.game and arg != "--force":
            await ctx.send(language["cmd"]["frestart_confirm"].format(ctx.author.mention, botutils.BotEmoji.x_emoji))
            return

        await ctx.send(language["cmd"]["frestart"].format(ctx.author.mention, botutils.BotEmoji.success))
        os.execl(sys.executable, sys.executable, *sys.argv)

    @frestart.error
    async def frestart_error(self, ctx, error):
        """Frestart command error handling"""
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
