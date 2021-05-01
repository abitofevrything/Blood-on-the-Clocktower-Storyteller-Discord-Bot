"""Contains the streak command cog"""

import itertools
import json
import sqlite3
import traceback
from collections import ChainMap
from typing import Union
from library import display_time
import toml

import discord
from discord.ext import commands

import botutils
from botc.setups import setup

from ._miscellaneous import Miscellaneous

with open("preferences.toml") as fd:
    preferences = toml.load(fd)

    STREAK_COOLDOWN = preferences["duration"]["streak_cooldown"]

with open("botutils/bot_text.json") as json_file:
    language = json.load(json_file)

with open("botc/game_text.json") as json_file:
    documentation = json.load(json_file)
    user_not_found_str = language["errors"]["user_not_found"]
    role_not_found_str = documentation["cmd_warnings"]["role_not_found"]
    ambiguous_user_str = language["errors"]["ambiguous_user"]
    error_str = language["system"]["error"]

    playerstats_footer_str = language["cmd"]["playerstats_footer"]
    playerstats_no_games_str = language["cmd"]["playerstats_no_games"]
    playerstats_no_games_role_str = language["cmd"]["playerstats_no_games_role"]

    streak_title = language["cmd"]["streak_title"]
    streak_title_as = language["cmd"]["streak_title_as"]

    good_games_streak_str = language["cmd"]["good_games_streak"]
    evil_games_streak_str = language["cmd"]["evil_games_streak"]
    good_wins_streak_str = language["cmd"]["good_wins_streak"]
    evil_wins_streak_str = language["cmd"]["evil_wins_streak"]
    good_loss_streak_str = language["cmd"]["good_loss_streak"]
    evil_loss_streak_str = language["cmd"]["evil_loss_streak"]

    game_streak_str = language["cmd"]["game_streak"]
    win_streak_str = language["cmd"]["win_streak"]
    loss_streak_str = language["cmd"]["loss_streak"]

    cooldown = language["errors"]["cmd_cooldown"]

with open("botc/emojis.json") as json_file:
    emojis = json.load(json_file)

