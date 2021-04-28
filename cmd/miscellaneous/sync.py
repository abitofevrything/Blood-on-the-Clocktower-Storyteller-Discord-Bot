"""Sync command"""

from discord.ext import commands
import botutils
import json
import traceback

import globvars

with open('botutils/bot_text.json') as json_file:
    language = json.load(json_file)

sync_succesful_string = language["cmd"]["sync_success"]
error_str = language["system"]["error"]

class Sync(commands.Cog, name = language["system"]["miscellaneous_cog"]):
    
    @commands.command(
        name = "sync",
        aliases = [],
        pass_context = True,
        brief = language["doc"]["sync"]["brief"],
        help = language["doc"]["sync"]["help"],
        description = language["doc"]["sync"]["description"],
    )
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def sync(self, ctx):
        """Sync command"""

        # Case 1 : Game end softlock
        if globvars.master_state.game and not globvars.master_state.game.gameloop.is_running():
            from botc.gamemodes.Gamemode import Gamemode
            
            globvars.master_state.game.invalidated = True
            try:
                await botutils.unlock_lobby()
                await botutils.remove_all_alive_dead_roles_after_game()
            except Exception:
                pass

            try:
                if globvars.master_state.game.gamemode == Gamemode.trouble_brewing:
                    globvars.client.unload_extension("botc.commands.abilities.tb")
                elif globvars.master_state.game.gamemode == Gamemode.bad_moon_rising:
                    globvars.client.unload_extension("botc.commands.abilities.bmr")
                elif globvars.master_state.game.gamemode == Gamemode.sects_and_violets:
                    globvars.client.unload_extension("botc.commands.abilities.snv")

                globvars.client.unload_extension("botc.commands.townhall")
                globvars.client.unload_extension("botc.commands.debug")
            except Exception:
                pass
            from botc.gameloops import base_day_loop, nomination_loop

            try:
                # Stop the nomination loop if it is running
                if nomination_loop.is_running():
                    nomination_loop.cancel()
                # Stop the base day loop if it is running
                if base_day_loop.is_running():
                    base_day_loop.cancel()
            except Exception:
                pass
            
            globvars.master_state.game = None
        elif not globvars.master_state.game:
            try:
                await botutils.unlock_lobby()
            except Exception:
                pass


        await ctx.send(sync_succesful_string.format(ctx.author.mention, botutils.BotEmoji.success))
    
    @sync.error
    async def sync_error(self, ctx, error):
        if isinstance(error, commands.Cooldown):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())