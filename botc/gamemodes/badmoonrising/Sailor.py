"""Contains the Sailor Character class"""

import json
import random

import toml

import globvars
from botc import (Action, ActionTypes, Character, GameLogic, Player,
                  RecurringAction, SailorDrunkenness, Targets, Townsfolk)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.sailor.value.lower()]

butterfly = BotEmoji.butterfly
from botc import emojis
from config import DISABLE_DMS


class Sailor(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Sailor: Each night, choose a player: either you or they are drunk until dusk. 
    You cannot die.

    ===== SAILOR =====

    true_self = sailor
    ego_self = sailor
    social_self = sailor

    commands:
    - visit <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send query for "visit" command

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "visit" command
    """

    def __init__(self):

        Character.__init__(self)
        BadMoonRising.__init__(self)
        Townsfolk.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/0/01/Sailor_Token.png"
        self._art_link_cropped = "https://imgur.com/wXLvtmm.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Sailor"

        self._role_enum = BMRRole.sailor
        self._emoji = emojis["badmoonrising"]["sailor"]

    def has_finished_night_action(self, player):
        """Return True if sailor has submitted the visit action"""

        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(
                current_phase_id)
            return received_action is not None
        return True

    def create_n1_instr_str(self):
        """Create the instruction field on the opening dm card"""

        # First line is the character instruction string
        msg = f"{self.emoji} {self.instruction}"
        addendum = character_text["n1_addendum"]

        # Some characters have a line of addendum
        if addendum:
            scroll_emoji = BotEmoji.scroll
            msg += f"\n{scroll_emoji} {addendum}"

        return msg

    def add_action_field_n1(self, embed_obj):
        """Send the stats list n1"""

        msg = self.action
        msg += globvars.master_state.game.create_sitting_order_stats_string()
        embed_obj.add_field(
            name=butterfly + " **「 Your Action 」**", value=msg, inline=False)
        return embed_obj

    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    async def register_visit(self, player, targets):
        """Visit command"""
        # Must be 1 target
        assert len(
            targets) == 1, "Received a number of targets different than 1 for sailor 'visit'"
        action = Action(player, random.choice([targets, Targets(
            [player])]), ActionTypes.visit, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(
            action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + \
            character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_visit(self, player, target):
        """Visit command"""

        success = "unsuccessfully "

        if not player.is_droisoned() and player.is_alive():
            target.add_status_effect(SailorDrunkenness(player, target))
            success = ""

        globvars.master_state.game.replay += f"- {player.user.name} (Sailor) {success}poisons {target.user.name} ({target.role.name})\n"

    async def process_night_ability(self, player):
        """Process night actions for the sailor character.
        @player : the Sailor player (Player object)
        """

        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The sailor has submitted an action. We call the execution function immediately
        if action and not action.action_type == ActionTypes.ability_pass:
            assert action.action_type == ActionTypes.visit, f"Wrong action type {action} in sailor"
            targets = action.target_player
            poisoned_player = targets[0]
            await self.exec_visit(player, poisoned_player)
        # The sailer has not submitted an action. We will not randomize the action since
        # the visit ability is a "priviledged" ability
        else:
            pass

    def can_be_executed(self, player):
        if not player.is_droisoned():
            return False
        return super().can_be_executed(player)

    def can_be_demon_killed(self, player):
        if not player.is_droisoned():
            return False
        return super().can_be_demon_killed(player)

    def can_be_killed(self, player):
        if not player.is_droisoned():
            return False
        return super().can_be_killed(player)
