"""Revealroles command"""

import json
from typing import Union
import discord
import traceback

import botutils
import globvars
from botc import BOTCUtils, PlayerNotFound
from botutils import BotEmoji

from discord.ext import commands

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)

with open('botutils/bot_text.json') as json_file:
    language = json.load(json_file)
    error_str = language["system"]["error"]

class RevealRole(commands.Cog, name = documentation["misc"]["debug_cog"]):

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    @commands.command(
        pass_context = True,
        name = "revealrole",
        aliases = ["rr", "revealroles"],
        brief = documentation["doc"]["modkill"]["brief"],
        help = documentation["doc"]["modkill"]["help"],
        description = documentation["doc"]["modkill"]["description"]
    )
    async def reveal_roles(self, ctx, target: str):
        if target == 'all':
            msg = ""
            for player in globvars.master_state.game.sitting_order:
                msg += player.game_nametag + " is the **" + player.role.true_self.name + \
                    (" " + player.role.ego_self.name if player.role.true_self.name != player.role.ego_self.name else "") + "**\n"
        else:
            target = BOTCUtils.get_player_from_string(target)
            if target is None:
                raise PlayerNotFound(f"Player {target} not found")
            msg = target.game_nametag + " is the **" + target.role.true_self.name + \
                    (" " + target.role.ego_self.name if target.role.true_self.name != target.role.ego_self.name else "") + "**"
        await ctx.send(msg)

    @reveal_roles.error
    async def reveal_roles_error(self, ctx, error):
        # Incorrect argument -> commands.BadArgument
        if isinstance(error, commands.BadArgument):
            return
        # Missing argument -> commands.MissingRequiredArgument
        elif isinstance(error, commands.MissingRequiredArgument):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())