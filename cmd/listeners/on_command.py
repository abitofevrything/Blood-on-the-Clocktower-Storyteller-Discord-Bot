"""Contains the on_command event listener"""

import json
import sqlite3

import discord
import toml
from discord.ext import commands

import botutils

with open("preferences.toml") as fd:
    preferences = toml.load(fd)

    IGNORE_THRESHOLD = preferences["duration"]["ignore_threshold"]
    TOKENS_GIVEN = preferences["duration"]["tokens_given"]
    TOKEN_RESET = preferences["duration"]["token_reset"]

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

    ignore = language["system"]["ignore"]


class on_command(commands.Cog):
    """Event listener on_command"""

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """On_command event"""

        import globvars

        # For each command used, we increase the count by one
        if str(ctx.author.id) not in globvars.ratelimit_dict:
            globvars.ratelimit_dict[str(ctx.author.id)] = 1
        else:
            globvars.ratelimit_dict[str(ctx.author.id)] += 1

        # The user has surpassed the threshold, and will be ignored
        if globvars.ratelimit_dict[str(ctx.author.id)] > IGNORE_THRESHOLD:
            with sqlite3.connect("data.sqlite3") as conn:
                c = conn.cursor()

                c.execute("INSERT OR IGNORE INTO ignore (user_id) VALUES (:user_id)", {"user_id": ctx.author.id})

                if c.rowcount:
                    msg = f"{ctx.author.mention} was added to the ignore list for rate limiting."
                    await botutils.log(botutils.Level.warning, msg)
                    await ctx.send(ignore.format(ctx.author.mention, IGNORE_THRESHOLD, TOKEN_RESET))

        if globvars.ratelimit_dict[str(ctx.author.id)] >= TOKENS_GIVEN:
            pass


def setup(client):
    client.add_cog(on_command(client))
