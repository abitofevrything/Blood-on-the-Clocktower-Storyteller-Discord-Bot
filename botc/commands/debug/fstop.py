"""Contains the fstop command cog"""

import json
import traceback

from discord.ext import commands

import botutils

from botc import game_text

from botutils import bot_text
error_str = bot_text["system"]["error"]


class Fstop(commands.Cog, name = game_text["misc"]["debug_cog"]):
    """Fstop command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- FSTOP command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "fstop",
        hidden = False,
        brief = game_text["doc"]["fstop"]["brief"],
        help = game_text["doc"]["fstop"]["help"],
        description = game_text["doc"]["fstop"]["description"]
    )
    async def fstop(self, ctx):
        """Fstop command"""

        from botc.gameloops import base_day_loop, debate_timer, nomination_loop

        # Stop the nomination loop if it is running
        if nomination_loop.is_running():
            nomination_loop.cancel()

        # Stop the base day loop if it is running
        if base_day_loop.is_running():
            base_day_loop.cancel()

        # Stop the debate timer loop if it is running
        if debate_timer.is_running():
            debate_timer.cancel()

        # Stop the gameplay loop if it is running
        import globvars
        if globvars.master_state.game.gameloop.is_running():
            globvars.master_state.game.gameloop.cancel()
            feedback = game_text["doc"]["fstop"]["feedback"]
            await ctx.send(feedback.format(botutils.BotEmoji.check))
        else:
            feedback = game_text["cmd_warnings"]["no_game_running"]
            await ctx.send(feedback.format(ctx.author.mention, botutils.BotEmoji.x_emoji))

    @fstop.error
    async def fstop_error(self, ctx, error):
        """Fstop command error handling"""
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
