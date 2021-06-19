"""Contains the Moonchild Character class"""

import json

from botc import Character, Outsider

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.moonchild.value.lower()]

from botc import emojis


class Moonchild(Outsider, BadMoonRising, Character):
    """Moonchild: When you learn you are dead, choose 1 alive player: if good, they die tonight.
    """

    def __init__(self):

        Character.__init__(self)
        BadMoonRising.__init__(self)
        Outsider.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/4/4c/Moonchild_Token.png"
        self._art_link_cropped = "https://imgur.com/iVnwFvV.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Moonchild"

        self._role_enum = BMRRole.moonchild
        self._emoji = emojis["badmoonrising"]["moonchild"]

