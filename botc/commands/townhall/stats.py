"""Stats command"""

import json
import math
import traceback

from discord.ext import commands

import botutils
from botc import Phase, RoleGuide
from library import fancy

from botutils import bot_text

error_str = bot_text["system"]["error"]

from botc import game_text
current_phase = game_text["gameplay"]["current_phase"]
stats_tied = game_text["gameplay"]["stats_tied"]
stats_no_one = game_text["gameplay"]["stats_no_one"]
stats_chopping = game_text["gameplay"]["stats_chopping"]
stats_header = game_text["gameplay"]["stats_header"]
votes_stats = game_text["gameplay"]["votes_stats"]
stats_1 = game_text["gameplay"]["stats_1"]
stats_2 = game_text["gameplay"]["stats_2"]
stats_3 = game_text["gameplay"]["stats_3"]
setup_info = game_text["gameplay"]["setup_info"]


class Stats(commands.Cog, name = game_text["misc"]["townhall_cog"]):
    """BoTC in-game commands cog
    Stats command - used for viewing the game's player statistics
    """

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check the channel of the context, return True if it is sent in either
        lobby, or in spec chat.
        Admins can bypass.
        """
        return botutils.check_if_admin(ctx) or \
               botutils.check_if_lobby(ctx) or \
               botutils.check_if_dm(ctx) or \
               botutils.check_if_spec(ctx)

    # ---------- STATS COMMAND (Stats) ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "stats",
        hidden = False,
        brief = game_text["doc"]["stats"]["brief"],
        help = game_text["doc"]["stats"]["help"],
        description = game_text["doc"]["stats"]["description"]
    )
    async def stats(self, ctx):
        """Stats command
        usage: stats
        can be used by all players, spectators in spec-chat or in DM
        """
        import globvars
        game = globvars.master_state.game
        nb_total_players = len(game.sitting_order)

        # Header information - edition, phase and game title
        msg = ctx.author.mention
        msg += " "
        msg += stats_header.format(game.nb_players, fancy.bold(game.gamemode.value))
        msg += "\n"
        msg += current_phase.format(fancy.bold(game.current_phase.value))
        msg += "\n"

        # Setup information
        role_guide = RoleGuide(nb_total_players)
        nb_townsfolks = role_guide.nb_townsfolks
        nb_outsiders = role_guide.nb_outsiders
        nb_minions = role_guide.nb_minions
        nb_demons = role_guide.nb_demons
        msg += setup_info.format(
            nb_total_players,
            nb_townsfolks,
            "s" if nb_townsfolks != 1 else "",
            nb_outsiders,
            "s" if nb_outsiders != 1 else "",
            nb_minions,
            "s" if nb_minions != 1 else "",
            nb_demons,
            "s" if nb_demons != 1 else ""
        )

        msg += "\n"

        nb_alive_players = len([player for player in game.sitting_order if player.is_apparently_alive()])
        nb_available_votes = len([player for player in game.sitting_order if player.has_vote()])

        # Vote stats
        msg += votes_stats.format(
            total = nb_total_players,
            emoji_total = botutils.BotEmoji.people,
            alive = nb_alive_players,
            emoji_alive = botutils.BotEmoji.alive,
            votes = nb_available_votes,
            emoji_votes = botutils.BotEmoji.votes
        )

        # If the phase is daytime, then include voting information
        if game.current_phase == Phase.day:

            chopping_block = game.chopping_block

            msg += "\n"

            if chopping_block:
                player_about_to_die = chopping_block.player_about_to_die
                nb_votes = chopping_block.nb_votes
                if player_about_to_die:
                    msg += stats_chopping.format(player_about_to_die.game_nametag, nb_votes)
                    msg += " "
                    msg += stats_1.format(nb_votes, nb_votes + 1)
                else:
                    msg += stats_tied.format(nb_votes)
                    msg += " "
                    msg += stats_2.format(nb_votes + 1)
            else:
                msg += stats_no_one
                msg += " "
                msg += stats_3.format(math.ceil(nb_alive_players / 2))

        msg += game.create_sitting_order_stats_string()
        await ctx.send(msg)

    @stats.error
    async def stats_error(self, ctx, error):
        # Check did not pass -> commands.CheckFailure
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())

def setup(client):
    client.add_cog(Stats(client))
