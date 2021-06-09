"""Contains the fleave command cog"""

import json

import discord
from discord.ext import commands
from typing import Union

import botutils
import toml
from botutils import lobby_timeout, start_votes_timer

from ._admin import Admin

from botutils import bot_text

fleave_str = bot_text["cmd"]["fleave"]
fleaved_str = bot_text["cmd"]["fleaved"]

from config import SERVER_ID

class Fleave(Admin, name = bot_text["system"]["admin_cog"]):
    """Fleave command"""

    @commands.command(
        pass_context = True,
        name = "fleave",
        brief = bot_text["doc"]["fleave"]["brief"],
        help = bot_text["doc"]["fleave"]["help"],
        description = bot_text["doc"]["fleave"]["description"]
    )
    async def fleave(self, ctx, *members: Union[discord.Member, str]):
        """Force leave command"""

        import globvars

        if members[0] == "all":
            count = len(globvars.master_state.pregame) - 1
            for player in globvars.master_state.pregame:
                fetched_member = globvars.client.get_guild(SERVER_ID).get_member(player)
                await ctx.send(fleave_str.format(
                    (fetched_member.name if fetched_member else player),
                    count
                ))
                if fetched_member:
                    await botutils.remove_alive_role(fetched_member)
                count -= 1
            globvars.master_state.pregame.clear()
            lobby_timeout.cancel()
            if start_votes_timer.is_running():
                start_votes_timer.cancel()
            botutils.update_state_machine()
        elif isinstance(members[0], discord.Member):
            for member in members:
                # The player has joined; make them leave
                if globvars.master_state.pregame.is_joined(member.id):
                    globvars.master_state.pregame.safe_remove_player(member.id)
                    await ctx.send(fleave_str.format(member.name, len(globvars.master_state.pregame)))
                    botutils.update_state_machine()
                    # If you are the last player to leave, then cancel the lobby timeout loop
                    if len(globvars.master_state.pregame) == 0:
                        lobby_timeout.cancel()
                    # If the player has voted to start, then remove the start vote
                    if member.id in globvars.start_votes:
                        globvars.start_votes.remove(member.id)
                    globvars.master_state.game_chooser.remove_vote(member.id)
                    # Cancel the start clear timer if no one has voted to start
                    if len(globvars.start_votes) == 0 and start_votes_timer.is_running():
                        start_votes_timer.cancel()

                # The player has not joined
                else:
                    await ctx.send(fleaved_str.format(ctx.author.mention, member.name))

                await botutils.remove_alive_role(member)
