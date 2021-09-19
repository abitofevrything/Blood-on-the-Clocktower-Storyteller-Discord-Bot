"""Contains admins only commands"""

import json
import traceback

from discord.ext import commands

import botutils
from botutils import bot_text

user_not_found_str = bot_text["errors"]["user_not_found"]
missing_user_str = bot_text["errors"]["missing_user"]
error_str = bot_text["system"]["error"]


class Admin(commands.Cog, name = bot_text["system"]["admin_cog"]):
    """Admins only commands cog"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    async def cog_command_error(self, ctx, error):
        """Error handling on command"""

        from botc.BOTCUtils import GamemodeNotFound, PlayerNotFound

        # Case: check failure
        if isinstance(error, commands.CheckFailure):
            return

        # Case: bad argument (user not found)
        elif isinstance(error, PlayerNotFound):
            await ctx.send(user_not_found_str.format(ctx.author.mention))
            return

        elif isinstance(error, GamemodeNotFound):
            error = getattr(error, 'original', error)
            await ctx.send(error)
            return
        
        # Case: missing required argument (user not specified)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(missing_user_str.format(ctx.author.mention))
            return

        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
