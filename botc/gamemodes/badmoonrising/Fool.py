"""Contains the Fool Character class"""

import json

from botc import Character, Townsfolk

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.fool.value.lower()]

from botc import emojis


class Fool(Townsfolk, BadMoonRising, Character):
    """Fool: The first time you die, you don't.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/b/ba/Fool_Token.png"
        self._art_link_cropped = "https://imgur.com/nA8CXp1.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Fool"

        self._role_enum = BMRRole.fool
        self._emoji = emojis["badmoonrising"]["fool"]
