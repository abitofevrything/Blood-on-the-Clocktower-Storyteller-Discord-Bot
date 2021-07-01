"""Contains the notes command cog"""

import re
import traceback
from inspect import Parameter
from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument

import botutils
import globvars
from botc import (BOTCUtils, Category, NotAPlayer, NotDMChannel, NotNight,
                  Phase, Player, PlayerConverter, PlayerNotFound, RoleNotFound,
                  check_if_dm, game_text)
from botc.Character import Character
from botc.checks import check_if_is_player
from botutils import BotEmoji, bot_text
from config import CLAIM_SHOW_TIME

notes_add_feedback_str = game_text["doc"]["notes"]["add"]["feedback"]
notes_remove_feedback_str = game_text["doc"]["notes"]["remove"]["feedback"]
info_add_feedback_str = game_text["doc"]["notes"]["info"]["add"]["feedback"]
info_remove_feedback_str = game_text["doc"]["notes"]["info"]["remove"]["feedback"]
remove_claim_str = game_text["doc"]["notes"]["claim"]["remove"]["feedback"]
private_remove_claim_str = game_text["doc"]["notes"]["claim"]["remove"]["private_feedback"]
claim_role_str = game_text["doc"]["notes"]["claim"]["add"]["feedback"]
private_claim_role_str = game_text["doc"]["notes"]["claim"]["add"]["private_feedback"]

role_not_found_str = game_text["cmd_warnings"]["role_not_found"]
player_not_found_str = game_text["cmd_warnings"]["player_not_found"]

error_str = bot_text["system"]["error"]

