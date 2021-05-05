"""Contains the top command cog"""

import json
import sqlite3
from collections import defaultdict

import discord
import toml
from discord.ext import commands

import globvars

from ._miscellaneous import Miscellaneous

with open("config.toml") as fd:
    config = toml.load(fd)

    limit = config["commands"]["top"]["limit"]
    min_games = config["commands"]["top"]["winrate"]["min_games"]

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

    async def _top_winrate(self, ctx, alignment=None):
        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]
            footer = top_footer_str.format(total_games, "" if total_games == 1 else "s") + " · " + top_footer_winrate_str.format(min(total_games, min_games), "" if total_games == 1 else "s")

            actual_min_games = min(total_games, min_games)

            leaderboard = list()
            c.execute("""
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
                alignment LIKE :alignment
            GROUP BY
                user_id
            """, {
                "alignment": alignment or "%",
            })

            tmp = defaultdict(lambda: {"games": 0, "wins": 0})

            for (user_id, games, wins) in c.fetchall():
                primary_user_id = user_id

                # Check if the current user is an alt
                c.execute("""
                    SELECT
                        primary_user_id
                    FROM
                        player_map
                    WHERE
                        secondary_user_id = :user_id
                """, {
                    "user_id": user_id,
                })
                row = c.fetchone()
                if row:
                    primary_user_id = row[0]

                tmp[primary_user_id]["games"] += games
                tmp[primary_user_id]["wins"] += wins

            count = 0
            precision = 1

            for (user_id, stats) in tmp.items():
                tmp[user_id]["winrate"] = stats["wins"] / stats["games"]

            for (user_id, stats) in sorted(tmp.items(), key=lambda x: -x[1]["winrate"]):
                # Check if user is still in the guild
                user = globvars.client.get_user(user_id)
                if not user:
                    continue

                games = stats["games"]
                wins = stats["wins"]
                winrate = stats["winrate"]

                if games < actual_min_games:
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

            if alignment == "good":
                title = top_good_winrate_str.format(min(limit, len(leaderboard)))
            elif alignment == "evil":
                title = top_evil_winrate_str.format(min(limit, len(leaderboard)))
            else:
                assert alignment is None
                title = top_winrate_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "winrate",
        aliases = ["wr"]
    )
    async def top_winrate(self, ctx):
        await self._top_winrate(ctx)

    @top.command(
        pass_context = True,
        name = "evilwinrate",
        aliases = ["evilwr", "evil_winrate", "evil_wr"]
    )
    async def top_evil_winrate(self, ctx):
        await self._top_winrate(ctx, "evil")

    @top.command(
        pass_context = True,
        name = "goodwinrate",
        aliases = ["goodwr", "good_winrate", "good_wr"]
    )
    async def top_good_winrate(self, ctx):
        await self._top_winrate(ctx, "good")

    async def _top_games(self, ctx, alignment=None):
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
                alignment LIKE :alignment
            GROUP BY
                user_id
            """, {
                "alignment": alignment or "%",
            })

            tmp = defaultdict(int)

            for (user_id, games) in c.fetchall():
                primary_user_id = user_id

                # Check if the current user is an alt
                c.execute("""
                    SELECT
                        primary_user_id
                    FROM
                        player_map
                    WHERE
                        secondary_user_id = :user_id
                """, {
                    "user_id": user_id,
                })
                row = c.fetchone()
                if row:
                    primary_user_id = row[0]

                tmp[primary_user_id] += games

            leaderboard = list()
            count = 0

            for (user_id, games) in sorted(tmp.items(), key=lambda x: -x[1]):
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

            if alignment == "good":
                title = top_good_games_str.format(min(limit, len(leaderboard)))
            elif alignment == "evil":
                title = top_evil_games_str.format(min(limit, len(leaderboard)))
            else:
                assert alignment is None
                title = top_games_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "games"
    )
    async def top_games(self, ctx):
        await self._top_games(ctx)

    @top.command(
        pass_context = True,
        name = "evilgames",
        aliases = ["evil_games"]
    )
    async def top_evil_games(self, ctx):
        await self._top_games(ctx, "evil")

    @top.command(
        pass_context = True,
        name = "goodgames",
        aliases = ["good_games"]
    )
    async def top_good_games(self, ctx):
        await self._top_games(ctx, "good")

    async def _top_wins(self, ctx, alignment=None):
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
                alignment LIKE :alignment
                AND alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
            GROUP BY
                user_id
            """, {
                "alignment": alignment or "%",
            })

            tmp = defaultdict(int)

            for (user_id, wins) in c.fetchall():
                primary_user_id = user_id

                # Check if the current user is an alt
                c.execute("""
                    SELECT
                        primary_user_id
                    FROM
                        player_map
                    WHERE
                        secondary_user_id = :user_id
                """, {
                    "user_id": user_id,
                })
                row = c.fetchone()
                if row:
                    primary_user_id = row[0]

                tmp[primary_user_id] += wins

            leaderboard = list()
            count = 0

            for (user_id, wins) in sorted(tmp.items(), key=lambda x: -x[1]):
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

            if alignment == "good":
                title = top_good_wins_str.format(min(limit, len(leaderboard)))
            elif alignment == "evil":
                title = top_evil_wins_str.format(min(limit, len(leaderboard)))
            else:
                assert alignment is None
                title = top_wins_str.format(min(limit, len(leaderboard)))

            embed = discord.Embed(color=discord.Color.orange(), title=title, description=msg)
            embed.set_footer(text=footer)
            await ctx.send(embed=embed)

    @top.command(
        pass_context = True,
        name = "wins"
    )
    async def top_wins(self, ctx):
        await self._top_wins(ctx)

    @top.command(
        pass_context = True,
        name = "evilwins",
        aliases = ["evil_wins"]
    )
    async def top_evil_wins(self, ctx):
        await self._top_wins(ctx, "evil")

    @top.command(
        pass_context = True,
        name = "goodwins",
        aliases = ["good_wins"]
    )
    async def top_good_wins(self, ctx):
        await self._top_wins(ctx, "good")
