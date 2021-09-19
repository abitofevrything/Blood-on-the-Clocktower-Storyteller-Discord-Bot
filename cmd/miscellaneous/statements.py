"""assassinate command"""

import json
import traceback

import discord
from discord.ext import commands

import botutils
from botc import (AbilityForbidden, AliveOnlyCommand, BOTCUtils, NotAPlayer,
                  NotDay, NotDMChannel, RoleCannotUseCommand, game_text)
from botutils import BotEmoji, bot_text

error_str = bot_text["system"]["error"]

statements = game_text["doc"]["gossip"]["statements"]

def create_statements_embed():
    embed = discord.Embed(title = "Gossip statements")
    msg = "```"
    for statement in statements:
        msg += statement + "\n"
    msg = msg + "```"
    embed.add_field(name = "**Example statements**", value = msg)
    embed.set_thumbnail(url = "https://imgur.com/uhcVkwz.png")
    embed.set_footer(text="If you want to suggest a new statement to be added, please contact an admin or a dev.")
    return embed

class Statements(commands.Cog, name = game_text["misc"]["abilities_cog"]):
    """BoTC in-game commands cog
    Gossip command - used by gossip
    """
    
    def __init__(self, client):
        self.client = client

    # ---------- ASSASSINATE COMMAND (Assassin) --------------
    @commands.command(
        pass_context = True,
        name = "statements",
        hidden = False
    )
    async def statements(self, ctx):
        """Gossip command
        usage: gossip <statement>
        characters: gossip
        """

        await ctx.send(embed=create_statements_embed())

    @statements.error
    async def statements_error(self, ctx, error):
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
    client.add_cog(Statements(client))
    