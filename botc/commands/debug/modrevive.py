"""Contains the modrevive command cog"""

import json
import random
import traceback

import discord
import toml
from discord.ext import commands

import botutils
import globvars
from botc import (AlreadyAlive, Category, Flags, PlayerConverter,
                  PlayerNotFound, game_text)
from botc.BOTCUtils import BOTCUtils
from botc.gamemodes.troublebrewing import Imp
from botutils import bot_text
from config import DISABLE_DMS

error_str = bot_text["system"]["error"]

x_emoji = botutils.BotEmoji.x_emoji
check_emoji = botutils.BotEmoji.check

class Modrevive(commands.Cog, name = game_text["misc"]["debug_cog"]):
    """Modrevive command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- MODREVIVE command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "modrevive",
        hidden = False,
        brief = game_text["doc"]["modrevive"]["brief"],
        help = game_text["doc"]["modrevive"]["help"],
        description = game_text["doc"]["modrevive"]["description"]
    )
    async def modrevive(self, ctx, *, player: PlayerConverter):
        """Modrevive command"""

        await player.revive(True)
        globvars.master_state.game.invalidated = True
        feedback = game_text["doc"]["modrevive"]["feedback"]
        await ctx.send(feedback.format(check_emoji, player.game_nametag))

    @modrevive.error
    async def modrevive_error(self, ctx, error):
        """modrevive command error handling"""
        if isinstance(error, commands.MissingRequiredArgument):
            msg = game_text["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, PlayerNotFound):
            msg = game_text["cmd_warnings"]["player_not_found"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, AlreadyAlive):
            msg = game_text["cmd_warnings"]["already_alive"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
