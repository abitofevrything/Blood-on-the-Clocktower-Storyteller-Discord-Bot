"""Nominate command"""

import json
import traceback

from discord.ext import commands

import botutils
from botc import (AliveOnlyCommand, BOTCUtils, NotAPlayer, NotDay,
                  NotLobbyChannel, PlayerConverter, check_if_is_day,
                  check_if_is_player, check_if_lobby,
                  check_if_player_apparently_alive)
from botutils import bot_text

error_str = bot_text["system"]["error"]

from botc import game_text

nomination_ongoing = game_text["cmd_warnings"]["nomination_ongoing"]
nominations_not_open = game_text["cmd_warnings"]["nominations_not_open"]
cannot_be_nominated_again = game_text["cmd_warnings"]["cannot_be_nominated_again"]
cannot_nominate_again = game_text["cmd_warnings"]["cannot_nominate_again"]


class Nominate(commands.Cog, name = game_text["misc"]["townhall_cog"]):
    """BoTC in-game commands cog
    Nominate command - used for execution
    """

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        """Check performed on all commands of this cog.
        Must be a non-fleaved player to use these commands.
        """
        return check_if_is_player(ctx)  # Registered non-quit player -> NotAPlayer

    # ---------- NOMINATE COMMAND (Voting) ----------------------------------------
    @commands.command(
        pass_context = True,
        name = "nominate",
        hidden = False,
        aliases = ["nom"],
        brief = game_text["doc"]["nominate"]["brief"],
        help = game_text["doc"]["nominate"]["help"],
        description = game_text["doc"]["nominate"]["description"]
    )
    @commands.check(check_if_lobby)  # Correct channel -> NotLobbyChannel
    @commands.check(check_if_is_day)  # Correct phase -> NotDay
    @commands.check(check_if_player_apparently_alive)  # Player alive -> AliveOnlyCommand
    async def nominate(self, ctx, *, nominated: PlayerConverter()):
        """Nominate command
        usage: nominate <player>
        characters: living players
        """
        import globvars
        from botc.gameloops import base_day_loop, nomination_loop
        player = BOTCUtils.get_player_from_id(ctx.author.id)

        # A nomination is currently going on. The player cannot nominate.
        if nomination_loop.is_running():
            msg = nomination_ongoing.format(
                ctx.author.mention,
                botutils.BotEmoji.x_emoji
            )
            await ctx.send(msg)
            return

        # The day has not reached nomination phase yet. The player cannot nominate.
        elif base_day_loop.is_running():
            msg = nominations_not_open.format(
                ctx.author.mention,
                botutils.BotEmoji.x_emoji
            )
            await ctx.send(msg)
            return

        if player.can_nominate():
            if nominated.can_be_nominated():
                # The player cannot nominate again today
                player.toggle_has_nominated()
                # The nominated player cannot be nominated again today
                nominated.toggle_was_nominated()
                await nominated.role.true_self.on_being_nominated(player, nominated)
            else:
                msg = cannot_be_nominated_again.format(
                    ctx.author.mention,
                    botutils.BotEmoji.x_emoji,
                    nominated.game_nametag
                )
                await ctx.send(msg)
        else:
            msg = cannot_nominate_again.format(
                ctx.author.mention,
                botutils.BotEmoji.x_emoji
            )
            await ctx.send(msg)


    @nominate.error
    async def nominate_error(self, ctx, error):
        emoji = botutils.BotEmoji.x_emoji
        # Non-registered or quit player -> NotAPlayer
        if isinstance(error, NotAPlayer):
            return
        # Incorrect argument -> commands.BadArgument
        elif isinstance(error, commands.BadArgument):
            await ctx.send(game_text["cmd_warnings"]["player_not_found"].format(ctx.author.mention, emoji))
        # Incorrect channel -> NotLobbyChannel
        elif isinstance(error, NotLobbyChannel):
            await ctx.send(game_text["cmd_warnings"]["lobby_only"].format(ctx.author.mention, emoji))
        # Player not alive -> AliveOnlyCommand
        elif isinstance(error, AliveOnlyCommand):
            await ctx.send(game_text["cmd_warnings"]["alive_only"].format(ctx.author.mention, emoji))
        # Incorrect phase -> NotDay
        elif isinstance(error, NotDay):
            await ctx.send(game_text["cmd_warnings"]["day_only"].format(ctx.author.mention, emoji))
        # Missing argument -> commands.MissingRequiredArgument
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(game_text["cmd_warnings"]["player_not_found"].format(ctx.author.mention, emoji))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())

def setup(client):
    client.add_cog(Nominate(client))
