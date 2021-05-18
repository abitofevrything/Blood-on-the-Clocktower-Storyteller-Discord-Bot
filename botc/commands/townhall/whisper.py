"""Whisper command cog"""

import time
import traceback

import discord
from discord.ext import commands

import botutils
import globvars
from botc import (BOTCUtils, NotAPlayer, NotDay, NotDMChannel, PlayerConverter,
                  WhisperConverter, WhisperTooLong, check_if_dm,
                  check_if_is_day, check_if_is_player, game_text)
from library import display_time
from botutils import bot_text

from config import WHISPER_COOLDOWN, WHISPER_SHOW_TIME

error_str = bot_text["system"]["error"]
cooldown = bot_text["errors"]["cmd_cooldown"]

recipient_blocked = game_text["cmd_warnings"]["recipient_blocked"]
whisper_announcement = game_text["gameplay"]["whisper_announcement"]
from_str = game_text["gameplay"]["from"]
to_str = game_text["gameplay"]["to"]
whisper_self = game_text["cmd_warnings"]["whisper_self"]


class Whisper(commands.Cog, name = game_text["misc"]["townhall_cog"]):
    """Whisper command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check performed on all commands of this cog.
        Must be a non-fleaved player to use these commands.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer

    # ---------- WHISPER COMMAND ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "whisper",
        aliases = ["w"],
        hidden = False,
        cooldown_after_parsing = True,
        brief = game_text["doc"]["whisper"]["brief"],
        help = game_text["doc"]["whisper"]["help"],
        description = game_text["doc"]["whisper"]["description"]
    )
    @commands.check(check_if_is_day)  # Correct phase -> NotDay
    @commands.check(check_if_dm)  # Correct channel -> NotDMChannel
    async def whisper(self, ctx, recipient: PlayerConverter, *, content: WhisperConverter):
        """Whisper command"""
        if globvars.master_state.game.nomination_iteration_date:
            await ctx.author.send(game_text["cmd_warnings"]["whisper_not_allowed_during_noms"].format(botutils.BotEmoji.x_emoji, ctx.author.mention))
            return

        player = BOTCUtils.get_player_from_id(ctx.author.id)
        # You may not whisper to yourself
        if player.user.id == recipient.user.id:
            msg = whisper_self.format(
                botutils.BotEmoji.x_emoji,
                ctx.author.mention
            )
            try:
                await ctx.author.send(msg)
            except discord.Forbidden:
                pass
            return

        delta = int(time.time()) - globvars.last_whisper[ctx.author.id][recipient.user.id]
        if delta < WHISPER_COOLDOWN:
            await ctx.send(cooldown.format(ctx.author.mention, botutils.BotEmoji.x_emoji, display_time(int(WHISPER_COOLDOWN - delta))))
            return

        try:
            msg = from_str.format(
                botutils.BotEmoji.unread_message,
                player.game_nametag,
                discord.utils.escape_markdown(content)
            )
            await recipient.user.send(msg)
        except discord.Forbidden:
            msg = recipient_blocked.format(botutils.BotEmoji.warning_sign)
            await ctx.send(msg)
        else:
            msg = to_str.format(
                botutils.BotEmoji.whisper,
                recipient.game_nametag,
                discord.utils.escape_markdown(content)
            )
            await ctx.send(msg)
            announcement_msg = whisper_announcement.format(
                botutils.BotEmoji.opened_letter,
                player.game_nametag,
                recipient.game_nametag,
            )
            await botutils.send_lobby(announcement_msg, delete_after = WHISPER_SHOW_TIME)

            globvars.last_whisper[ctx.author.id][recipient.user.id] = int(time.time())

    @whisper.error
    async def whisper_error(self, ctx, error):
        emoji = botutils.BotEmoji.x_emoji
        # Non-registered or quit player -> NotAPlayer
        if isinstance(error, NotAPlayer):
            return
        # Incorrect channel -> NotDMChannel
        elif isinstance(error, NotDMChannel):
            return
        # Command on cooldown -> commands.CommandOnCooldown
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(cooldown.format(ctx.author.mention, emoji, display_time(int(ctx.command.get_cooldown_retry_after(ctx)))))
        # Incorrect argument -> commands.BadArgument
        elif isinstance(error, commands.BadArgument):
            await ctx.send(game_text["cmd_warnings"]["player_not_found"].format(ctx.author.mention, emoji))
        # Incorrect phase -> NotDay
        elif isinstance(error, NotDay):
            await ctx.send(game_text["cmd_warnings"]["day_only"].format(ctx.author.mention, emoji))
        # Missing argument -> commands.MissingRequiredArgument
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(game_text["cmd_warnings"]["whisper_missing_args"].format(ctx.author.mention, emoji))
        # Whisper too long -> WhisperTooLong
        elif isinstance(error, WhisperTooLong):
            await ctx.send(game_text["cmd_warnings"]["whisper_too_long"].format(ctx.author.mention, emoji))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())


def setup(client):
    client.add_cog(Whisper(client))
