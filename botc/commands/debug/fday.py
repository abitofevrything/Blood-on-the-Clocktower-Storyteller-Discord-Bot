"""Contains the fday command cog"""

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


class Fday(commands.Cog, name = documentation["misc"]["debug_cog"]):
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
        brief = documentation["doc"]["fday"]["brief"],
        help = documentation["doc"]["fday"]["help"],
        description = documentation["doc"]["fday"]["description"]
    )
    async def fday(self, ctx):
        """Fnight command"""

        import globvars
        if globvars.master_state.game.current_phase == Phase.night or globvars.master_state.game.current_phase == Phase.dawn:

            import botc.switches
            botc.switches.master_proceed_to_day = True
            msg = documentation["doc"]["fday"]["feedback"].format(botutils.BotEmoji.success)

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
