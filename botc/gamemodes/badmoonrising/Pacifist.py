"""Contains the Pacifist Character class"""

import json
import random

import globvars
from botc import (Character, NonRecurringAction, SafetyFromExecution,
                  StatusList, Townsfolk)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.pacifist.value.lower()]

from botc import emojis


class Pacifist(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Pacifist: Executed good players may not die.

    ===== PACIFIST ===== 

    true_self = pacifist
    ego_self = pacifist
    social_self = pacifist

    commands:

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> NO

    END:
    override regular night end? -> YES
                                => Give certain good players safety from execution
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/1/1a/Pacifist_Token.png"
        self._art_link_cropped = "https://imgur.com/3diVUmW.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Pacifist"

        self._role_enum = BMRRole.pacifist
        self._emoji = emojis["badmoonrising"]["pacifist"]

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

    def exec_init_role(self, setup):
        pacifist_player = [p for p in globvars.master_state.game.player_obj_list if p.role.true_self.name == BMRRole.pacifist.value]
        pacifist_player = pacifist_player[0]
        for player in globvars.master_state.game.player_obj_list:
            if random.random() < 0.5 and player.role.social_self.is_good():
                player.add_status_effect(SafetyFromExecution(pacifist_player, player, None, float("inf")))

    async def after_night(self, pacifist_player):
        if pacifist_player.is_droisoned():
            for player in globvars.master_state.game.player_obj_list:
                if player.has_status_effect(StatusList.safety_from_execution) and \
                    len([effect for effect in player.status_effects if effect.effect == StatusList.safety_from_execution\
                    and effect.source_player == pacifist_player]) == 1:
                    
                    player.remove_status_effect(StatusList.safety_from_execution, pacifist_player)

        else:
            for player in globvars.master_state.game.player_obj_list:
                if random.random() < 0.5 and player.role.social_self.is_good():
                    player.add_status_effect(SafetyFromExecution(pacifist_player, player, None, float("inf")))