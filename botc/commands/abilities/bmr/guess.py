"""Guess command"""

import json
import traceback

import discord
from discord.ext import commands

import botutils
from botc import (AbilityForbidden, AliveOnlyCommand, BOTCUtils, NotAPlayer,
                  NotDMChannel, NotNight, PlayerParser, RoleCannotUseCommand,
                  RoleConverter, check_if_can_guess, check_if_dm,
                  check_if_is_night, check_if_is_player,
                  check_if_player_really_alive, game_text)
from botutils import BotEmoji, bot_text

error_str = bot_text["system"]["error"]

x_emoji = BotEmoji.x_emoji

class Guess(commands.Cog, name = game_text["misc"]["abilities_cog"]):
    """BoTC in-game commands cog
    Guess command - used by gambler
    """

    def __init__(self, client):
        self.client = client
    
    def cog_check(self, ctx):
        """Check performed on all commands of this cog.
        Must be a non-fleaved player to use these commands.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer

    # ---------------- GUESS COMMAND (Gambler) ---------------
    @commands.command(
        pass_context = True, 
        name = "guess",
        aliases = ["gamble"],
        hidden = False,
        brief = game_text["doc"]["guess"]["brief"],
        help = game_text["doc"]["guess"]["help"],
        description = game_text["doc"]["guess"]["description"]
    )
    @commands.check(check_if_is_night)  # Correct phase -> NotNight
    @commands.check(check_if_dm)  # Correct channel -> NotDMChannel
    @commands.check(check_if_player_really_alive)  # Player alive -> AliveOnlyCommand
    @commands.check(check_if_can_guess)  # Correct character -> RoleCannotUseCommand
    async def guess(self, ctx, *, guess):
        """Guess command
        usage: guess <player> is <character>
        characters: exorcist
        """

        splitters = [' is the ', ' is an ', ' is a ', ' is ']

        for split in splitters:
            split = guess.split(split)
            if len(split) == 2:
                break
        
        if len(split) != 2:
            await ctx.author.send(game_text["cmd_warnings"]["guess_invalid_syntax"].format(ctx.author.mention, x_emoji))
            return

        target_players = await PlayerParser().convert(ctx, split[0])
        target_role = await RoleConverter().convert(ctx, split[1])

        if len(target_players) != 1:
            await ctx.author.send(game_text["cmd_warnings"]["guess_invalid_syntax"].format(ctx.author.mention, x_emoji))
            return

        target_player = target_players[0]

        player = BOTCUtils.get_player_from_id(ctx.author.id)
        await player.role.ego_self.register_guess(player, [(target_player, target_role)])

    @guess.error
    async def guess_error(self, ctx, error):
        emoji = BotEmoji.x_emoji
        # Incorrect character -> RoleCannotUseCommand
        if isinstance(error, RoleCannotUseCommand):
            return
        # If it passed all the checks but raised an error in the character class
        elif isinstance(error, AbilityForbidden):
            error = getattr(error, 'original', error)
            await ctx.send(error)
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
    client.add_cog(Guess(client))
    