"""Contains the claim command cog"""

import traceback

import botutils
import re
import discord
import globvars
from botc import (BOTCUtils, NotDMChannel, PlayerConverter, PlayerNotFound,
                  RoleNotFound, check_if_dm, game_text, NotNight, Category, Phase)
from botc.checks import check_if_is_player
from botutils import BotEmoji, bot_text
from config import CLAIM_SHOW_TIME
from discord.ext import commands

error_str = bot_text["system"]["error"]
claim_role_str = game_text["doc"]["notes"]["claim"]["add"]["feedback"]

# Claim strings
claim_matches = {
    r"im .+": r"(?<=im ).+",
    r"i'm .+": r"(?<=i'm ).+", 
    r"i am .+": r"(?<=i am ).+",
    r"im a .+": r"(?<=im a ).+",
    r"i'm a .+": r"(?<=i'm a ).+",
    r"i am a .+": r"(?<=i am a ).+",
    r"im an .+": r"(?<=im an ).+",
    r"i'm an .+": r"(?<=i'm an ).+",
    r"i am an .+": r"(?<=i am an ).+",
    r"im the .+": r"(?<=im the ).+",
    r"i'm the .+": r"(?<=i'm the ).+",
    r"i am the .+": r"(?<=i am the ).+",

    r".+ here": r".+(?= here)",
    r"your .+ here": r"(?<=your ).+(?= here)",
}

claim_matches = {re.compile(f"^{k}$", re.IGNORECASE): re.compile(v, re.IGNORECASE) for k, v in claim_matches.items()}

class Claim(commands.Cog, name = game_text["misc"]["info_cog"]):
    
    def __init__(self, client) -> None:
        self.client = client

        self.notes_command = next(c for c in client.commands if c.name == "notes")
        self.notes_claim_command = next(c for c in self.notes_command.commands if c.name == "claim")
        self.notes_claim_add_command = next(c for c in self.notes_claim_command.commands if c.name == "add")
        self.notes_claim_remove_command = next(c for c in self.notes_claim_command.commands if c.name == "remove")

    @commands.group(
        pass_context = True,
        name = "claim",
        aliases = ["cl", "c", "claims"],
        invoke_without_command = True,
        brief = game_text["doc"]["notes"]["claim"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["help"],
        description = game_text["doc"]["notes"]["claim"]["description"]
    )
    @commands.check(check_if_is_player)
    async def claim(self, ctx, player_or_claim = None, claim: str = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if player_or_claim is None:
            # Claims summary
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(invoking_player), make_code=True, delete_after=CLAIM_SHOW_TIME)
            else:
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(), make_code=True, delete_after=CLAIM_SHOW_TIME)
            return
        else:
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await self.notes_claim_command.callback(self, ctx, player_or_claim, claim)

    @claim.command(
        pass_context = True,
        name = "add",
        brief = game_text["doc"]["notes"]["claim"]["add"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["add"]["help"],
        description = game_text["doc"]["notes"]["claim"]["add"]["description"]
    )
    @commands.check(check_if_dm)
    async def claim_add(self, ctx, player_or_claim: str, claim: str = None):
        await self.notes_claim_add_command.callback(self, ctx, player_or_claim, claim)

    @claim.command(
        pass_context = True,
        name = "remove",
        aliases = ["rem", "rm", "clear"],
        brief = game_text["doc"]["notes"]["claim"]["remove"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["remove"]["help"],
        description = game_text["doc"]["notes"]["claim"]["remove"]["description"]
    )
    @commands.check(check_if_dm)
    async def claim_remove(self, ctx, player: PlayerConverter = None):
        await self.notes_claim_remove_command.callback(self, ctx, player)
    
    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        ctx = await globvars.client.get_context(message)
        # Empty messages (image uploads) may cause issues, we ignore them
        if not isinstance(message.content, str):
            return
        try:
            if botutils.check_if_lobby(ctx):
                player = BOTCUtils.get_player_from_id(message.author.id)
                if player is not None:
                    if globvars.master_state.game._chrono.phase == Phase.night:
                        return
                    for k, v in claim_matches.items():
                        if k.fullmatch(message.content):
                            claim_str = v.search(message.content).group().lower()

                            claimed_character = None
                            claimed_category = None

                            temp = botutils.find_role_in_all(claim_str)
                            if temp is not None:
                                if temp.gm_of_appearance != globvars.master_state.game.gamemode:
                                    continue
                                claimed_character = temp
                                claimed_category = temp.category
                            else:
                                if claim_str in ('town', 'townsfolk'):
                                    claimed_category = Category.townsfolk
                                elif claim_str in ('os', 'outsider'):
                                    claimed_category = Category.outsider
                                elif claim_str in ('minion'):
                                    claimed_category = Category.minion
                                elif claim_str in ('demon'):
                                    claimed_category = Category.demon
                                else:
                                    continue

                            an_a_the = "the"
                            if claimed_character == None:
                                if claimed_category == Category.outsider:
                                    an_a_the = "an"
                                else:
                                    an_a_the = "a"

                            globvars.master_state.game.note_manager.claim(player, claimed_category, claimed_character)
                            await botutils.send_lobby(claim_role_str.format(message.author.mention, an_a_the, (claimed_character.name if claimed_character else claimed_category.value)))
                            return
        except Exception:
            await ctx.send(error_str)
            await botutils.log(botutils.Level.error, traceback.format_exc())

    @claim.error
    async def claim_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = game_text["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, PlayerNotFound):
            msg = game_text["cmd_warnings"]["player_not_found"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, RoleNotFound):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, BOTCUtils.NotAPlayer):
            return
        elif isinstance(error, commands.BadArgument):
            msg = game_text["cmd_warnings"]["bad_argument"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, NotDMChannel):
            return
        elif isinstance(error, NotNight):
            await ctx.send(game_text["cmd_warnings"]["night_only"].format(ctx.author.mention, BotEmoji.x_emoji))
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())


    # Errors must be handled per-command, not per-group

    @claim_add.error
    async def claim_add_error(self, ctx, error):
        await ctx.command.root_parent.on_error(self, ctx, error)

    @claim_remove.error
    async def claim_remove_error(self, ctx, error):
        await ctx.command.root_parent.on_error(self, ctx, error)
