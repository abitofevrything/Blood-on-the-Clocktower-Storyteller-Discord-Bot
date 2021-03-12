"""Serve command"""

import botutils
import discord
import traceback
import json
from discord.ext import commands
from botc import check_if_is_player, check_if_is_night, check_if_dm, RoleCannotUseCommand, \
    check_if_player_really_alive, check_if_can_serve, PlayerParser, AbilityForbidden, \
    NotAPlayer, BOTCUtils, AliveOnlyCommand, NotNight, NotDMChannel
from botutils import BotEmoji

with open('botutils/bot_text.json') as json_file: 
    language = json.load(json_file)

error_str = language["system"]["error"]

with open('botc/game_text.json') as json_file: 
    documentation = json.load(json_file)


class Serve(commands.Cog, name = documentation["misc"]["abilities_cog"]):
    """BoTC in-game commands cog
    Serve command - used by butler
    """
    
    def __init__(self, client):
        self.client = client
    
    def cog_check(self, ctx):
        """Check performed on all commands of this cog.
        Must be a non-fleaved player to use these commands.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer
    
    # ---------- SERVE COMMAND (Butler) ----------------------------------------
    @commands.command(
        pass_context = True, 
        name = "serve",
        hidden = False,
        brief = documentation["doc"]["serve"]["brief"],
        help = documentation["doc"]["serve"]["help"],
        description = documentation["doc"]["serve"]["description"]
    )
    @commands.check(check_if_is_night)  # Correct phase -> NotNight
    @commands.check(check_if_dm)  # Correct channel -> NotDMChannel
    @commands.check(check_if_player_really_alive)  # Player alive -> AliveOnlyCommand
    @commands.check(check_if_can_serve)  # Correct character -> RoleCannotUseCommand
    async def serve(self, ctx, *, master: PlayerParser()):
        """Serve command: 
        usage: serve <player> and <player> and...
        characters: butler
        """
        player = BOTCUtils.get_player_from_id(ctx.author.id)
        await player.role.ego_self.register_serve(player, master)

    @serve.error
    async def serve_error(self, ctx, error):
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
    client.add_cog(Serve(client))
    