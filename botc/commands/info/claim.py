"""Contains the claim command cog"""

import traceback
from typing import Union

import botutils
import discord
import globvars
from botc import (BOTCUtils, PlayerConverter, PlayerNotFound, RoleNotFound,
                  check_if_dm, game_text, NotDMChannel)
from botutils import BotEmoji, bot_text
from config import CLAIM_SHOW_TIME
from discord.ext import commands

error_str = bot_text["system"]["error"]

class Claim(commands.Cog, name = game_text["misc"]["info_cog"]):
    
    def __init__(self, client) -> None:
        self.client = client

        self.notes_command = next(c for c in client.commands if c.name == "notes")
        self.notes_claim_command = next(c for c in self.notes_command.commands if c.name == "claim")
        self.notes_claim_add_command = next(c for c in self.notes_claim_command.commands if c.name == "add")
        self.notes_claim_remove_command = next(c for c in self.notes_claim_command.commands if c.name == "remove")

    @commands.group(
        pass_context = True,
        name = "claim",
        aliases = ["cl", "c", "claims"],
        invoke_without_command = True,
        brief = game_text["doc"]["notes"]["claim"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["help"],
        description = game_text["doc"]["notes"]["claim"]["description"]
    )
    async def claim(self, ctx, player_or_claim = None, claim: str = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if player_or_claim is None:
            # Claims summary
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(invoking_player), make_code=True, delete_after=CLAIM_SHOW_TIME)
            else:
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(), make_code=True, delete_after=CLAIM_SHOW_TIME)
            return
        else:
            await self.notes_claim_command.callback(self, ctx, player_or_claim, claim)

    @claim.command(
        pass_context = True,
        name = "add",
        brief = game_text["doc"]["notes"]["claim"]["add"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["add"]["help"],
        description = game_text["doc"]["notes"]["claim"]["add"]["description"]
    )
    @commands.check(check_if_dm)
    async def claim_add(self, ctx, player_or_claim: str, claim: str = None):
        await self.notes_claim_add_command.callback(self, ctx, player_or_claim, claim)

    @claim.command(
        pass_context = True,
        name = "remove",
        aliases = ["rem", "rm", "clear"],
        brief = game_text["doc"]["notes"]["claim"]["remove"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["remove"]["help"],
        description = game_text["doc"]["notes"]["claim"]["remove"]["description"]
    )
    @commands.check(check_if_dm)
    async def claim_remove(self, ctx, player: PlayerConverter = None):
        await self.notes_claim_remove_command.callback(self, ctx, player)

    @claim.error
    async def claim_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = game_text["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, PlayerNotFound):
            msg = game_text["cmd_warnings"]["player_not_found"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, RoleNotFound):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.BadArgument):
            msg = game_text["cmd_warnings"]["bad_argument"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, NotDMChannel):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())


    # Errors must be handled per-command, not per-group

    @claim_add.error
    async def claim_add_error(self, ctx, error):
        await ctx.command.root_parent.on_error(self, ctx, error)

    @claim_remove.error
    async def claim_remove_error(self, ctx, error):
        await ctx.command.root_parent.on_error(self, ctx, error)
