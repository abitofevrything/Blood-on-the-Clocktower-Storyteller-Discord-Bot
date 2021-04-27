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
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()
            c.execute("""
            CREATE TEMPORARY VIEW IF NOT EXISTS
                winrate_view
            AS
                SELECT
                    user_id,
                    COUNT(*) AS games,
                    COUNT(CASE WHEN alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id) THEN 1 END) AS wins
                FROM
                    game_player
                INNER JOIN
                    game
                ON
                    game.game_id = game_player.game_id
                GROUP BY
                    user_id
            """)
            c.execute("""
            SELECT
                user_id,
                (wins*1.0)/games AS winrate
            FROM
                winrate_view
            WHERE
                games >= ?
                AND wins > 0
            ORDER BY
                winrate DESC
            """, [actual_min_games])

            count = 0
            precision = 1
            for (user_id, winrate) in c.fetchall():
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                assert 0.00 <= winrate <= 1.00, f'invalid winrate for player {user}'

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()
            c.execute("""
            CREATE TEMPORARY VIEW IF NOT EXISTS
                evil_winrate_view
            AS
                SELECT
                    user_id,
                    COUNT(*) AS games,
                    COUNT(CASE WHEN alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id) THEN 1 END) AS wins
                FROM
                    game_player
                INNER JOIN
                    game
                ON
                    game.game_id = game_player.game_id
                WHERE
                    alignment = 'evil'
                GROUP BY
                    user_id
            """)
            c.execute("""
            SELECT
                user_id,
                (wins*1.0)/games AS winrate
            FROM
                evil_winrate_view
            WHERE
                games >= ?
                AND wins > 0
            ORDER BY
                winrate DESC
            """, [actual_min_games])

            count = 0
            precision = 1
            for (user_id, evil_winrate) in c.fetchall():
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                assert 0.00 <= evil_winrate <= 1.00, f'invalid evil winrate for player {user}'

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()

            c.execute("""
            CREATE TEMPORARY VIEW IF NOT EXISTS
                good_winrate_view
            AS
                SELECT
                    user_id,
                    COUNT(*) AS games,
                    COUNT(CASE WHEN alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id) THEN 1 END) AS wins
                FROM
                    game_player
                INNER JOIN
                    game
                ON
                    game.game_id = game_player.game_id
                WHERE
                    alignment = 'good'
                GROUP BY
                    user_id
            """)
            c.execute("""
            SELECT
                user_id,
                (wins*1.0)/games AS winrate
            FROM
                good_winrate_view
            WHERE
                games >= ?
                AND wins > 0
            ORDER BY
                winrate DESC
            """, [actual_min_games])

            count = 0
            precision = 1
            for (user_id, good_winrate) in c.fetchall():
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                assert 0.00 <= good_winrate <= 1.00, f'invalid good winrate for player {user}'

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c.execute("""
            SELECT user_id, COUNT(*) AS games
                FROM game_player
                GROUP BY user_id
                ORDER BY games DESC
            """)

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c.execute("""
            SELECT
                user_id,
                COUNT(*) AS games
            FROM
                game_player
            WHERE
                alignment = 'evil'
            GROUP BY
                user_id
            ORDER BY
                games DESC
            """)

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c.execute("""
            SELECT
                user_id,
                COUNT(*) AS games
            FROM
                game_player
            WHERE
                alignment = 'good'
            GROUP BY
                user_id
            ORDER BY
                games DESC
            """)

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c.execute("""
            SELECT
                user_id,
                COUNT(*) AS wins
            FROM
                game_player
            WHERE
                alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
            GROUP BY
                user_id
            ORDER BY
                wins DESC
            """)

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]

            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c.execute("""
            SELECT
                user_id,
                COUNT(*) AS wins
            FROM
                game_player
            WHERE
                alignment = 'evil'
                AND alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
            GROUP BY
                user_id
            ORDER BY
                wins DESC
            """)

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
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s")

            c.execute("""
            SELECT
                user_id,
                COUNT(*) AS wins
            FROM
                game_player
            WHERE
                alignment = 'good'
                AND alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
            GROUP BY
                user_id
            ORDER BY
                wins DESC
            """)

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
