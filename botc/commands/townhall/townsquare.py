"""Townsquare command"""

import json
import traceback

import discord
import toml
from discord.ext import commands

import botutils
from botc import Townsquare as TownsquareImage, game_text
from library import display_time
from botutils import bot_text

from config import TOWNSQUARE_COOLDOWN

error_str = bot_text["system"]["error"]
cooldown = bot_text["errors"]["cmd_cooldown"]

townsquare_loading = game_text["cmd_warnings"]["townsquare_loading"]

class Townsquare(commands.Cog, name = game_text["misc"]["townhall_cog"]):
    """BoTC in-game commands cog
    Townsquare command - used for viewing the townsquare image
    """

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check the channel of the context, return True if it is sent in either
        lobby, or in spec chat.
        Admins can bypass.
        """
        return botutils.check_if_admin(ctx) or \
               botutils.check_if_lobby(ctx) or \
               botutils.check_if_dm(ctx) or \
               botutils.check_if_spec(ctx)

    # ---------- TOWNSQUARE COMMAND (Stats) ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "townsquare",
        aliases = ["ts"],
        hidden = False,
        brief = game_text["doc"]["townsquare"]["brief"],
        help = game_text["doc"]["townsquare"]["help"],
        description = game_text["doc"]["townsquare"]["description"]
    )
    @commands.cooldown(1, TOWNSQUARE_COOLDOWN, commands.BucketType.channel)
    async def townsquare(self, ctx):
        """Townsquare command
        usage: townsquare
        can be used by all players, spectators in spec-chat or in DM
        """
        loading_msg = await ctx.send(townsquare_loading.format(botutils.BotEmoji.loading))
        async with ctx.channel.typing():
            import globvars
            TownsquareImage().create(globvars.master_state.game)
            await ctx.send(file=discord.File('botc/assets/townsquare.png'))
        await loading_msg.delete()

    @townsquare.error
    async def townsquare_error(self, ctx, error):
        emoji = botutils.BotEmoji.x_emoji
        # Check failed -> commands.CheckFailure
        if isinstance(error, commands.CheckFailure):
            return
        # Command on cooldown -> commands.CommandOnCooldown
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(cooldown.format(ctx.author.mention, emoji, display_time(int(ctx.command.get_cooldown_retry_after(ctx)))))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())

def setup(client):
    client.add_cog(Townsquare(client))

