"""Contains the Tea Lady Character class"""

import json

from botc import Character, NonRecurringAction, Townsfolk
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.tealady.value.lower()]

from botc import emojis


class TeaLady(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Tea Lady: If both your alive neighbors are good, they can not die.

    ===== TEA LADY =====

    true_self = tea lady
    ego_self = tea lady
    social_self = tea lady

    commands:
    - kill <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send 3 demon bluffs
                                      => Send demon and minion identities to this minion if 7 players or more

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "kill" command
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/e/e7/Tea_Lady_Token.png"
        self._art_link_cropped = "https://imgur.com/oEHE6oQ.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Tea_Lady"

        self._role_enum = BMRRole.tealady
        self._emoji = emojis["badmoonrising"]["tealady"]
    
    def create_n1_instr_str(self):
        """Create the instruction field on the opening dm card"""

        # First line is the character instruction string
        msg = f"{self.emoji} {self.instruction}"
        addendum = character_text["n1_addendum"]
        
        # Some characters have a line of addendum
        if addendum:
            scroll_emoji = BotEmoji.scroll
            msg += f"\n{scroll_emoji} {addendum}"
            
        return msg
