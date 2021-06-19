"""Contains the time command"""

import datetime
import json
import traceback

import toml
from discord.ext import commands

import botutils
from botc import Phase, check_if_is_player, game_text
from botc.gameloops import (base_day_loop, calculate_base_day_duration,
                            debate_timer, nomination_loop)
from botutils import bot_text
from config import (BASE_DAWN, BASE_NIGHT, DAWN_MULTIPLIER, DEBATE_TIME,
                    INCREMENT, NIGHT_MULTIPLER)
from library import display_time

error_str = bot_text["system"]["error"]

time_night = game_text["gameplay"]["time_night"]
time_dawn = game_text["gameplay"]["time_dawn"]
time_day_base = game_text["gameplay"]["time_day_base"]
time_voting = game_text["gameplay"]["time_voting"]
time_debate = game_text["gameplay"]["time_debate"]
time_nomination = game_text["gameplay"]["time_nomination"]


class Time(commands.Cog, name = game_text["misc"]["townhall_cog"]):
    """BoTC in-game commands cog
    Time command - used for viewing the time left for each different phase or
    stage of the game
    """

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check the channel of the context, return True if it is sent in
        lobby or in spectators chat
        Admins can bypass.
        """
        return  botutils.check_if_admin(ctx) or \
                botutils.check_if_spec(ctx) or \
                check_if_is_player(ctx)

    # ---------- TIME COMMAND ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "time",
        aliases = ["t"],
        hidden = False,
        brief = game_text["doc"]["time"]["brief"],
        help = game_text["doc"]["time"]["help"],
        description = game_text["doc"]["time"]["description"]
    )
    async def time(self, ctx):
        """Time command
        usage: time
        can be used by all players or in DM
        """
        import globvars

        # Day phase
        if globvars.master_state.game.current_phase == Phase.day:

            # Day phase: pre-nomination (base day phase)
            if base_day_loop.is_running():

                start_time = base_day_loop.next_iteration
                total_duration = calculate_base_day_duration(globvars.master_state.game)
                __time_elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).seconds
                time_left = total_duration - __time_elapsed

                msg = time_day_base.format(
                    display_time(total_duration),
                    "is" if time_left == 1 or (time_left >= 60 and time_left < 120) else "are",
                    display_time(time_left)
                )

                await ctx.send(msg)

            # Day phase: nomination loop is running
            elif nomination_loop.is_running():

                # We are in the debate phase
                if debate_timer.is_running():
                    end_time = debate_timer.next_iteration
                    total_duration = DEBATE_TIME
                    time_left = (end_time - datetime.datetime.now(datetime.timezone.utc)).seconds
                    msg = time_debate.format(
                        display_time(total_duration),
                        display_time(time_left)
                    )
                    await ctx.send(msg)

                # We are in the active voting phase
                else:
                    msg = time_voting
                    await ctx.send(msg)

            # Day phase: waiting for a nomination
            else:
                start_time = globvars.master_state.game.nomination_iteration_date[0]
                duration = globvars.master_state.game.nomination_iteration_date[1]
                time_left = duration - (datetime.datetime.now() - start_time).seconds
                msg = time_nomination.format(
                    display_time(duration),
                    display_time(time_left)
                )
                await ctx.send(msg)

        # Night phase
        elif globvars.master_state.game.current_phase == Phase.night:

            min_night_duration = BASE_NIGHT
            max_night_duration = BASE_NIGHT + NIGHT_MULTIPLER * INCREMENT
            __time_elapsed = (datetime.datetime.now() - globvars.master_state.game.night_start_time).seconds
            time_left = max_night_duration - __time_elapsed

            msg = time_night.format(
                display_time(min_night_duration),
                display_time(max_night_duration),
                "is" if time_left == 1 or (time_left >= 60 and time_left < 120) else "are",
                display_time(time_left)
            )

            await ctx.send(msg)

        # Dawn phase
        elif globvars.master_state.game.current_phase == Phase.dawn:

            min_dawn_duration = BASE_DAWN
            max_dawn_duration = BASE_DAWN + DAWN_MULTIPLIER * INCREMENT
            __time_elapsed = (datetime.datetime.now() - globvars.master_state.game.dawn_start_time).seconds
            time_left = max_dawn_duration - __time_elapsed

            msg = time_dawn.format(
                display_time(min_dawn_duration),
                display_time(max_dawn_duration),
                "is" if time_left == 1 or (time_left >= 60 and time_left < 120) else "are",
                display_time(time_left)
            )

            await ctx.send(msg)

    @time.error
    async def time_error(self, ctx, error):
        # Check did not pass -> commands.CheckFailure
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
