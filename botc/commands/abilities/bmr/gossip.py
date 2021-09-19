"""assassinate command"""

import json
import traceback

import discord
from discord.ext import commands

import botutils
from botc import (AbilityForbidden, AliveOnlyCommand, BOTCUtils, NotAPlayer,
                  NotDay, NotDMChannel, RoleCannotUseCommand,
                  check_if_can_gossip, check_if_is_day, check_if_is_player,
                  check_if_lobby, check_if_player_really_alive, game_text)
from botutils import BotEmoji, bot_text

error_str = bot_text["system"]["error"]


class Gossip(commands.Cog, name = game_text["misc"]["abilities_cog"]):
    """BoTC in-game commands cog
    Gossip command - used by gossip
    """
    
    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check performed on all commands of this cog.
        Must be a non-fleaved player to use these commands.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer

    # ---------- ASSASSINATE COMMAND (Assassin) --------------
    @commands.command(
        pass_context = True,
        name = "gossip",
        hidden = False,
        brief = game_text["doc"]["gossip"]["brief"],
        help = game_text["doc"]["gossip"]["brief"],
        description = game_text["doc"]["gossip"]["description"]
    )
    @commands.check(check_if_is_day)
    @commands.check(check_if_lobby)
    @commands.check(check_if_player_really_alive)
    @commands.check(check_if_can_gossip)
    async def gossip(self, ctx, *, statement: str):
        """Gossip command
        usage: gossip <statement>
        characters: gossip
        """
        
        player = BOTCUtils.get_player_from_id(ctx.author.id)
        await player.role.ego_self.register_gossip(player, statement)

    @gossip.error
    async def gossip_error(self, ctx, error):
        emoji = BotEmoji.x_emoji
        # Incorrect character -> RoleCannotUseCommand
        if isinstance(error, RoleCannotUseCommand):
            return
        # If it passed all the checks but raised an error in the character class
        elif isinstance(error, AbilityForbidden):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        elif isinstance(error, commands.BadArgument):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            return
        # Non-registered or quit player -> NotAPlayer
        elif isinstance(error, NotAPlayer):
            return
        # Incorrect channel -> NotDMChannel
        elif isinstance(error, NotDMChannel):
            return
        # Incorrect argument -> commands.BadArgument
        elif isinstance(error, commands.BadArgument):
            return
        # Incorrect phase -> NotDay
        elif isinstance(error, NotDay):
            try:
                await ctx.author.send(game_text["cmd_warnings"]["day_only"].format(ctx.author.mention, emoji))
            except discord.Forbidden:
                pass
        # Player not alive -> AliveOnlyCommand
        elif isinstance(error, AliveOnlyCommand):
            try:
                await ctx.author.send(game_text["cmd_warnings"]["alive_only"].format(ctx.author.mention, emoji))
            except discord.Forbidden:
                pass
        # Missing argument -> commands.MissingRequiredArgument
        elif isinstance(error, commands.MissingRequiredArgument):
            player = BOTCUtils.get_player_from_id(ctx.author.id)
            msg = player.role.ego_self.emoji + " " + player.role.ego_self.instruction + " " + player.role.ego_self.action
            try:
                await ctx.author.send(msg)
            except discord.Forbidden:
                pass
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc()) 
    
def setup(client):
    client.add_cog(Gossip(client))
    