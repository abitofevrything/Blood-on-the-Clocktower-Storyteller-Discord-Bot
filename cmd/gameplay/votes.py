"""Contains the vote command cog"""

import discord
import json
import botutils
import traceback
from discord.ext import commands
from library.fancytext import fancy

with open('botutils/bot_text.json') as json_file:
    language = json.load(json_file)
    vote_str = language["cmd"]["vote"]
    no_vote_str = language["cmd"]["vote_not_registered"]
    error_str = language["system"]["error"]

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)

x_emoji = botutils.BotEmoji.cross

class Votes(commands.Cog, name = language["system"]["gameplay_cog"]):
    """Votes command cog"""

    @commands.command(
        pass_context = True,
        name = "votes",
        hidden = False,
        brief = language["doc"]["votes"]["brief"],
        help = language["doc"]["votes"]["help"],
        description = language["doc"]["votes"]["description"]
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
            msg = documentation["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        
        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())