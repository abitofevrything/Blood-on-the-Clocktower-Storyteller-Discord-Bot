"""Contains the Chambermaid Character class"""

import json
import globvars
from botc import Character, Townsfolk, ActionTypes
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.chambermaid.value.lower()]


class Chambermaid(Townsfolk, BadMoonRising, Character):
    """Chambermaid Each night, choose 2 alive players (not yourself): you learn how many woke 
    tonight due to their ability.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/8/87/Chambermaid_Token.png"
        self._art_link_cropped = "https://imgur.com/eNn6hQa.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Chambermaid"

        self._role_enum = BMRRole.chambermaid
        self._emoji = "<:bmrchambermaid:781151556053499925>"

    def has_finished_night_action(self, player):
        """Return True if the Chambermaid has submitted the see action"""

        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.see
        return True