"""Help command"""

import discord
from discord.ext import commands

from botutils import bot_text

help_str = bot_text["cmd"]["help"]

class Help(commands.DefaultHelpCommand):

    def __init__(self, *args, **kwargs):
        commands.DefaultHelpCommand.__init__(self, *args, **kwargs)

    async def prepare_help_command(self, ctx, command):
        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.send(help_str.format(ctx.author.mention))
        await super().prepare_help_command(ctx, command)