class Notes(commands.Cog, name = game_text["misc"]["info_cog"]):

    def __init__(self, client) -> None:
        self.client = client

    @commands.group(
        pass_context = True,
        name = "notes",
        aliases = ["n"],
        invoke_without_command = True,
        brief = game_text["doc"]["notes"]["brief"],
        help = game_text["doc"]["notes"]["help"],
        description = game_text["doc"]["notes"]["description"]
    )
    @commands.check(check_if_is_player)
    async def notes(self, ctx, *, args = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if args is None:
            # Claims summary
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(invoking_player), make_code=True, delete_after=CLAIM_SHOW_TIME)
            else:
                await botutils.send_long_message(ctx.channel, globvars.master_state.game.note_manager.format_notes(), make_code=True, delete_after=CLAIM_SHOW_TIME)
            return
        else:
            if isinstance(ctx.channel, discord.channel.DMChannel):
                await self.notes_add.callback(self, ctx, args=args)

    @notes.command(
        pass_context = True,
        name = "add",
        brief = game_text["doc"]["notes"]["add"]["brief"],
        help = game_text["doc"]["notes"]["add"]["help"],
        description = game_text["doc"]["notes"]["add"]["description"]
    )
    @commands.check(check_if_dm)
    async def notes_add(self, ctx, *, args):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        args = re.split(' +', args)

        target_player = BOTCUtils.get_player_from_string(args[0])
        if target_player is None:
            target_player = invoking_player
            note = ' '.join(args)
        else:
            args.pop(0)
            note = ' '.join(args)

        globvars.master_state.game.note_manager.note(target_player, note, invoking_player)
        await ctx.send(notes_add_feedback_str.format(BotEmoji.check))

    @notes.command(
        pass_context = True,
        name = "remove",
        aliases = ["rem", "rm"],
        brief = game_text["doc"]["notes"]["remove"]["brief"],
        help = game_text["doc"]["notes"]["remove"]["help"],
        description = game_text["doc"]["notes"]["remove"]["description"]
    )
    @commands.check(check_if_dm)
    async def notes_remove(self, ctx, player_or_id: Union[PlayerConverter, int], id: int = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if isinstance(player_or_id, Player):
            if id is None:
                raise MissingRequiredArgument(Parameter('id', Parameter.POSITIONAL_ONLY))
        else:
            id = player_or_id
            player_or_id = invoking_player

        globvars.master_state.game.note_manager.rm_note(player_or_id, id, invoking_player)
        await ctx.send(notes_remove_feedback_str.format(BotEmoji.check))

    @notes.group(
        pass_context = True,
        name = "info",
        aliases = ['i'],
        invoke_without_command = True,
        brief = game_text["doc"]["notes"]["info"]["brief"],
        help = game_text["doc"]["notes"]["info"]["help"],
        description = game_text["doc"]["notes"]["info"]["description"]
    )
    async def info(self, ctx, *, args: str):
        await self.info_add.callback(self, ctx, args=args)

    @info.command(
        pass_context = True,
        name = "add",
        brief = game_text["doc"]["notes"]["info"]["add"]["brief"],
        help = game_text["doc"]["notes"]["info"]["add"]["help"],
        description = game_text["doc"]["notes"]["info"]["add"]["description"]
    )
    @commands.check(check_if_dm)
    async def info_add(self, ctx, *, args: str):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        args = re.split(' +', args)

        # Ensure that we have enough values in the list
        args += ['', '']

        try:
            target_phase = int(args[0])
            target_player = None
            args.pop(0)
        except ValueError:
            target_player = BOTCUtils.get_player_from_string(args[0])
            if target_player is not None:
                args.pop(0)

            try:
                target_phase = int(args[0])
                args.pop(0)
            except ValueError:
                target_phase = None

        # Remove the two dummy elements
        args.pop()
        args.pop()

        rem = ' '.join(args)

        if not rem.strip():
            if target_phase is None:
                if target_player is None:
                    raise commands.MissingRequiredArgument(Parameter('info', Parameter.POSITIONAL_ONLY))
                else:
                    # Added info was a player name
                    rem = str(target_player)
                    target_player = None
            else:
                # Added info was a number (empath for example)
                rem = str(target_phase)
                target_phase = None

        if target_phase is not None and target_phase > globvars.master_state.game._chrono.cycle:
            raise commands.BadArgument()

        if target_player is not None:
            globvars.master_state.game.note_manager.info(target_player, rem, invoking_player, target_phase)
        else:
            if globvars.master_state.game._chrono.phase == Phase.night:
                raise NotNight("Command is allowed during night phase only (BoTC)")
            globvars.master_state.game.note_manager.info(invoking_player, rem, None, target_phase)

        await ctx.send(info_add_feedback_str.format(BotEmoji.check))

    @info.command(
        pass_context = True,
        name = "remove",
        aliases = ["rem", "rm"],
        brief = game_text["doc"]["notes"]["info"]["remove"]["brief"],
        help = game_text["doc"]["notes"]["info"]["remove"]["help"],
        description = game_text["doc"]["notes"]["info"]["remove"]["description"]
    )
    @commands.check(check_if_dm)
    async def info_remove(self, ctx, player_or_id: Union[int, PlayerConverter] = None, id: PlayerConverter() = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if isinstance(player_or_id, int):
            id = player_or_id
            player_or_id = None

        if player_or_id is None:
            if globvars.master_state.game._chrono.phase == Phase.night:
                raise NotNight("Command is allowed during night phase only (BoTC)")
            globvars.master_state.game.note_manager.rm_info(invoking_player, id)
        else:
            globvars.master_state.game.note_manager.rm_info(player_or_id, id, invoking_player)

        await ctx.send(info_remove_feedback_str.format(BotEmoji.check))

    @notes.group(
        name = "claim",
        aliases = ["c", "cl", "claims"],
        invoke_without_command = True,
        brief = game_text["doc"]["notes"]["claim"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["help"],
        description = game_text["doc"]["notes"]["claim"]["description"]
    )
    @commands.check(check_if_dm)
    async def claim(self, ctx, player_or_claim: str, claim: str = None):
        await self.claim_add.callback(self, ctx, player_or_claim, claim)

    @claim.command(
        pass_context = True,
        name = "add",
        brief = game_text["doc"]["notes"]["claim"]["add"]["brief"],
        help = game_text["doc"]["notes"]["claim"]["add"]["help"],
        description = game_text["doc"]["notes"]["claim"]["add"]["description"]
    )
    @commands.check(check_if_dm)
    async def claim_add(self, ctx, player_or_claim: str, claim: str = None):
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        # Overloading a command
        temp = botutils.find_role_in_all(player_or_claim)
        if temp is not None:
            if temp.gm_of_appearance != globvars.master_state.game.gamemode:
                raise RoleNotFound(role_not_found_str.format(ctx.author.mention, BotEmoji.x_emoji))
            player_or_claim = temp
        else:
            temp = BOTCUtils.get_player_from_string(player_or_claim)
            player_or_claim = (temp if temp is not None else player_or_claim)

        if claim is not None:
            temp = botutils.find_role_in_all(claim)
            if temp is not None:
                if temp.gm_of_appearance != globvars.master_state.game.gamemode:
                    raise RoleNotFound(role_not_found_str.format(ctx.author.mention, BotEmoji.x_emoji))
                claim = temp


        if isinstance(player_or_claim, Player):
            if claim is None:
                raise MissingRequiredArgument(Parameter('claim', Parameter.POSITIONAL_ONLY))

            if isinstance(claim, Character):
                claimed_character = claim
                claimed_category = claimed_character.category
            else:
                claimed_character = None

                claim = claim.lower()
                if claim in ('town', 'townsfolk'):
                    claimed_category = Category.townsfolk
                elif claim in ('os', 'outsider'):
                    claimed_category = Category.outsider
                elif claim in ('minion'):
                    claimed_category = Category.minion
                elif claim in ('demon'):
                    claimed_category = Category.demon
                else:
                    raise RoleNotFound(role_not_found_str.format(ctx.author.mention, BotEmoji.x_emoji))

        elif isinstance(player_or_claim, Character):
            claimed_character = player_or_claim
            claimed_category = claimed_character.category
            player_or_claim = None
        else:
            claimed_character = None

            player_or_claim = player_or_claim.lower()
            if player_or_claim in ('town', 'townsfolk'):
                claimed_category = Category.townsfolk
            elif player_or_claim in ('os', 'outsider'):
                claimed_category = Category.outsider
            elif player_or_claim in ('minion'):
                claimed_category = Category.minion
            elif player_or_claim in ('demon'):
                claimed_category = Category.demon
            else:
                raise RoleNotFound(role_not_found_str.format(ctx.author.mention, BotEmoji.x_emoji))

            player_or_claim = None

        if player_or_claim is None:
            if globvars.master_state.game._chrono.phase == Phase.night:
                raise NotNight("Command is allowed during night phase only (BoTC)")

            old_claim_role = globvars.master_state.game.note_manager.public_notes().get_entry(invoking_player).claimed_role
            old_claim_category = globvars.master_state.game.note_manager.public_notes().get_entry(invoking_player).claimed_category

            globvars.master_state.game.note_manager.claim(invoking_player, claimed_category, claimed_character)

            an_a_the = "the"
            if claimed_character == None:
                if claimed_category == Category.outsider:
                    an_a_the = "an"
                else:
                    an_a_the = "a"

            if old_claim_role != claimed_character or old_claim_category != claimed_category:
                await botutils.send_lobby(claim_role_str.format(ctx.author.mention, an_a_the, (claimed_character.name if claimed_character else claimed_category.value)), delete_after=CLAIM_SHOW_TIME)
        else:
            globvars.master_state.game.note_manager.claim(player_or_claim, claimed_category, claimed_character, invoking_player)

        await ctx.send(private_claim_role_str.format(BotEmoji.check))

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
        invoking_player = BOTCUtils.get_player_from_id(ctx.author.id)

        if player is None:
            if globvars.master_state.game._chrono.phase == Phase.night:
                raise NotNight("Command is allowed during night phase only (BoTC)")
            globvars.master_state.game.note_manager.rm_claim(invoking_player)
            await botutils.send_lobby(remove_claim_str.format(ctx.author.mention), delete_after = CLAIM_SHOW_TIME)
        else:
            globvars.master_state.game.note_manager.rm_claim(player, invoking_player)

        await ctx.send(private_remove_claim_str.format(BotEmoji.check))


    @notes.error
    @notes_add.error
    @notes_remove.error
    @info.error
    @info_add.error
    @info_remove.error
    @claim.error
    @claim_add.error
    @claim_remove.error
    async def notes_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = game_text["cmd_warnings"]["missing_arguments"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, PlayerNotFound):
            msg = game_text["cmd_warnings"]["player_not_found"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, RoleNotFound):
            error = getattr(error, 'original', error)
            await ctx.send(error)
        elif isinstance(error, NotNight):
            await ctx.send(game_text["cmd_warnings"]["night_only"].format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, NotAPlayer):
            return
        elif isinstance(error, commands.BadArgument):
            msg = game_text["cmd_warnings"]["bad_argument"]
            await ctx.send(msg.format(ctx.author.mention, BotEmoji.x_emoji))
        elif isinstance(error, NotDMChannel):
            return
        else:
            try:
                raise error
            except Exception:
                await ctx.send(error_str)
                await botutils.log(botutils.Level.error, traceback.format_exc())
