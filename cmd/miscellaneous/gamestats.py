"""Contains the gamestats command cog"""

import json
import sqlite3

import discord
from discord.ext import commands

from ._miscellaneous import Miscellaneous

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

gamestats_title_str = language["cmd"]["gamestats_title"]
gamestats_title_players_str = language["cmd"]["gamestats_title_players"]
gamestats_total_games_str = language["cmd"]["gamestats_total_games"]
gamestats_good_wins_str = language["cmd"]["gamestats_good_wins"]
gamestats_evil_wins_str = language["cmd"]["gamestats_evil_wins"]
error_title_str = language["errors"]["error_title"]
gamestats_invalid_str = language["cmd"]["gamestats_invalid"]
gamestats_no_games_str = language["cmd"]["gamestats_no_games"]
gamestats_no_games_players_str = language["cmd"]["gamestats_no_games_players"]


class Gamestats(Miscellaneous, name = language["system"]["miscellaneous_cog"]):
    """Gamestats command cog"""

    @commands.command(
        pass_context = True,
        name = "gamestats",
        brief = language["doc"]["gamestats"]["brief"],
        help = language["doc"]["gamestats"]["help"],
        description = language["doc"]["gamestats"]["description"]
    )
    async def gamestats(self, ctx, players: str = None):
        """Gamestats command"""

        if players:
            if players.lower().endswith("p"):
                players = players[:-1]

            try:
                players = int(players)
            except Exception:
                return await ctx.send(embed=discord.Embed(color=discord.Color.red(), title=error_title_str, description=gamestats_invalid_str))

        with sqlite3.connect("data.sqlite3") as db:
            if players:
                title = gamestats_title_players_str.format(players)

                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game
                WHERE
                    (SELECT COUNT(*) FROM game_player WHERE game.game_id = game_player.game_id) = :players
                """, [players])
                total_games = c.fetchone()[0]

                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game
                WHERE
                    (SELECT COUNT(*) FROM game_player WHERE game.game_id = game_player.game_id) = :players
                    AND winner = 'good'
                """, [players])
                good_wins = c.fetchone()[0]

                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game
                WHERE
                    (SELECT COUNT(*) FROM game_player WHERE game.game_id = game_player.game_id) = :players
                    AND winner = 'evil'
                """, [players])
                evil_wins = c.fetchone()[0]
            else:
                title = gamestats_title_str

                c = db.execute("SELECT COUNT(*) FROM game")
                total_games = c.fetchone()[0]

                c = db.execute("SELECT COUNT(*) FROM game WHERE winner = 'good'")
                good_wins = c.fetchone()[0]

                c = db.execute("SELECT COUNT(*) FROM game WHERE winner = 'evil'")
                evil_wins = c.fetchone()[0]

            good_winrate = good_wins / total_games
            assert 0.00 <= good_winrate <= 1.00, 'invalid good winrate'

            evil_winrate = evil_wins / total_games
            assert 0.00 <= evil_winrate <= 1.00, 'invalid evil winrate'

            if not total_games:
                if players:
                    desc = gamestats_no_games_players_str.format(players)
                else:
                    desc = gamestats_no_games_str
                return await ctx.send(embed=discord.Embed(color=discord.Color.red(), title=error_title_str, description=desc))

            embed = discord.Embed(color=discord.Color.blue(), title=title)
            embed.add_field(name=gamestats_total_games_str, value=str(total_games), inline=True)
            embed.add_field(name=gamestats_good_wins_str, value=f"{good_wins} ({good_winrate * 100:.1f}%)", inline=True)
            embed.add_field(name=gamestats_evil_wins_str, value=f"{evil_wins} ({evil_winrate * 100:.1f}%)", inline=True)
            await ctx.send(embed=embed)
