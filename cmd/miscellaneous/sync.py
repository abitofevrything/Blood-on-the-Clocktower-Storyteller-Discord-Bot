"""Sync command"""

from discord.ext import commands
import botutils
import toml
import json
import traceback
from library import display_time

import globvars

from config import SERVER_ID, LOBBY_CHANNEL_ID, ALIVE_ROLE_ID, DEAD_ROLE_ID

from botutils import bot_text

sync_succesful_string = bot_text["cmd"]["sync_success"]
error_str = bot_text["system"]["error"]
cooldown = bot_text["errors"]["cmd_cooldown"]

class Sync(commands.Cog, name = bot_text["system"]["miscellaneous_cog"]):
    
    @commands.command(
        name = "sync",
        aliases = [],
        pass_context = True,
        brief = bot_text["doc"]["sync"]["brief"],
        help = bot_text["doc"]["sync"]["help"],
        description = bot_text["doc"]["sync"]["description"],
    )
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def sync(self, ctx):
        """Sync command"""

        # Case 1 : Game softlock
        if globvars.master_state.game and not globvars.master_state.game.gameloop.is_running() and not globvars.master_state.game.working:
            from botc.gamemodes.Gamemode import Gamemode
            
            globvars.master_state.game.invalidated = True
            try:
                await botutils.unlock_lobby()

                alive_role = globvars.client.get_guild(SERVER_ID).get_role(ALIVE_ROLE_ID)
                dead_role = globvars.client.get_guild(SERVER_ID).get_role(DEAD_ROLE_ID)

                for player in alive_role.members:
                    await botutils.remove_alive_role(player)
                for player in dead_role.members:
                    await botutils.remove_dead_role(player)
            except Exception as e:
                print(e)

            try:
                if globvars.master_state.game.gamemode == Gamemode.trouble_brewing:
                    globvars.client.unload_extension("botc.commands.abilities.tb")
                elif globvars.master_state.game.gamemode == Gamemode.bad_moon_rising:
                    globvars.client.unload_extension("botc.commands.abilities.bmr")
                elif globvars.master_state.game.gamemode == Gamemode.sects_and_violets:
                    globvars.client.unload_extension("botc.commands.abilities.snv")

                globvars.client.unload_extension("botc.commands.townhall")
                globvars.client.unload_extension("botc.commands.debug")
            except Exception as e:
                print(e)

            from botc.gameloops import base_day_loop, nomination_loop, master_game_loop

            try:
                # Stop the nomination loop if it is running
                if nomination_loop.is_running():
                    nomination_loop.cancel()
                # Stop the base day loop if it is running
                if base_day_loop.is_running():
                    base_day_loop.cancel()
                
                if master_game_loop.is_running():
                    master_game_loop.cancel()
            except Exception as e:
                print(e)

            try:
                from botc.Game import CONFLICTING_CMDS
                for cmd in CONFLICTING_CMDS:
                    globvars.client.load_extension(cmd)
            except Exception:
                pass
            
            globvars.master_state.game = None

            botutils.update_state_machine()

        elif not globvars.master_state.game:
            try:
                await botutils.unlock_lobby()
                
                dead_role = globvars.client.get_guild(SERVER_ID).get_role(DEAD_ROLE_ID)
                for player in dead_role.members:
                    await botutils.remove_dead_role(player)
            except Exception:
                pass

            try:
                from botc.Game import CONFLICTING_CMDS
                for cmd in CONFLICTING_CMDS:
                    globvars.client.load_extension(cmd)
            except Exception:
                pass
                
            try:
                await botutils.unlock_lobby()
            except Exception:
                pass
            
            botutils.update_state_machine()


        await ctx.send(sync_succesful_string.format(ctx.author.mention, botutils.BotEmoji.success))
    
    @sync.error
    async def sync_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(cooldown.format(ctx.author.mention, botutils.BotEmoji.x_emoji, display_time(int(ctx.command.get_cooldown_retry_after(ctx)))))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())