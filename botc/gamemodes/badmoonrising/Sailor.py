"""Contains the Sailor Character class"""

import json
from botc import Character, Townsfolk
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.sailor.value.lower()]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


class Sailor(Townsfolk, BadMoonRising, Character):
    """Sailor: Each night, choose a player: either you or they are drunk until dusk. 
    You can not die.
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
        
