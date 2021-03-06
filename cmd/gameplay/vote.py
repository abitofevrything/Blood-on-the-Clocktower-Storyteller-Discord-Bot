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
    gm_not_found_str = language["cmd"]["gm_not_found"]
    not_joined_str = language["cmd"]["not_joined"]
    error_str = language["system"]["error"]

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)

x_emoji = botutils.BotEmoji.cross

class Vote(commands.Cog, name = language["system"]["gameplay_cog"]):
    """Vote command cog"""

    @commands.command(
        pass_context = True,
        name = "vote",
        aliases = ["v"],
        hidden = False,
        brief = language["doc"]["vote"]["brief"],
        help = language["doc"]["vote"]["help"],
        description = language["doc"]["vote"]["description"]
    )
    @commands.check(botutils.check_if_lobby)
    @commands.check(botutils.check_if_not_in_game)
    async def vote(self, ctx, arg: str):
        """Vote command"""

        import globvars

        # Do not vote during game setup
        if globvars.master_state.game:
            return
        
        gm = botutils.get_gamemode_from_str(arg)

        # Bad string passed
        if gm is None:
            await ctx.send(gm_not_found_str.format(x_emoji, ctx.author.mention, arg))
            return

        # Connot vote if not in lobby
        if not globvars.master_state.pregame.is_joined(ctx.author.id):
            await ctx.send(not_joined_str.format(x_emoji, ctx.author.mention))
            return

        globvars.master_state.game_chooser.register_vote(ctx.author.id, gm)

        current_votes = globvars.master_state.game_chooser.votes

        votes_str = '\n'.join([f"{gm.value}: {current_votes[gm]}" for gm in current_votes])

        await ctx.send(vote_str.format(ctx.author.mention, fancy.bold(gm.value), votes_str))

    @vote.error
    async def vote_error(self, ctx, error):
        """Error handling of the vote command"""

        # Case: check failure
        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, commands.MissingRequiredArgument):
            msg = documentation["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))

        elif isinstance(error, commands.BadArgument):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        
        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())