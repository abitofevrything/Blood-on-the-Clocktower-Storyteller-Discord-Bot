"""Playtest command cog"""

import toml
from discord.ext import commands

import botutils
from config import PLAYTESTERS

from ._admin import Admin


class Playtest(Admin):
    """Playtest command"""

    # ---------- PLAYTEST COMMAND ----------------------------------------
    @commands.command(pass_context=True, name = "playtest")
    @commands.is_owner()
    async def playtest(self, ctx):
        """Playtest command"""

        import globvars
        playtesters = PLAYTESTERS
        for userid in playtesters:
            globvars.master_state.pregame.safe_add_player(userid)
        globvars.master_state.game = globvars.master_state.game_packs["botc"]["game_obj"]
        await globvars.master_state.game.start_game()
