"""Contains the Mastermind Character class"""

import json

from botc import Character, Minion

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.mastermind.value.lower()]

from botc import emojis


class Mastermind(Minion, BadMoonRising, Character):
    """Mastermind: If the Demon dies by execution, play for 1 more day. If a player
    is then executed, their team loses
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/d/d5/Mastermind_Token.png"
        self._art_link_cropped = "https://imgur.com/rM0fbDu.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Mastermind"

        self._role_enum = BMRRole.mastermind
        self._emoji = emojis["badmoonrising"]["mastermind"]

