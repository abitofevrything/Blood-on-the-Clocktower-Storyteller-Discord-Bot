"""Contains the vote command cog"""

import json
import traceback

import discord
from discord.ext import commands

import botutils
from botc import game_text
from botutils import bot_text
from library.fancytext import fancy

vote_str = bot_text["cmd"]["vote"]
no_vote_str = bot_text["cmd"]["vote_not_registered"]
error_str = bot_text["system"]["error"]

x_emoji = botutils.BotEmoji.x_emoji

class Votes(commands.Cog, name = bot_text["system"]["gameplay_cog"]):
    """Votes command cog"""

    @commands.command(
        pass_context = True,
        name = "votes",
        hidden = False,
        brief = bot_text["doc"]["votes"]["brief"],
        help = bot_text["doc"]["votes"]["help"],
        description = bot_text["doc"]["votes"]["description"]
    )
    @commands.check(botutils.check_if_lobby)
    @commands.check(botutils.check_if_not_in_game)
    async def vote(self, ctx):
        """Votes command"""

        import globvars

        current_vote = globvars.master_state.game_chooser.get_vote(ctx.author.id)

        current_votes = globvars.master_state.game_chooser.votes

        votes_str = '\n'.join([f"{gm.value}: {current_votes[gm]}" for gm in current_votes])
        if current_vote:
            await ctx.send(vote_str.format(ctx.author.mention, fancy.bold(current_vote.value), votes_str))
        else:
            await ctx.send(no_vote_str.format(ctx.author.mention, votes_str))  


    @vote.error
    async def vote_error(self, ctx, error):
        """Error handling of the vote command"""

        # Case: check failure
        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, commands.MissingRequiredArgument):
            msg = game_text["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        
        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())