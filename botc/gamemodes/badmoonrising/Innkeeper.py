"""Contains the Innkeeper Character class"""

import json
import random

import toml

import globvars
from botc import (Action, ActionTypes, Character, Drunkenness, GameLogic,
                  RecurringAction, SafetyFromDeath, SafetyFromDemon, Townsfolk)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.innkeeper.value.lower()]

from botc import emojis
from config import DISABLE_DMS


class Innkeeper(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Innkeeper: Each night*, choose 2 players: they cannot die tonight, but 1 is drunk until dusk.

    ===== INNKEEPER ===== 

    true_self = innkeeper
    ego_self = innkeeper
    social_self = innkeeper

    commands:
    - host <player1> and <player2>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "host" command
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/3/38/Innkeeper_Token.png"
        self._art_link_cropped = "https://imgur.com/ru3mIMo.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Innkeeper"

        self._role_enum = BMRRole.innkeeper
        self._emoji = emojis["badmoonrising"]["innkeeper"]
        
    def has_finished_night_action(self, player):
        """Return True if the Innkeeper has submitted the host action"""
        
        if player.is_alive():
            # First night, innkeeper does not act
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
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

    @GameLogic.except_first_night
    @GameLogic.requires_two_targets
    @GameLogic.requires_different_targets
    @GameLogic.changes_not_allowed
    async def register_host(self, player, targets):
        """Host command"""

        # Must be 2 targets
        assert len(targets) == 2, "Received a number of targets different than 2 for innkeeper 'host'"
        action = Action(player, targets, ActionTypes.host, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = BotEmoji.butterfly + " " + character_text["feedback"].format(targets[0].game_nametag, targets[1].game_nametag)
        await player.user.send(msg)

    async def exec_host(self, innkeeper_player, targets):
        """Process the host action (nightly ability interaction)"""

        success = "unsuccessfully "

        if innkeeper_player.is_alive() and not innkeeper_player.is_droisoned():
            
            success = ""

            targets[0].add_status_effect(SafetyFromDeath(innkeeper_player, targets[0], None, 1))
            targets[0].add_status_effect(SafetyFromDemon(innkeeper_player, targets[0], None, 1))
                    
            targets[1].add_status_effect(SafetyFromDeath(innkeeper_player, targets[1], None, 1))
            targets[1].add_status_effect(SafetyFromDemon(innkeeper_player, targets[1], None, 1))
            
            chosen_drunk = random.choice([0, 1])

            targets[chosen_drunk].add_status_effect(Drunkenness(innkeeper_player, targets[chosen_drunk]))

        globvars.master_state.game.replay += f"- {innkeeper_player.user.name} (Innkeeper) {success}hosts {targets[0].user.name} " \
            f"({targets[0].role.name}) and {targets[1].user.name} ({targets[1].role.name})\n"

    async def process_night_ability(self, player):
        """Process night actions for the innkeeper character.
        @player : the Innkeeper player (Player object)
        """
        
        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The Fortune teller has submitted an action. We call the execution function immediately
        if action and not action.action_type == ActionTypes.ability_pass:
            assert action.action_type == ActionTypes.host, f"Wrong action type {action} in innkeeper"
            targets = action.target_player
            await self.exec_host(player, targets)
        # The innkeeper has not submitted an action. We will not randomize the action since 
        # the host ability is a "priviledged" ability
        else:
            pass
