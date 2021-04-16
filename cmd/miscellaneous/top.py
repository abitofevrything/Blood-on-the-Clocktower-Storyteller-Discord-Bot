"""Contains the top command cog"""

import configparser
import json
import sqlite3

import discord
from discord.ext import commands

import globvars

from ._miscellaneous import Miscellaneous

Config = configparser.ConfigParser()
Config.read("config.INI")

limit = int(Config["misc"]["TOP_LIMIT"])
min_games = int(Config["misc"]["TOP_WINRATE_MIN_GAMES"])

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

top_games_str = language["cmd"]["top_games"]
top_evil_games_str = language["cmd"]["top_evil_games"]
top_good_games_str = language["cmd"]["top_good_games"]
top_wins_str = language["cmd"]["top_wins"]
top_evil_wins_str = language["cmd"]["top_evil_wins"]
top_good_wins_str = language["cmd"]["top_good_wins"]
top_winrate_str = language["cmd"]["top_winrate"]
top_evil_winrate_str = language["cmd"]["top_evil_winrate"]
top_good_winrate_str = language["cmd"]["top_good_winrate"]
top_footer_str = language["cmd"]["top_footer"]
top_footer_winrate_str = language["cmd"]["top_footer_winrate"]

top_usage_str = language["cmd"]["top_usage"]

class Top(Miscellaneous, name = language["system"]["miscellaneous_cog"]):
    """Top command cog"""

    @commands.group(
        pass_context = True,
        name = "top",
        aliases = [],
        brief = language["doc"]["top"]["brief"],
        help = language["doc"]["top"]["help"],
        description = language["doc"]["top"]["description"]
    )
    async def top(self, ctx):
        """Top command"""

        if ctx.invoked_subcommand is None:
            await ctx.send(top_usage_str)

    @top.command(
        pass_context = True,
        name = "winrate",
        aliases = ["wr"]
    )
    async def top_winrate(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()
            c = db.execute("SELECT user_id, ((wins*1.0)/games) AS winrate FROM playerstats WHERE games >= ? ORDER BY winrate DESC", (actual_min_games,))
            count = 0

            precision = 1
            for (user_id, winrate) in c.fetchall():
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, winrate))

                # If the current and previous wr are not the same but appear the same when truncated,
                # increase the truncation precision so that they will be different
                if count > 0 and not leaderboard[count-1][2] == leaderboard[count][2]:
                    while f"{leaderboard[count-1][2] * 100:.{precision}f}" == f"{leaderboard[count][2] * 100:.{precision}f}":
                        precision += 1

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, winrate) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {winrate * 100:.{precision}f}%\n"
                
            title = top_winrate_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "evilwinrate",
        aliases = ["evilwr", "evil_winrate", "evil_wr"]
    )
    async def top_evil_winrate(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()
            c = db.execute("SELECT user_id, ((evil_wins*1.0)/evil_games) AS winrate FROM playerstats WHERE evil_games >= ? ORDER BY winrate DESC", (actual_min_games,))
            count = 0

            precision = 1
            for (user_id, evil_winrate) in c.fetchall():
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, evil_winrate))

                # If the current and previous wr are not the same but appear the same when truncated,
                # increase the truncation precision so that they will be different
                if count > 0 and not leaderboard[count-1][2] == leaderboard[count][2]:
                    while f"{leaderboard[count-1][2] * 100:.{precision}f}" == f"{leaderboard[count][2] * 100:.{precision}f}":
                        precision += 1

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, evil_winrate) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {evil_winrate * 100:.{precision}f}%\n"
                
            title = top_evil_winrate_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "goodwinrate",
        aliases = ["goodwr", "good_winrate", "good_wr"]
    )
    async def top_good_winrate(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()
            c = db.execute("SELECT user_id, ((good_wins*1.0)/good_games) AS winrate FROM playerstats WHERE good_games >= ? ORDER BY winrate DESC", (actual_min_games,))
            count = 0

            precision = 1
            for (user_id, good_winrate) in c.fetchall():
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, good_winrate))

                # If the current and previous wr are not the same but appear the same when truncated,
                # increase the truncation precision so that they will be different
                if count > 0 and not leaderboard[count-1][2] == leaderboard[count][2]:
                    while f"{leaderboard[count-1][2] * 100:.{precision}f}" == f"{leaderboard[count][2] * 100:.{precision}f}":
                        precision += 1

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, good_winrate) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {good_winrate * 100:.{precision}f}%\n"
                
            title = top_good_winrate_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "games"
    )
    async def top_games(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c = db.execute("SELECT user_id, games FROM playerstats ORDER BY games DESC")

            leaderboard = list()
            count = 0
            for (user_id, games) in c.fetchall():
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, games))

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, games) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {games}\n"

            title = top_games_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "evilgames",
        aliases = ["evil_games"]
    )
    async def top_evil_games(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c = db.execute("SELECT user_id, evil_games FROM playerstats ORDER BY evil_games DESC")

            leaderboard = list()
            count = 0
            for (user_id, evil_games) in c.fetchall():
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, evil_games))

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, evil_games) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {evil_games}\n"

            title = top_evil_games_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "goodgames",
        aliases = ["good_games"]
    )
    async def top_good_games(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c = db.execute("SELECT user_id, good_games FROM playerstats ORDER BY good_games DESC")

            leaderboard = list()
            count = 0
            for (user_id, good_games) in c.fetchall():
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, good_games))

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, good_games) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {good_games}\n"

            title = top_good_games_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "wins"
    )
    async def top_wins(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c = db.execute("SELECT user_id, wins FROM playerstats ORDER BY wins DESC")

            leaderboard = list()
            count = 0
            for (user_id, wins) in c.fetchall():
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, wins))

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, wins) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {wins}\n"

            title = top_wins_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "evilwins",
        aliases = ["evil_wins"]
    )
    async def top_evil_wins(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c = db.execute("SELECT user_id, evil_wins FROM playerstats ORDER BY evil_wins DESC")

            leaderboard = list()
            count = 0
            for (user_id, evil_wins) in c.fetchall():
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, evil_wins))

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, evil_wins) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {evil_wins}\n"

            title = top_evil_wins_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "goodwins",
        aliases = ["good_wins"]
    )
    async def top_good_wins(self, ctx):
        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT SUM(total_games) FROM gamestats")
            total_games, = c.fetchone()
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c = db.execute("SELECT user_id, good_wins FROM playerstats ORDER BY good_wins DESC")

            leaderboard = list()
            count = 0
            for (user_id, good_wins) in c.fetchall():
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                leaderboard.append((count + 1, user, good_wins))

                count += 1
                if count >= limit:
                    break

            msg = ""

            for (i, user, good_wins) in leaderboard:
                msg += f"{i}. **{discord.utils.escape_markdown(user.name)}** - {good_wins}\n"

            title = top_good_wins_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)