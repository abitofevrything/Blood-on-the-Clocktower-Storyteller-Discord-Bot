"""Contains the frole command cog"""

import json
import traceback

import discord
import toml
from discord.ext import commands

import botutils
from botc import PlayerConverter, PlayerNotFound, RoleConverter, RoleNotFound

from botc import game_text
from config import NO_INVALIDATE

from botutils import bot_text
error_str = bot_text["system"]["error"]

x_emoji = botutils.BotEmoji.x_emoji
check_emoji = botutils.BotEmoji.check


class Frole(commands.Cog, name = game_text["misc"]["debug_cog"]):
    """Frole command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- FROLE command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "frole",
        hidden = False,
        brief = game_text["doc"]["frole"]["brief"],
        help = game_text["doc"]["frole"]["help"],
        description = game_text["doc"]["frole"]["description"]
    )
    async def frole(self, ctx, player: PlayerConverter(), role: RoleConverter()):
        """Frole command"""
        import globvars
        old_role = player.role.true_self
        await player.exec_change_role(role)
        player.role.exec_init_role(globvars.master_state.game.setup)
        if not NO_INVALIDATE:
            globvars.master_state.game.invalidated = True
        try:
            await player.role.ego_self.send_opening_dm_embed(player.user)
        except discord.Forbidden:
            pass
        feedback = game_text["doc"]["frole"]["feedback"]
        await ctx.send(feedback.format(check_emoji, player.game_nametag, old_role, role.emoji, role))

    @frole.error
    async def frole_error(self, ctx, error):
        """Frole command error handling"""
        if isinstance(error, commands.MissingRequiredArgument):
            msg = game_text["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, PlayerNotFound):
            msg = game_text["cmd_warnings"]["player_not_found"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, RoleNotFound):
            msg = game_text["cmd_warnings"]["role_not_found"]
            await ctx.send(msg.format(ctx.author.mention, x_emoji))
        elif isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
