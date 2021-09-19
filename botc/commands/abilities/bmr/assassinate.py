"""assassinate command"""

import json
import traceback

import discord
from discord.ext import commands

import botutils
from botc import (AbilityForbidden, AliveOnlyCommand, BOTCUtils, NotAPlayer,
                  NotDMChannel, NotNight, PlayerParser, RoleCannotUseCommand,
                  check_if_can_assassinate, check_if_dm, check_if_is_night,
                  check_if_is_player, check_if_player_really_alive, game_text)
from botutils import BotEmoji, bot_text

error_str = bot_text["system"]["error"]

class Assassinate(commands.Cog, name = game_text["misc"]["abilities_cog"]):
    """BoTC in-game commands cog
    Assassinate command - used by assassin
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
        name = "assassinate",
        hidden = False,
        brief = game_text["doc"]["assassinate"]["brief"],
        help = game_text["doc"]["assassinate"]["brief"],
        description = game_text["doc"]["assassinate"]["description"]
    )
    @commands.check(check_if_is_night)  # Correct phase -> NotNight
    @commands.check(check_if_dm)  # Correct channel -> NotDMChannel
    @commands.check(check_if_player_really_alive)  # Player alive -> AliveOnlyCommand
    @commands.check(check_if_can_assassinate)  # Correct character -> RoleCannotUseCommand
    async def assassinate(self, ctx, *, killed: PlayerParser()):
        """Assassinate command
        usage: assassinate <player>
        characters: assassin
        """
        player = BOTCUtils.get_player_from_id(ctx.author.id)
        await player.role.ego_self.register_assassinate(player, killed)

    @assassinate.error
    async def assassinate_error(self, ctx, error):
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
    client.add_cog(Assassinate(client))
    