"""Contains the frestart command cog"""

import json
import os
import sys
import traceback

from discord.ext import commands

import botutils
import globvars
from botutils import bot_text

error_str = bot_text["system"]["error"]


class Frestart(commands.Cog, name = bot_text["system"]["admin_cog"]):
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
        brief = bot_text["doc"]["frestart"]["frestart"]["brief"],
        help = bot_text["doc"]["frestart"]["frestart"]["help"],
        description = bot_text["doc"]["frestart"]["frestart"]["description"]
    )
    async def frestart(self, ctx, arg=None):
        """Frestart command"""
        await botutils.restart_bot(ctx, force=(arg == "--force"))

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
