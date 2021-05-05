"""Contains the fdawn command cog"""

import json
import traceback

from discord.ext import commands

import botutils
from botc import Phase

from botc import game_text

from botutils import bot_text
error_str = bot_text["system"]["error"]


class Fdawn(commands.Cog, name = game_text["misc"]["debug_cog"]):
    """Fdawn command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- FDAWN command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "fdawn",
        hidden = False,
        brief = game_text["doc"]["fdawn"]["brief"],
        help = game_text["doc"]["fdawn"]["help"],
        description = game_text["doc"]["fdawn"]["description"]
    )
    async def fdawn(self, ctx):
        """Fnight command"""

        import globvars
        if globvars.master_state.game.current_phase == Phase.night:

            import botc.switches
            botc.switches.master_proceed_to_dawn = True
            msg = game_text["doc"]["fdawn"]["feedback"].format(botutils.BotEmoji.success)

            await ctx.send(msg)

    @fdawn.error
    async def fdawn_error(self, ctx, error):
        # Check did not pass -> commands.CheckFailure
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
