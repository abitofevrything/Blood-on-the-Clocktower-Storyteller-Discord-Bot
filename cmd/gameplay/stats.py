"""Contains the stats command cog"""

import json
import traceback

import toml
from discord.ext import commands

import botutils
from botutils import bot_text

from ._gameplay import Gameplay

from config import PREFIX

error_str = bot_text["system"]["error"]
no_game = bot_text["cmd"]["no_game"]


class Stats(Gameplay, name = bot_text["system"]["gameplay_cog"]):
    """Stats command cog"""

    @commands.command(
        pass_context = True,
        name = "stats",
        aliases = ["statistics"],
        brief = bot_text["doc"]["stats"]["brief"],
        help = bot_text["doc"]["stats"]["help"],
        description = bot_text["doc"]["stats"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_spec_or_dm_or_admin)
    async def stats(self, ctx):
        """Stats command"""

        import globvars

        # If we are in pregame:
        if globvars.master_state.session == botutils.BotState.pregame:
            await botutils.send_pregame_stats(ctx, globvars.master_state.pregame.list)

        # If we are in game:
        elif globvars.master_state.session == botutils.BotState.game:
            return

        # If we are in empty:
        elif globvars.master_state.session == botutils.BotState.empty:
            await ctx.send(no_game.format(PREFIX))

    @stats.error
    async def stats_error(self, ctx, error):
        """Error handling of the stats command"""

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
