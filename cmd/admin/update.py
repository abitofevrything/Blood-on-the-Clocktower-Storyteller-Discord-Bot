"""Contains the update command cog"""

import json
import os
import subprocess
import sys
import traceback

from discord.ext import commands

import botutils
from botutils import bot_text

error_str = bot_text["system"]["error"]

class Update(commands.Cog, name = bot_text["system"]["admin_cog"]):
    """Update command"""

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        return botutils.check_if_admin(ctx)

    # ---------- UPDATE command ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "update",
        hidden = False,
        brief = bot_text["doc"]["update"]["brief"],
        help = bot_text["doc"]["update"]["help"],
        description = bot_text["doc"]["update"]["description"]
    )
    async def update(self, ctx):
        """Update command"""

        p = subprocess.run(["git", "-C", os.path.dirname(sys.argv[0]), "pull", "--stat", "--ff-only"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output = ""
        for line in p.stdout.decode("utf-8").splitlines():
            if len(output + line + "\n") + 6 <= 2000:
                output += f"{line}\n"
            else:
                await ctx.send(f"```{output}```")
                output = ""
        if output:
            await ctx.send(f"```{output}```")

        if p.returncode != 0:
            await ctx.send(bot_text["cmd"]["update_exitcode"].format(p.returncode))
            return

        if b"Already up to date" in p.stdout:
            return

        await botutils.restart_bot(ctx)

    @update.error
    async def update_error(self, ctx, error):
        """Update command error handling"""
        if isinstance(error, commands.CheckFailure):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
