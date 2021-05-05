"""Contains the fday command cog"""

import json
import traceback

from discord.ext import commands

import botutils
from botc import Phase

from botc import game_text

from botutils import bot_text
error_str = bot_text["system"]["error"]


class Fday(commands.Cog, name = game_text["misc"]["debug_cog"]):
    """Fday command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- FDAWN command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "fday",
        hidden = False,
        brief = game_text["doc"]["fday"]["brief"],
        help = game_text["doc"]["fday"]["help"],
        description = game_text["doc"]["fday"]["description"]
    )
    async def fday(self, ctx):
        """Fnight command"""

        import globvars
        if globvars.master_state.game.current_phase == Phase.night or globvars.master_state.game.current_phase == Phase.dawn:

            import botc.switches
            botc.switches.master_proceed_to_day = True
            msg = game_text["doc"]["fday"]["feedback"].format(botutils.BotEmoji.success)

            await ctx.send(msg)

    @fday.error
    async def fday_error(self, ctx, error):
        # Check did not pass -> commands.CheckFailure
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
