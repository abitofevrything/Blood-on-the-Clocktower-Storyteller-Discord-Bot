"""Contains the info command cog"""

import traceback
from typing import Union

import botutils
import discord
import globvars
from botc import (BOTCUtils, NotDMChannel, PlayerConverter, PlayerNotFound,
                  RoleNotFound, check_if_dm, game_text, NotNight)
from botc.checks import check_if_is_player
from botutils import BotEmoji, bot_text
from config import CLAIM_SHOW_TIME
from discord.ext import commands

error_str = bot_text["system"]["error"]

class Info(commands.Cog, name = game_text["misc"]["info_cog"]):
    
    def __init__(self, client) -> None:
        self.client = client

        self.notes_command = next(c for c in client.commands if c.name == "notes")
        self.notes_info_command = next(c for c in self.notes_command.commands if c.name == "info")
        self.notes_info_add_command = next(c for c in self.notes_info_command.commands if c.name == "add")
        self.notes_info_remove_command = next(c for c in self.notes_info_command.commands if c.name == "remove")

    @commands.group(
        pass_context = True,
        name = "info",
        aliases = ['i'],
        invoke_without_command = True,
        brief = game_text["doc"]["notes"]["info"]["brief"],
        help = game_text["doc"]["notes"]["info"]["help"],
        description = game_text["doc"]["notes"]["info"]["description"]
    )
    @commands.check(check_if_is_player)
    async def info(self, ctx, *, args: str = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if args is None:
            # Claims summary
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(invoking_player), make_code=True, delete_after=CLAIM_SHOW_TIME)
            else:
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(), make_code=True, delete_after=CLAIM_SHOW_TIME)
            return
        else:
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await self.notes_info_command.callback(self, ctx, args=args)

    @info.command(
        pass_context = True,
        name = "add",
        brief = game_text["doc"]["notes"]["info"]["add"]["brief"],
        help = game_text["doc"]["notes"]["info"]["add"]["help"],
        description = game_text["doc"]["notes"]["info"]["add"]["description"]
    )
    @commands.check(check_if_dm)
    async def info_add(self, ctx, *, args: str):
        await self.notes_info_add_command.callback(self, ctx, args=args)

    @info.command(
        pass_context = True,
        name = "remove",
        aliases = ["rem", "rm"],
        brief = game_text["doc"]["notes"]["info"]["remove"]["brief"],
        help = game_text["doc"]["notes"]["info"]["remove"]["help"],
        description = game_text["doc"]["notes"]["info"]["remove"]["description"]
    )
    @commands.check(check_if_dm)
    async def info_remove(self, ctx, n_or_player: Union[int, PlayerConverter] = None, player: PlayerConverter() = None):
        await self.notes_info_remove_command.callback(self, ctx, n_or_player, player)

    @info.error
    async def info_error(self, ctx, error):
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
        elif isinstance(error, BOTCUtils.NotAPlayer):
            return
        elif isinstance(error, commands.BadArgument):
            msg = game_text["cmd_warnings"]["bad_argument"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, NotDMChannel):
            return
        elif isinstance(error, NotNight):
            await ctx.send(game_text["cmd_warnings"]["night_only"].format(ctx.author.mention, BotEmoji.x_emoji))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())

    # Errors must be handled per-command, not per-group

    @info_add.error
    async def info_add_error(self, ctx, error):
        await ctx.command.root_parent.on_error(self, ctx, error)

    @info_remove.error
    async def info_remove_error(self, ctx, error):
        await ctx.command.root_parent.on_error(self, ctx, error)