class Streak(Miscellaneous, name = language["system"]["miscellaneous_cog"]):
    """Streak command cog"""

    @commands.command(
        pass_context = True,
        name = "streak",
        aliases = ["streaks", "winstreak"],
        brief = language["doc"]["streak"]["brief"],
        help = language["doc"]["streak"]["help"],
        description = language["doc"]["streak"]["description"]
    )
    @commands.cooldown(1, STREAK_COOLDOWN, commands.BucketType.member)
    async def streak(self, ctx, user_or_role: Union[discord.Member, discord.User, str] = None, role=""):
        """Streak command"""

        async with ctx.channel.typing():

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

                c = db.execute("SELECT COUNT(*) FROM game_player WHERE :user_id LIKE user_id AND role LIKE :role", {
                    "user_id": user.id,
                    "role": role or '%'
                })
                user_games = c.fetchone()[0]

                if user_games > 0:
                    if not role:
                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, alignment
                                FROM game_player GP
                                WHERE :user_id IN (
                                    SELECT user_id
                                    FROM game_player G
                                    WHERE G.game_id == GP.game_id
                                )
                                GROUP BY game_id
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT game_id, alignment, (
                                    SELECT COUNT(*) FROM player_games G
                                    WHERE G.alignment <> GR.alignment
                                    AND G.game_id <= GR.game_id
                                ) AS run_group
                                FROM player_games GR
                            ),
                            streak_total AS (
                                SELECT alignment, COUNT(*) AS streak
                                FROM run_groups
                                WHERE alignment = 'good'
                                GROUP BY run_group
                            )
                            SELECT MAX(streak) AS biggest_streak
                            FROM streak_total
                        """, {
                            "user_id" : user.id
                        })
                        good_game_streak = c.fetchone()[0]

                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, alignment
                                FROM game_player GP
                                WHERE :user_id IN (
                                    SELECT user_id
                                    FROM game_player G
                                    WHERE G.game_id == GP.game_id
                                )
                                GROUP BY game_id
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT game_id, alignment, (
                                    SELECT COUNT(*) FROM player_games G
                                    WHERE G.alignment <> GR.alignment
                                    AND G.game_id <= GR.game_id
                                ) AS run_group
                                FROM player_games GR
                            ),
                            streak_total AS (
                                SELECT alignment, COUNT(*) AS streak
                                FROM run_groups
                                WHERE alignment = 'evil'
                                GROUP BY run_group
                            )
                            SELECT MAX(streak) AS biggest_streak
                            FROM streak_total
                        """, {
                            "user_id" : user.id
                        })
                        evil_game_streak = c.fetchone()[0]

                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, game_player.alignment = (
                                    SELECT winner
                                    FROM game
                                    WHERE game.game_id = game_player.game_id
                                ) AS won
                                FROM game_player
                                WHERE user_id = :user_id AND alignment LIKE 'good'
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT won, (
                                    SELECT COUNT(*)
                                    FROM player_games PG
                                    WHERE PG.won <> PGR.won
                                    AND PG.game_id <= PGR.game_id
                                ) AS run_group
                                FROM player_games PGR
                            ),
                            streak_total AS (
                                SELECT COUNT(*) AS streak
                                FROM run_groups
                                WHERE won = 1
                                GROUP BY run_group, won 
                            )
                            SELECT MAX(streak) AS biggest_streak FROM streak_total
                        """, {
                            "user_id" : user.id
                        })
                        good_win_streak = c.fetchone()[0]

                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, game_player.alignment = (
                                    SELECT winner
                                    FROM game
                                    WHERE game.game_id = game_player.game_id
                                ) AS won
                                FROM game_player
                                WHERE user_id = :user_id AND alignment LIKE 'evil'
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT won, (
                                    SELECT COUNT(*)
                                    FROM player_games PG
                                    WHERE PG.won <> PGR.won
                                    AND PG.game_id <= PGR.game_id
                                ) AS run_group
                                FROM player_games PGR
                            ),
                            streak_total AS (
                                SELECT COUNT(*) AS streak
                                FROM run_groups
                                WHERE won = 1
                                GROUP BY run_group, won 
                            )
                            SELECT MAX(streak) AS biggest_streak FROM streak_total
                        """, {
                            "user_id" : user.id
                        })
                        evil_win_streak = c.fetchone()[0]

                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, game_player.alignment = (
                                    SELECT winner
                                    FROM game
                                    WHERE game.game_id = game_player.game_id
                                ) AS won
                                FROM game_player
                                WHERE user_id = :user_id AND alignment LIKE 'good'
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT won, (
                                    SELECT COUNT(*)
                                    FROM player_games PG
                                    WHERE PG.won <> PGR.won
                                    AND PG.game_id <= PGR.game_id
                                ) AS run_group
                                FROM player_games PGR
                            ),
                            streak_total AS (
                                SELECT COUNT(*) AS streak
                                FROM run_groups
                                WHERE won = 0
                                GROUP BY run_group, won 
                            )
                            SELECT MAX(streak) AS biggest_streak FROM streak_total
                        """, {
                            "user_id" : user.id
                        })
                        good_loss_streak = c.fetchone()[0]

                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, game_player.alignment = (
                                    SELECT winner
                                    FROM game
                                    WHERE game.game_id = game_player.game_id
                                ) AS won
                                FROM game_player
                                WHERE user_id = :user_id AND alignment LIKE 'evil'
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT won, (
                                    SELECT COUNT(*)
                                    FROM player_games PG
                                    WHERE PG.won <> PGR.won
                                    AND PG.game_id <= PGR.game_id
                                ) AS run_group
                                FROM player_games PGR
                            ),
                            streak_total AS (
                                SELECT COUNT(*) AS streak
                                FROM run_groups
                                WHERE won = 0
                                GROUP BY run_group, won 
                            )
                            SELECT MAX(streak) AS biggest_streak FROM streak_total
                        """, {
                            "user_id" : user.id
                        })
                        evil_loss_streak = c.fetchone()[0]


                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, CASE WHEN :user_id IN (
                                    SELECT user_id
                                    FROM game_player G
                                    WHERE G.game_id == GP.game_id
                                ) THEN 1 ELSE 0 END AS played
                                FROM game_player GP
                                GROUP BY game_id
                            ),
                            run_groups AS (
                                SELECT game_id, played, (
                                    SELECT COUNT(*) FROM player_games G
                                    WHERE G.played <> GR.played
                                    AND G.game_id <= GR.game_id
                                ) AS run_group
                                FROM player_games GR
                            ),
                            streak_total AS (
                                SELECT played, COUNT(*) AS streak
                                FROM run_groups
                                WHERE played = 1
                                GROUP BY run_group
                            )
                            SELECT MAX(streak) AS biggest_streak
                            FROM streak_total
                            GROUP BY played
                        """, {
                            "user_id" : user.id
                        })
                        game_streak = c.fetchone()[0]

                    else:
                        c = db.execute("""
                            WITH player_games AS (
                                SELECT game_id, role
                                FROM game_player GP
                                WHERE :user_id IN (
                                    SELECT user_id
                                    FROM game_player G
                                    WHERE G.game_id == GP.game_id
                                )
                                GROUP BY game_id
                                ORDER BY game_id
                            ),
                            run_groups AS (
                                SELECT game_id, role, (
                                    SELECT COUNT(*) FROM player_games G
                                    WHERE G.role <> GR.role
                                    AND G.game_id <= GR.game_id
                                ) AS run_group
                                FROM player_games GR
                            ),
                            streak_total AS (
                                SELECT role, COUNT(*) AS streak
                                FROM run_groups
                                WHERE role = :role
                                GROUP BY run_group
                            )
                            SELECT MAX(streak) AS biggest_streak
                            FROM streak_total
                        """, {
                            "user_id" : user.id,
                            "role" : role
                        })
                        game_streak = c.fetchone()[0]


                    c = db.execute("""
                        WITH player_games AS (
                            SELECT game_id, game_player.alignment = (
                                SELECT winner
                                FROM game
                                WHERE game.game_id = game_player.game_id
                            ) AS won
                            FROM game_player
                            WHERE user_id = :user_id AND role LIKE :role
                            ORDER BY game_id
                        ),
                        run_groups AS (
                            SELECT won, (
                                SELECT COUNT(*)
                                FROM player_games PG
                                WHERE PG.won <> PGR.won
                                AND PG.game_id <= PGR.game_id
                            ) AS run_group
                            FROM player_games PGR
                        ),
                        streak_total AS (
                            SELECT COUNT(*) AS streak
                            FROM run_groups
                            WHERE won = 1
                            GROUP BY run_group, won 
                        )
                        SELECT MAX(streak) AS biggest_streak FROM streak_total
                    """, {
                        "user_id" : user.id,
                        "role" : role or "%"
                    })
                    win_streak = c.fetchone()[0]

                    c = db.execute("""
                        WITH player_games AS (
                            SELECT game_id, game_player.alignment = (
                                SELECT winner
                                FROM game
                                WHERE game.game_id = game_player.game_id
                            ) AS won
                            FROM game_player
                            WHERE user_id = :user_id AND role LIKE :role
                            ORDER BY game_id
                        ),
                        run_groups AS (
                            SELECT won, (
                                SELECT COUNT(*)
                                FROM player_games PG
                                WHERE PG.won <> PGR.won
                                AND PG.game_id <= PGR.game_id
                            ) AS run_group
                            FROM player_games PGR
                        ),
                        streak_total AS (
                            SELECT COUNT(*) AS streak
                            FROM run_groups
                            WHERE won = 0
                            GROUP BY run_group, won 
                        )
                        SELECT MAX(streak) AS biggest_streak FROM streak_total
                    """, {
                        "user_id" : user.id,
                        "role" : role or "%"
                    })
                    loss_streak = c.fetchone()[0]

                if role:
                    embed = discord.Embed(color=discord.Color.green(), title=streak_title_as.format(role))
                    emoji = botutils.get_emoji(ChainMap(*emojis.values())[role.lower().replace(" ", "")])
                    if emoji:
                        embed.set_thumbnail(url=emoji.url)
                else:
                    embed = discord.Embed(color=discord.Color.green(), title=streak_title)
                embed.set_author(name=str(user), icon_url=user.avatar_url)
                embed.set_footer(text=playerstats_footer_str.format(total_games, "" if total_games == 1 else "s"))

                if user_games > 0:

                    embed.add_field(name=game_streak_str, value=str(game_streak), inline=True)
                    embed.add_field(name=win_streak_str, value=str(win_streak), inline=True)
                    embed.add_field(name=loss_streak_str, value=str(loss_streak) + '\n\u200b', inline=True)

                    if not role:
                        embed.add_field(name=good_games_streak_str, value=str(good_game_streak), inline=True)
                        embed.add_field(name=good_wins_streak_str, value=str(good_win_streak), inline=True)
                        embed.add_field(name=good_loss_streak_str, value=str(good_loss_streak) + '\n\u200b', inline=True)

                        embed.add_field(name=evil_games_streak_str, value=str(evil_game_streak), inline=True)
                        embed.add_field(name=evil_wins_streak_str, value=str(evil_win_streak), inline=True)
                        embed.add_field(name=evil_loss_streak_str, value=str(evil_loss_streak), inline=True)
                else:
                    if role:
                        embed.description = playerstats_no_games_role_str.format(role)
                    else:
                        embed.description = playerstats_no_games_str

                await ctx.send(embed=embed)

    @streak.error
    async def playerstats_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(cooldown.format(ctx.author.mention, botutils.BotEmoji.x_emoji, display_time(int(ctx.command.get_cooldown_retry_after(ctx)))))
        elif isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.errors.BadUnionArgument):
            await ctx.send(user_not_found_str.format(ctx.author.mention))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())