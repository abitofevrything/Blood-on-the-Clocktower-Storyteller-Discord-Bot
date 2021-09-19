"""Contains the join command cog"""

import json
import random
import sqlite3
import traceback

from discord.ext import commands

import botutils
from botutils import bot_text, lobby_timeout
from library.fancytext import fancy

from ._gameplay import Gameplay

joined_str = bot_text["cmd"]["joined"]
joined_alt_str = bot_text["cmd"]["joined_alt"]
error_str = bot_text["system"]["error"]
vote_str = bot_text["cmd"]["vote"]
gm_not_found_str = bot_text["cmd"]["gm_not_found"]
voting_disabled_str = bot_text["cmd"]["voting_diabled"]
not_joined_str = bot_text["cmd"]["not_joined"]

x_emoji = botutils.BotEmoji.x_emoji

emojis = [
    botutils.BotEmoji.char1,
    botutils.BotEmoji.char2,
    botutils.BotEmoji.char3,
    botutils.BotEmoji.char4,
    botutils.BotEmoji.char5,
    botutils.BotEmoji.char6,
    botutils.BotEmoji.char7,
    botutils.BotEmoji.char8,
    botutils.BotEmoji.char9,
    botutils.BotEmoji.char10,
    botutils.BotEmoji.char11,
    botutils.BotEmoji.char12,
    botutils.BotEmoji.char13,
    botutils.BotEmoji.char14
]


class Join(Gameplay, name = bot_text["system"]["gameplay_cog"]):
    """Join command cog"""

    @commands.command(
        pass_context = True,
        name = "join",
        aliases = ["j", "vote", "v"],
        brief = bot_text["doc"]["join"]["brief"],
        help = bot_text["doc"]["join"]["help"],
        description = bot_text["doc"]["join"]["description"]
    )
    @commands.check(botutils.check_if_lobby)
    @commands.check(botutils.check_if_not_in_game)
    async def join(self, ctx, vote: str = None):
        """Join command"""

        vote = ctx.message.content[len(ctx.prefix) + len(ctx.invoked_with):]

        # If player is not in lobby, make them join
        # If no vote is provided and player is alr in lobby, send the error message
        # If vote is given, register that vote
        
        import globvars

        if globvars.master_state.game:
            # This check is to ensure a player doesn't join right after !start
            # before the game is fully set up and end up breaking the game.
            return

        if not globvars.master_state.pregame.is_joined(ctx.author.id):
            if ctx.invoked_with == 'v' or ctx.invoked_with == 'vote':
                await ctx.send(not_joined_str.format(ctx.author.mention, x_emoji))
                return

            user_ids = set()

            with sqlite3.connect("data.sqlite3") as conn:
                c = conn.cursor()

                c.execute("""
                SELECT
                    primary_user_id,
                    secondary_user_id
                FROM
                    player_map
                WHERE
                    primary_user_id = :user_id
                    OR secondary_user_id = :user_id
                """, {
                    "user_id": ctx.author.id,
                })

                for row in c.fetchall():
                    primary, secondary = row

                    user_ids.add(primary)
                    user_ids.add(secondary)

            for user_id in globvars.master_state.pregame:
                if user_id in user_ids:
                    user = globvars.client.get_user(user_id)
                    await ctx.send(joined_alt_str.format(ctx.author.mention, str(user)))
                    return

            globvars.master_state.pregame.safe_add_player(ctx.author.id)
            botutils.update_state_machine()
            join_replies = bot_text["doc"]["join"]["outputs"]
            join_weights = bot_text["doc"]["join"]["weights"]

            if join_weights:
                join_reply = random.choices(
                    join_replies,
                    weights=join_weights
                )
                join_str = join_reply[0]
            else:
                join_str = random.choice(join_replies)

            emoji = random.choice(emojis)
            msg = emoji
            msg += " "
            msg += join_str.format(
                ctx.author.name,
                len(globvars.master_state.pregame),
                "player" if len(globvars.master_state.pregame) == 1 else "players"
            )
            await ctx.send(msg)

            # If you are the first player to join the game, then start the lobby timeout loop
            if len(globvars.master_state.pregame) == 1:
                if lobby_timeout.is_running():
                    lobby_timeout.cancel()
                lobby_timeout.start()

        elif not vote:
            await ctx.send(joined_str.format(ctx.author.mention))
            return

        await botutils.add_alive_role(ctx.author)

        if vote:

                gm = botutils.get_gamemode_from_str(vote)

                # Bad string passed
                if gm is None:
                    await ctx.send(gm_not_found_str.format(x_emoji, ctx.author.mention, vote))
                else:
                    globvars.master_state.game_chooser.register_vote(ctx.author.id, gm)

                    current_votes = globvars.master_state.game_chooser.votes

                    votes_str = '\n'.join([f"{gm.value}: {current_votes[gm]}" for gm in current_votes])

                    await ctx.send(vote_str.format(ctx.author.mention, fancy.bold(gm.value), votes_str))
    
    @join.error
    async def join_error(self, ctx, error):
        """Error handling of the join command"""

        # Case: check failure
        if isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.BadArgument):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        
        # For other cases we will want to see the error logged
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
