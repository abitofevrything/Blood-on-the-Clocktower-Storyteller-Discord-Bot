"""Contains the playerstats command cog"""

import itertools
import json
import sqlite3
import traceback
from collections import ChainMap
from typing import Union

import discord
from discord.ext import commands

import botutils
from botc.setups import setup

from ._miscellaneous import Miscellaneous

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

with open("botc/game_text.json") as json_file:
    documentation = json.load(json_file)

with open("botc/emojis.json") as json_file:
    emojis = json.load(json_file)

playerstats_title_str = language["cmd"]["playerstats_title"]
playerstats_title_role_str = language["cmd"]["playerstats_title_role"]
playerstats_no_games_str = language["cmd"]["playerstats_no_games"]
playerstats_no_games_role_str = language["cmd"]["playerstats_no_games_role"]
playerstats_games_str = language["cmd"]["playerstats_games"]
playerstats_wins_str = language["cmd"]["playerstats_wins"]
playerstats_winrate_str = language["cmd"]["playerstats_winrate"]
playerstats_good_games_str = language["cmd"]["playerstats_good_games"]
playerstats_good_wins_str = language["cmd"]["playerstats_good_wins"]
playerstats_good_winrate_str = language["cmd"]["playerstats_good_winrate"]
playerstats_evil_games_str = language["cmd"]["playerstats_evil_games"]
playerstats_evil_wins_str = language["cmd"]["playerstats_evil_wins"]
playerstats_evil_winrate_str = language["cmd"]["playerstats_evil_winrate"]
playerstats_footer_str = language["cmd"]["playerstats_footer"]
user_not_found_str = language["errors"]["user_not_found"]
role_not_found_str = documentation["cmd_warnings"]["role_not_found"]
ambiguous_user_str = language["errors"]["ambiguous_user"]
error_str = language["system"]["error"]


class Playerstats(Miscellaneous, name = language["system"]["miscellaneous_cog"]):
    """Playerstats command cog"""

    @commands.command(
        pass_context = True,
        name = "playerstats",
        aliases = ["games", "wins"],
        brief = language["doc"]["playerstats"]["brief"],
        help = language["doc"]["playerstats"]["help"],
        description = language["doc"]["playerstats"]["description"]
    )
    async def playerstats(self, ctx, user_or_role: Union[discord.Member, discord.User, str] = None, role=""):
        """Playerstats command"""

        user = None

        roles = itertools.chain(*setup["botc"]["gamemodes"].values())

        if user_or_role and role:
            try:
                role = next(x for x in roles if role.lower() in x.name.lower()).name
            except StopIteration:
                return await ctx.send(role_not_found_str.format(ctx.author.mention, botutils.BotEmoji.x_emoji))

            try:
                user = botutils.get_member_from_string(str(user_or_role))
            except botutils.AmbiguousUserError as e:
                return await ctx.send(ambiguous_user_str.format(ctx.author.mention, ", ".join(sorted((str(x) for x in e.args[1]), key=str.lower))))
        elif user_or_role:
            if isinstance(user_or_role, str):
                try:
                    user = botutils.get_member_from_string(user_or_role)
                except botutils.AmbiguousUserError as e:
                    return await ctx.send(ambiguous_user_str.format(ctx.author.mention, ", ".join(sorted((str(x) for x in e.args[1]), key=str.lower))))

                if user is None:
                    try:
                        role = next(x for x in roles if user_or_role.lower() in x.name.lower()).name
                    except StopIteration:
                        return await ctx.send(role_not_found_str.format(ctx.author.mention, botutils.BotEmoji.x_emoji))
                    user = ctx.author
            else:
                user = user_or_role
        else:
            user = ctx.author

        if user is None:
            return await ctx.send(user_not_found_str.format(ctx.author.mention))

        with sqlite3.connect("data.sqlite3") as db:
            c = db.execute("SELECT COUNT(*) FROM game")
            total_games = c.fetchone()[0]

            c = db.execute("""
            SELECT
                COUNT(*)
            FROM
                game_player
            WHERE
                user_id = :user_id
                AND role LIKE :role
            """, {
                "user_id": user.id,
                "role": role or "%",
            })
            games = c.fetchone()[0]

            c = db.execute("""
            SELECT
                COUNT(*)
            FROM
                game_player
            WHERE
                user_id = :user_id
                AND role LIKE :role
                AND alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
            """, {
                "user_id": user.id,
                "role": role or "%",
            })
            wins = c.fetchone()[0]

            if not role:
                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game_player
                WHERE
                    user_id = :user_id
                    AND alignment = 'good'
                """, {
                    "user_id": user.id,
                })
                good_games = c.fetchone()[0]

                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game_player
                WHERE
                    user_id = :user_id
                    AND alignment = 'good'
                    AND alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
                """, {
                    "user_id": user.id,
                })
                good_wins = c.fetchone()[0]

                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game_player
                WHERE
                    user_id = :user_id
                    AND alignment = 'evil'
                """, {
                    "user_id": user.id,
                })
                evil_games = c.fetchone()[0]

                c = db.execute("""
                SELECT
                    COUNT(*)
                FROM
                    game_player
                WHERE
                    user_id = :user_id
                    AND alignment = 'good'
                    AND alignment = (SELECT winner FROM game WHERE game.game_id = game_player.game_id)
                """, {
                    "user_id": user.id,
                })
                evil_wins = c.fetchone()[0]

            if role:
                embed = discord.Embed(color=discord.Color.green(), title=playerstats_title_role_str.format(role))
                emoji = botutils.get_emoji(ChainMap(*emojis.values())[role.lower().replace(" ", "")])
                if emoji:
                    embed.set_thumbnail(url=emoji.url)
            else:
                embed = discord.Embed(color=discord.Color.green(), title=playerstats_title_str)
            embed.set_author(name=str(user), icon_url=user.avatar_url)
            embed.set_footer(text=playerstats_footer_str.format(total_games, "" if total_games == 1 else "s"))

            if games > 0:
                winrate = f"{(wins / games) * 100:.1f}%"

                if not role:
                    if good_games > 0:
                        good_winrate = f"{(good_wins / good_games) * 100:.1f}%"
                    else:
                        good_winrate = "N/A"

                    if evil_games > 0:
                        evil_winrate = f"{(evil_wins / evil_games) * 100:.1f}%"
                    else:
                        evil_winrate = "N/A"

                embed.add_field(name=playerstats_games_str, value=str(games), inline=True)
                embed.add_field(name=playerstats_wins_str, value=str(wins), inline=True)
                embed.add_field(name=playerstats_winrate_str, value=str(winrate) + ('' if role else '\n\u200b'), inline=True)
                if not role:
                    embed.add_field(name=playerstats_good_games_str, value=str(good_games), inline=True)
                    embed.add_field(name=playerstats_good_wins_str, value=str(good_wins), inline=True)
                    embed.add_field(name=playerstats_good_winrate_str, value=str(good_winrate) + '\n\u200b', inline=True)
                    embed.add_field(name=playerstats_evil_games_str, value=str(evil_games), inline=True)
                    embed.add_field(name=playerstats_evil_wins_str, value=str(evil_wins), inline=True)
                    embed.add_field(name=playerstats_evil_winrate_str, value=str(evil_winrate), inline=True)
            else:
                if role:
                    embed.description = playerstats_no_games_role_str.format(role)
                else:
                    embed.description = playerstats_no_games_str

            await ctx.send(embed=embed)

    @playerstats.error
    async def playerstats_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.errors.BadUnionArgument):
            await ctx.send(user_not_found_str.format(ctx.author.mention))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
