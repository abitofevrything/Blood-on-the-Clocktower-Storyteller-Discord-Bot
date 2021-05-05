"""Contains the fstart command cog"""

import json

from discord.ext import commands

import botutils

from ._admin import Admin

from botutils import bot_text

fstart_min = bot_text["errors"]["fstart_min"]
fstart_max = bot_text["errors"]["fstart_max"]


class Fstart(Admin, name = bot_text["system"]["admin_cog"]):
    """Fstart command"""

    @commands.command(
        pass_context = True,
        name = "fstart",
        brief = bot_text["doc"]["fstart"]["brief"],
        help = bot_text["doc"]["fstart"]["help"],
        description = bot_text["doc"]["fstart"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def fstart(self, ctx):
        """Force start command"""

        import globvars

        game = botutils.GameChooser().get_selected_game()

        # Make sure all the players are still in the guild
        globvars.master_state.pregame.remove_left_guild_players()

        if len(globvars.master_state.pregame) < game.MIN_PLAYERS:
            msg = fstart_min.format(
                ctx.author.mention,
                botutils.BotEmoji.x_emoji,
                str(game),
                game.MIN_PLAYERS
            )
            await ctx.send(msg)
            return

        if len(globvars.master_state.pregame) > game.MAX_PLAYERS:
            msg = fstart_max.format(
                ctx.author.mention,
                botutils.BotEmoji.x_emoji,
                str(game),
                game.MAX_PLAYERS
            )
            await ctx.send(msg)
            return

        globvars.master_state.game = game
        await globvars.master_state.game.start_game()
        botutils.update_state_machine()

        # Clear the start votes
        globvars.start_votes.clear()
