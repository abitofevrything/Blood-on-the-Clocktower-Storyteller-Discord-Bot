"""Contains the Witch Character class"""

import json

from botc import Character, Minion

from . import character_texts
from ._utils import SectsAndViolets, SnVRole

character_text = character_texts[SnVRole.witch.value.lower()]


class Witch(Minion, SectsAndViolets, Character):
    """Witch: Each night, choose a player: if they nominate tomorrow, they die. If just 3 players live, you lose this ability.
    """

    def __init__(self):

        Character.__init__(self)
        SectsAndViolets.__init__(self)
        Minion.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/c/cc/Witch_Token.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Witch"

        self._role_enum = SnVRole.witch
