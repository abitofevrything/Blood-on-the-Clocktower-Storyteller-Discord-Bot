"""Contains the Snake Charmer Character class"""

import json

from botc import Character, Townsfolk

from ._utils import SectsAndViolets, SnVRole

from . import character_texts
character_text = character_texts[SnVRole.snakecharmer.value.lower()]


class SnakeCharmer(Townsfolk, SectsAndViolets, Character):
    """Snake Charmer: Each night, choose an alive player: a chosen Demon swaps characters & alignments with you & is then poisoned.
    """

    def __init__(self):

        Character.__init__(self)
        SectsAndViolets.__init__(self)
        Townsfolk.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/6/65/Snake_Charmer_Token.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Snake_Charmer"

        self._role_enum = SnVRole.snakecharmer
