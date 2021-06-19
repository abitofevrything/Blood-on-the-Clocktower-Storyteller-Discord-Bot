"""Stats command"""

import traceback

import discord
from discord.ext import commands

import botutils
from botc import BOTCUtils
from botutils import BotEmoji, bot_text

error_str = bot_text["system"]["error"]

from botc import check_if_is_player, game_text


class GetRole(commands.Cog, name = game_text["misc"]["townhall_cog"]):
    """BoTC in-game commands cog
    Stats command - used for viewing the game's player statistics
    """

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check the channel of the context, return True if it is sent in either
        lobby, or in spec chat.
        Admins can bypass.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer

    # ---------- STATS COMMAND (Stats) ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "getrole",
        hidden = False,
        aliases = ["selfrole", "myrole"],
        brief = game_text["doc"]["getrole"]["brief"],
        help = game_text["doc"]["getrole"]["help"],
        description = game_text["doc"]["getrole"]["description"]
    )
    async def getrole(self, ctx):
        player = BOTCUtils.get_player_from_id(ctx.author.id)

        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.send(game_text["doc"]["getrole"]["feedback"].format(ctx.author.mention, BotEmoji.check))

        await player.role.ego_self.send_opening_dm_embed(player.user)

    @getrole.error
    async def getrole_error(self, ctx, error):
        # Check did not pass -> commands.CheckFailure
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
