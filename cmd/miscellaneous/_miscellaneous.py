"""Contains miscellaneous commands"""

import json
import traceback

from discord.ext import commands

import botutils
from botutils import bot_text

error_str = bot_text["system"]["error"]


class Miscellaneous(commands.Cog, name = bot_text["system"]["miscellaneous_cog"]):
    """Miscellaneous commands cog"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_not_ignored(ctx)

    async def cog_command_error(self, ctx, error):
        """Error handling on commands"""

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

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
