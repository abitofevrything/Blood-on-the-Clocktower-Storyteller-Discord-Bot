"""Contains the Pacifist Character class"""

import json
from botc import Character, Townsfolk, NonRecurringAction
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.pacifist.value.lower()]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


class Pacifist(Townsfolk, BadMoonRising, Character, NonRecurringAction): # Not sure what to put here, should it be RecurringAction? Probably depends on implementation.
    """Pacifist: Executed good players may not die.
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
        return "not_implemented"
