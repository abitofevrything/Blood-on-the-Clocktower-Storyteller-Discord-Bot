"""Contains the Lunatic Character class"""

import json
from botc import Character, Outsider, NonRecurringAction
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.lunatic.value.lower()]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


class Lunatic(Outsider, BadMoonRising, Character, NonRecurringAction):
    """Lunatic: You think you are a Demon, but your abilities malfunction. 
    The Demon knows who you are & who you attack.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/5/56/Lunatic_Token.png"
        self._art_link_cropped = "https://imgur.com/htUUx18.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Lunatic"

        self._role_enum = BMRRole.lunatic
        self._emoji = emojis["badmoonrising"]["lunatic"]
       
    def create_n1_instr_str(self):
        return "not_implemented" 
