"""Votestop command"""

from discord.ext import commands
import json
import configparser
import math

from botc import check_if_is_player
from botutils import check_if_lobby, votestop_votes_timer, send_lobby

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    votestop_vote = bot_text["cmd"]["votestop_vote"]

Config = configparser.ConfigParser()
Config.read("preferences.INI")

votestop_time = Config["duration"]["VOTESTOP_CLEAR"]

class Votestop(commands.Cog, name = documentation["misc"]["townhall_cog"]):
    
    def __init__(self, client):
        self.client = client
    
    def cog_check(self, ctx):
        """Check performed on all commands of this cog.
        Must be a non-fleaved player to use these commands.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer

    # ---------- VOTESTOP COMMAND ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "votestop",
        aliases = ["vs"],
        hidden = False,
        brief = documentation["doc"]["votestop"]["brief"],
        help = documentation["doc"]["votestop"]["help"],
        description = documentation["doc"]["votestop"]["description"]
    )
    @commands.check(check_if_lobby)
    async def votestop(self, ctx):
        """Votestop command"""

        import globvars

        if ctx.author.id in globvars.votestop_votes:
            return

        globvars.votestop_votes.append(ctx.author.id)

        votes_needed = math.ceil(len(globvars.master_state.game.player_obj_list) / 2)

        if not votestop_votes_timer.is_running():
            votestop_votes_timer.start()
        
        await send_lobby(votestop_vote.format(ctx.author.mention, votes_needed - len(globvars.votestop_votes), "" if votes_needed - len(globvars.votestop_votes) == 1 else "s"))

        if len(globvars.votestop_votes) >= votes_needed:
            votestop_votes_timer.cancel()

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