"""Help command"""

from discord.ext import commands
import json
from botutils import bot_text

help_str = bot_text["cmd"]["help"]

class Help(commands.DefaultHelpCommand):

    def __init__(self, *args, **kwargs):
        commands.DefaultHelpCommand.__init__(self, *args, **kwargs)

    async def prepare_help_command(self, ctx, command):
        await ctx.send(help_str.format(ctx.author.mention))
        super().prepare_help_command(ctx, command)