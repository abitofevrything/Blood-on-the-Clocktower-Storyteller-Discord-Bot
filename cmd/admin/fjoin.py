"""Contains the fjoin command cog"""

import json
from typing import Union

import discord
from discord.ext import commands

import botutils
from botutils import lobby_timeout

from ._admin import Admin

from botutils import bot_text

fjoin_str = bot_text["cmd"]["fjoin"]
fjoined_str = bot_text["cmd"]["fjoined"]
fjoin_max = bot_text["errors"]["fjoin_max"]
cant_fjoin_bot = bot_text["errors"]["cant_fjoin_bot"]


class Fjoin(Admin, name = bot_text["system"]["admin_cog"]):
    """Fjoin command"""

    @commands.command(
        pass_context = True,
        name = "fjoin",
        brief = bot_text["doc"]["fjoin"]["brief"],
        help = bot_text["doc"]["fjoin"]["help"],
        description = bot_text["doc"]["fjoin"]["description"]
    )
    async def fjoin(self, ctx, *members: Union[discord.Member, discord.User, str]):
        """Force join command"""

        import globvars

        game = botutils.GameChooser().get_selected_game()

        for member in members:
            if isinstance(member, str):
                member = botutils.get_member_from_string(member)

            # The player is a bot
            if member.bot:
                await ctx.send(cant_fjoin_bot.format(ctx.author.mention))
                return

            # Too many players
            if len(globvars.master_state.pregame) >= game.MAX_PLAYERS:
                msg = fjoin_max.format(
                    ctx.author.mention,
                    botutils.BotEmoji.x_emoji,
                    str(game),
                    game.MAX_PLAYERS
                )
                await ctx.send(msg)
                return

            # The player has already joined
            if globvars.master_state.pregame.is_joined(member.id):
                await ctx.send(fjoined_str.format(ctx.author.mention, member.name))

            # The player has not yet joined. Make them join.
            else:
                globvars.master_state.pregame.safe_add_player(member.id)
                botutils.update_state_machine()
                await ctx.send(fjoin_str.format(member.name, len(globvars.master_state.pregame)))

            # If you are the first player to join the game, then start the lobby timeout loop
            if len(globvars.master_state.pregame) == 1:
                lobby_timeout.start()

            await botutils.add_alive_role(member)
