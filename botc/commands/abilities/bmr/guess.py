"""Guess command"""

import botutils
import discord
import traceback
import json
from discord.ext import commands
from botc import check_if_is_player, check_if_is_night, check_if_dm, RoleCannotUseCommand, \
    check_if_player_really_alive, check_if_can_guess, PlayerParser, AbilityForbidden, \
    NotAPlayer, BOTCUtils, AliveOnlyCommand, NotNight, NotDMChannel, RoleConverter

with open('botutils/bot_text.json') as json_file: 
    language = json.load(json_file)

error_str = language["system"]["error"]

with open('botc/game_text.json') as json_file: 
    documentation = json.load(json_file)
    x_emoji = documentation["cmd_warnings"]["x_emoji"]

class Guess(commands.Cog, name = documentation["misc"]["abilities_cog"]):
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
        hidden = False,
        brief = documentation["doc"]["guess"]["brief"],
        help = documentation["doc"]["guess"]["help"],
        description = documentation["doc"]["guess"]["description"]
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

        print(f"Guess command : arguments are {guess}")

        split = guess.split(' is ')
        if len(split) != 2:
            await ctx.author.send(documentation["cmd_warnings"]["guess_invalid_syntax"].format(ctx.author.mention, x_emoji))
            return

        print(f"Guess command : valid syntax pt 1")

        target_players = await PlayerParser().convert(ctx, split[0])
        target_role = await RoleConverter().convert(ctx, split[1])

        if len(target_players) != 1:
            await ctx.author.send(documentation["cmd_warnings"]["guess_invalid_syntax"].format(ctx.author.mention, x_emoji))
            return

        target_player = target_players[0]

        print(f"Guess command : got {target_player} as {target_role}")

        player = BOTCUtils.get_player_from_id(ctx.author.id)
        await player.role.ego_self.register_guess(player, [(target_player, target_role)])

    @guess.error
    async def guess_error(self, ctx, error):
        emoji = documentation["cmd_warnings"]["x_emoji"]
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
                await ctx.author.send(documentation["cmd_warnings"]["night_only"].format(ctx.author.mention, emoji))
            except discord.Forbidden:
                pass
        # Player not alive -> AliveOnlyCommand
        elif isinstance(error, AliveOnlyCommand):
            try:
                await ctx.author.send(documentation["cmd_warnings"]["alive_only"].format(ctx.author.mention, emoji))
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
    