"""Contains the Innkeeper Character class"""

import json
import globvars
from botc import Character, Townsfolk, ActionTypes
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.innkeeper.value.lower()]


class Innkeeper(Townsfolk, BadMoonRising, Character):
    """Innkeeper: Each night*, choose 2 players: they cannot die tonight, but 1 is drunk until dusk.
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
        self._emoji = "<:bmrinnkeeper:781152055003840552>"
        
    def has_finished_night_action(self, player):
        """Return True if the Innkeeper has submitted the host action"""
        
        if player.is_alive():
            # First night, innkeeper does not act
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.host
        return True