"""Contains the join command cog"""

import botutils
import json
import random
import traceback
from library.fancytext import fancy
from discord.ext import commands
from ._gameplay import Gameplay
from botutils import lobby_timeout

with open('botutils/bot_text.json') as json_file:
    language = json.load(json_file)
    vote_str = language["cmd"]["vote"]
    gm_not_found_str = language["cmd"]["gm_not_found"]

joined_str = language["cmd"]["joined"]
error_str = language["system"]["error"]

x_emoji = botutils.BotEmoji.cross

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


class Join(Gameplay, name = language["system"]["gameplay_cog"]):
    """Join command cog"""

    @commands.command(
        pass_context = True,
        name = "join",
        aliases = ["j"],
        brief = language["doc"]["join"]["brief"],
        help = language["doc"]["join"]["help"],
        description = language["doc"]["join"]["description"]
    )
    @commands.check(botutils.check_if_lobby)
    @commands.check(botutils.check_if_not_in_game)
    async def join(self, ctx, vote: str = None):
        """Join command"""
        
        import globvars

        if globvars.master_state.game:
            # This check is to ensure a player doesn't join right after !start
            # before the game is fully set up and end up breaking the game.
            return

        # The command user has already joined
        if globvars.master_state.pregame.is_joined(ctx.author.id):
            await ctx.send(joined_str.format(ctx.author.mention))

        # The command user has not joined yet; make them join
        else:
            globvars.master_state.pregame.safe_add_player(ctx.author.id)
            botutils.update_state_machine()
            join_replies = language["doc"]["join"]["outputs"]
            join_weights = language["doc"]["join"]["weights"]

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
                lobby_timeout.start()

            # Handle votes
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

        # Still give everyone the role just in case of discord sync issue
        await botutils.add_alive_role(ctx.author)
    
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
