"""Contains the ignore command cog"""

import json
import sqlite3

import discord
import toml
from discord.ext import commands

import botutils

from ._admin import Admin

with open("config.toml") as fd:
    config = toml.load(fd)

    PREFIX = config["bot"]["prefix"]
    SERVER_ID = config["ids"]["server_id"]

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

    add_ignore = language["cmd"]["add_ignore"]
    remove_ignore = language["cmd"]["remove_ignore"]
    already_ignored = language["cmd"]["already_ignored"]
    not_ignored = language["cmd"]["not_ignored"]
    ignore_list_empty = language["cmd"]["ignore_list_empty"]
    people_total = language["cmd"]["people_total"]
    clear_ignore = language["cmd"]["clear_ignore"]
    force_clear = language["cmd"]["force_clear"]
    ignore_sync = language["cmd"]["ignore_sync"]


class Ignore(Admin, name = language["system"]["admin_cog"]):
    """Ignore command"""

    @commands.group(
        pass_context = True,
        name = "ignore",
        aliases = ["fignore"],
        brief = language["doc"]["ignore"]["ignore"]["brief"],
        help = language["doc"]["ignore"]["ignore"]["help"],
        description = language["doc"]["ignore"]["ignore"]["description"]
    )
    async def ignore(self, ctx):
        """If no subcommand is invoked, display the list of ignored users"""
        if ctx.invoked_subcommand is None:
            import globvars

            with sqlite3.connect("data.sqlite3") as conn:
                c = conn.cursor()

                c.execute("SELECT user_id FROM ignore")
                rows = c.fetchall()
                if rows:
                    msg = people_total.format(len(rows), botutils.BotEmoji.people) + "\n"

                    for row in rows:
                        userid = row[0]
                        user = globvars.client.get_user(userid)

                        msg += f"**{user.name}**#**{user.discriminator}** `({userid})`"
                        msg += ", "

                    # Remove ", " from the end of msg
                    msg = msg[:-2]

                    await ctx.send(msg)
                else:
                    await ctx.send(ignore_list_empty)

    @ignore.command(
        pass_context = True,
        name = "add",
        aliases = ["+"],
        brief = language["doc"]["ignore"]["add"]["brief"],
        help = language["doc"]["ignore"]["add"]["help"],
        description = language["doc"]["ignore"]["add"]["description"]
    )
    async def add(self, ctx, *, member: discord.Member):
        """Add a user into the ignore list"""
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("INSERT OR IGNORE INTO ignore (user_id) VALUES (:user_id)", {"user_id": member.id})

            if c.rowcount:
                msg = add_ignore.format(
                    botutils.BotEmoji.check,
                    member.display_name,
                    member.id
                )
            else:
                msg = already_ignored.format(
                    ctx.author.mention,
                    botutils.BotEmoji.x_emoji,
                    member.display_name,
                    member.id
                )

            await ctx.send(msg)

    @ignore.command(
        pass_context = True,
        name = "remove",
        aliases = ["-"],
        brief = language["doc"]["ignore"]["remove"]["brief"],
        help = language["doc"]["ignore"]["remove"]["help"],
        description = language["doc"]["ignore"]["remove"]["description"]
    )
    async def remove(self, ctx, *, member: discord.Member):
        """Remove a user from the ignore list"""
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("DELETE FROM ignore WHERE user_id = :user_id", {"user_id": member.id})

            if c.rowcount:
                msg = remove_ignore.format(
                    botutils.BotEmoji.check,
                    member.display_name,
                    member.id
                )
            else:
                msg = not_ignored.format(
                    ctx.author.mention,
                    botutils.BotEmoji.x_emoji,
                    member.display_name,
                    member.id
                )

            await ctx.send(msg)

    @ignore.command(
        pass_context = True,
        name = "sync",
        brief = language["doc"]["ignore"]["sync"]["brief"],
        help = language["doc"]["ignore"]["sync"]["help"],
        description = language["doc"]["ignore"]["sync"]["description"]
    )
    async def sync(self, ctx):
        """Remove users that are not in the server"""
        import globvars

        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            count = 0
            guild = globvars.client.get_guild(SERVER_ID)

            c.execute("SELECT user_id FROM ignore")

            for row in c.fetchall():
                userid = row[0]
                if guild.get_member(userid) is None:
                    c.execute("DELETE FROM ignore WHERE user_id = :user_id", {"user_id": userid})
                    count += 1

        msg = ignore_sync.format(botutils.BotEmoji.check, count)
        await ctx.send(msg)

    @ignore.group(
        pass_context = True,
        name = "clear",
        brief = language["doc"]["ignore"]["clear"]["brief"],
        help = language["doc"]["ignore"]["clear"]["help"],
        description = language["doc"]["ignore"]["clear"]["description"]
    )
    async def clear(self, ctx):
        """Clear the ignore list"""
        if ctx.invoked_subcommand is None:
            with sqlite3.connect("data.sqlite3") as conn:
                c = conn.cursor()

                c.execute("SELECT COUNT(*) FROM ignore")
                count = c.fetchone()[0]

                if count:
                    msg = clear_ignore.format(ctx.author.mention, count, PREFIX)
                else:
                    msg = ignore_list_empty

                await ctx.send(msg)

    @clear.command(
        pass_context = True,
        name = "--force",
        brief = language["doc"]["ignore"]["--force"]["brief"],
        help = language["doc"]["ignore"]["--force"]["help"],
        description = language["doc"]["ignore"]["--force"]["description"]
    )
    async def force(self, ctx):
        """Force flag for the clear subcommand"""
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("DELETE FROM ignore")

        msg = force_clear.format(botutils.BotEmoji.check)
        await ctx.send(msg)
