"""choose command"""

import json
import traceback

import discord
from discord.ext import commands

import botutils
from botc import (AbilityForbidden, BOTCUtils, DeadOnlyCommand, NotAPlayer,
                  NotDMChannel, NotNight, PlayerParser, RoleCannotUseCommand,
                  check_if_can_choose, check_if_dm, check_if_is_night,
                  check_if_is_player, check_if_player_apparently_dead,
                  game_text)
from botutils import BotEmoji, bot_text

error_str = bot_text["system"]["error"]

class Choose(commands.Cog, name = game_text["misc"]["abilities_cog"]):
    """BoTC in-game commands cog
    Choose command - used by moonchild
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
        name = "choose",
        hidden = False,
        brief = game_text["doc"]["choose"]["brief"],
        help = game_text["doc"]["choose"]["brief"],
        description = game_text["doc"]["choose"]["description"]
    )
    @commands.check(check_if_dm)  # Correct channel -> NotDMChannel
    @commands.check(check_if_player_apparently_dead)  # Player alive -> AliveOnlyCommand
    @commands.check(check_if_can_choose)  # Correct character -> RoleCannotUseCommand
    async def choose(self, ctx, *, killed: PlayerParser()):
        """Choose command
        usage: choose <player>
        characters: moonchild
        """
        player = BOTCUtils.get_player_from_id(ctx.author.id)
        await player.role.ego_self.register_choose(player, killed)

    @choose.error
    async def choose_error(self, ctx, error):
        emoji = BotEmoji.x_emoji
        # Incorrect character -> RoleCannotUseCommand
        if isinstance(error, RoleCannotUseCommand):
            return
        # If it passed all the checks but raised an error in the character class
        elif isinstance(error, AbilityForbidden):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        elif isinstance(error, commands.BadArgument):
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
        # Incorrect phase -> NotNight
        elif isinstance(error, NotNight):
            try:
                await ctx.author.send(game_text["cmd_warnings"]["night_only"].format(ctx.author.mention, emoji))
            except discord.Forbidden:
                pass
        # Player alive -> DeadOnlyCommand
        elif isinstance(error, DeadOnlyCommand):
            try:
                await ctx.author.send(game_text["cmd_warnings"]["dead_only"].format(ctx.author.mention, emoji))
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
    client.add_cog(Choose(client))
    