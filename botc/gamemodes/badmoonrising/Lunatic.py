"""Contains the Lunatic Character class"""

import json
import random

import globvars
from botc import (Character, Drunkenness, NonRecurringAction, Outsider,
                  Storyteller)

from . import character_texts
from ._utils import BadMoonRising, BMRRole
from .Po import Po
from .Pukka import Pukka
from .Shabaloth import Shabaloth
from .Zombuul import Zombuul

character_text = character_texts[BMRRole.lunatic.value.lower()]

from botc import emojis


class Lunatic(Outsider, BadMoonRising, Character, NonRecurringAction):
    """Lunatic: You think you are a Demon, but your abilities malfunction. 
    The Demon knows who you are & who you attack.

    ===== LUNATIC ===== 

    true_self = lunatic
    ego_self = demon
    social_self = lunatic

    commands:

    initialize setup? -> NO
    initialize role? -> YES
                     => Poison all Lunatics the their ability malfunctions

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> NO
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

    def exec_init_role(self, setup):
        self._ego_role = random.choice([Po, Pukka, Shabaloth, Zombuul])()
        globvars.logging.info(f">>> Lunatic [exec_init_role] Initialized ego_self as {self._ego_role}.")

        for player in setup.outsiders:
            if player.role.true_self.name == BMRRole.lunatic.value:
                player.add_status_effect(Drunkenness(Storyteller(), player, None, float("inf")))
