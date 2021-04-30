"""Contains the modkill command cog"""

import json
import random
import traceback

import discord
import toml
from discord.ext import commands

import botutils
import globvars
from botc import AlreadyDead, Category, PlayerConverter, PlayerNotFound
from botc.BOTCUtils import BOTCUtils
from botc.gamemodes.troublebrewing import Imp

with open("config.toml") as fd:
    config = toml.load(fd)

    DISABLE_DMS = config["debug"].get("disable_dms", False)

with open("botc/game_text.json") as json_file:
    documentation = json.load(json_file)

with open("botutils/bot_text.json") as json_file:
    bot_text = json.load(json_file)

    error_str = bot_text["system"]["error"]

x_emoji = botutils.BotEmoji.x_emoji
check_emoji = botutils.BotEmoji.check


class Modkill(commands.Cog, name = documentation["misc"]["debug_cog"]):
    """Modkill command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- MODKILL command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "modkill",
        hidden = False,
        brief = documentation["doc"]["modkill"]["brief"],
        help = documentation["doc"]["modkill"]["help"],
        description = documentation["doc"]["modkill"]["description"]
    )
    async def modkill(self, ctx, *, player: PlayerConverter):
        """Modkill command"""
        if player.role.social_self.category == Category.demon:
            if player.is_alive():
                # If 5 or more players alive (not counting travelers), scarlet woman gets
                # promoted to demonhood
                if globvars.master_state.game.nb_alive_players >= 5:

                    from botc.gamemodes.troublebrewing import ScarletWoman

                    # This list of scarletwomen could contain dead players
                    scarletwomen = BOTCUtils.get_players_from_role_name(ScarletWoman()._role_enum)

                    if scarletwomen:
                        # We only want the alive, and not poisoned scarlet women
                        alive_scarletwomen = [player for player in scarletwomen if player.is_alive() and not player.is_droisoned()]
                        if alive_scarletwomen:
                            promoted = random.choice(alive_scarletwomen)
                            promoted._old_role_obj = promoted._role_obj
                            await promoted.exec_change_role(Imp())

                            if not DISABLE_DMS:
                                embed = Imp._make_demonhood_promo_embed(Imp(), promoted)
                                try:
                                    await promoted.user.send(embed = embed)
                                except discord.Forbidden:
                                    pass

        await player.exec_real_death()
        player.ghost_vote = 0
        globvars.master_state.game.invalidated = True
        feedback = documentation["doc"]["modkill"]["feedback"]
        await ctx.send(feedback.format(check_emoji, player.game_nametag))

    @modkill.error
    async def modkill_error(self, ctx, error):
        """Modkill command error handling"""
        if isinstance(error, commands.MissingRequiredArgument):
            msg = documentation["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, PlayerNotFound):
            msg = documentation["cmd_warnings"]["player_not_found"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, AlreadyDead):
            msg = documentation["cmd_warnings"]["already_dead"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
