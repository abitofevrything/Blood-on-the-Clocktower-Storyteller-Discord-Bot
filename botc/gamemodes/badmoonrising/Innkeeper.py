"""Contains the Innkeeper Character class"""

import json
from botc import Character, Townsfolk
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.innkeeper.value.lower()]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


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
        self._emoji = emojis["badmoonrising"]["innkeeper"]
        
