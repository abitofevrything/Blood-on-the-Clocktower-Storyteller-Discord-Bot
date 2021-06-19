"""Contains the Courtier Character class"""

import json

from botc import Character, Townsfolk

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.courtier.value.lower()]

from botc import emojis


class Courtier(Townsfolk, BadMoonRising, Character):
    """Courtier: Once per game, at night, choose a character: they are drunk for 3 nights & 3 days.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/7/7d/Courtier_Token.png"
        self._art_link_cropped = "https://imgur.com/c1wt8jB.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Courtier"

        self._role_enum = BMRRole.courtier
        self._emoji = emojis["badmoonrising"]["courtier"]
