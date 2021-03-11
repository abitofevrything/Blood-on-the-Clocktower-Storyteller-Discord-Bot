"""Contains the Mastermind Character class"""

import json
from botc import Character, Minion, NonRecurringAction
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.mastermind.value.lower()]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


class Mastermind(Minion, BadMoonRising, Character, NonRecurringAction):
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
        
    def create_n1_instr_str(self):
        return "not_implemented"      
