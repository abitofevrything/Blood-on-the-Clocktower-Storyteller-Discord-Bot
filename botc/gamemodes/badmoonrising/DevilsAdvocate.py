"""Contains the Devil's Advocate Character class"""

import json
import globvars
from botc import Character, Minion, ActionTypes
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.devilsadvocate.value.lower()]


class DevilsAdvocate(Minion, BadMoonRising, Character):
    """Devil's Advocate: Each night, choose a living player (not the same as last night): 
    if executed tomorrow, they do not die.
    """

    def __init__(self):
        
        Character.__init__(self)
        BadMoonRising.__init__(self)
        Minion.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/2/23/Devils_Advocate_Token.png"
        self._art_link_cropped = "https://imgur.com/b2rcp8E.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Devil%27s_Advocate"

        self._role_enum = BMRRole.devilsadvocate
        self._emoji = "<:bmrdevilsadvocate:781151556493639680>"

    def has_finished_night_action(self, player):
        """Return True if the devil's advocate has submitted the protect action"""

        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.protect
        return True