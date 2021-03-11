"""Contains the Recluse Character class"""

import json 
import random
from botc import Outsider, Character, Minion, Demon, NonRecurringAction
from ._utils import TroubleBrewing, TBRole
import botutils
import globvars

with open('botc/gamemodes/troublebrewing/character_text.json') as json_file: 
    character_text = json.load(json_file)[TBRole.recluse.value.lower()]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


class Recluse(Outsider, TroubleBrewing, Character, NonRecurringAction):
    """Recluse: You might register as evil & as a Minion or Demon, even if dead.

    ===== RECLUSE ===== 

    true_self = recluse
    ego_self = recluse
    social_self = [minion] / [demon] / recluse *ephemeral

    commands:
    - None

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO  # default is to send instruction string only

    ----- Regular night
    START:
    override regular night instruction? -> NO  # default is to send nothing
    """

    def __init__(self):
        
        Character.__init__(self)
        TroubleBrewing.__init__(self)
        Outsider.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]
        
        self._art_link = "https://bloodontheclocktower.com/wiki/images/b/bb/Recluse_Token.png"
        self._art_link_cropped = "https://imgur.com/9VMElqP.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Recluse"

        self._role_enum = TBRole.recluse
        self._emoji = emojis["troublebrewing"]["recluse"]

    def create_n1_instr_str(self):
        """Create the instruction field on the opening dm card"""

        # First line is the character instruction string
        msg = f"{self.emoji} {self.instruction}"
        addendum = character_text["n1_addendum"]
        
        # Some characters have a line of addendum
        if addendum:
            scroll_emoji = botutils.BotEmoji.scroll
            msg += f"\n{scroll_emoji} {addendum}"
            
        return msg
    
    def set_new_social_self(self, player):
        """Social self: what the other players think he is.
        The recluse may register as a demon, a minion, or as recluse.
        """
        possibilities = [role_class() for role_class in TroubleBrewing.__subclasses__()
                        if issubclass(role_class, Demon) or issubclass(role_class, Minion)]
        possibilities.append(Recluse())
        chosen = random.choice(possibilities)
        self._social_role = chosen
        globvars.logging.info(f">>> Recluse [social_self] Registered as {chosen}.")
