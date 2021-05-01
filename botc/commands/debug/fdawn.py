"""Contains the fdawn command cog"""

import json
import traceback

from discord.ext import commands

import botutils
from botc import Phase

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    error_str = bot_text["system"]["error"]


class Fdawn(commands.Cog, name = documentation["misc"]["debug_cog"]):
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
        brief = documentation["doc"]["fdawn"]["brief"],
        help = documentation["doc"]["fdawn"]["help"],
        description = documentation["doc"]["fdawn"]["description"]
    )
    async def fdawn(self, ctx):
        """Fnight command"""

        import globvars
        if globvars.master_state.game.current_phase == Phase.night:

            import botc.switches
            botc.switches.master_proceed_to_dawn = True
            msg = documentation["doc"]["fdawn"]["feedback"].format(botutils.BotEmoji.success)

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
