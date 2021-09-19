"""Contains the Minstrel Character class"""

import json

import globvars
from botc import (Category, Character, Drunkenness, NonRecurringAction,
                  Townsfolk)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.minstrel.value.lower()]

from botc import emojis


class Minstrel(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Minstrel: If a Minion died today, all other players (except Travelers) are drunk that 
    night until dusk.

    ===== MINSTREL ===== 

    true_self = minstrel
    ego_self = minstrel
    social_self = minstrel

    commands:

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "poison" command if the player has not used their ability yet
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/0/03/Minstrel_Token.png"
        self._art_link_cropped = "https://imgur.com/3lmSmQp.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Minstrel"

        self._role_enum = BMRRole.minstrel
        self._emoji = emojis["badmoonrising"]["minstrel"]
        
        # Minions that have already died go here, as to not trigger the ability twice
        self.registered_dead_minions = list() # Player obj
        
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

    async def process_night_ability(self, minstrel_player):
        #Check if a minion died today. If so, make everyone drunk
        dead_today_minions = [
            p for p in globvars.master_state.game.player_obj_list if p.is_dead() \
            and p.role.social_self.category == Category.minion \
            and p not in self.registered_dead_minions\
        ]

        if len(dead_today_minions) == 0:
            return
        
        success = "unsuccessfully "

        if not minstrel_player.is_droisoned() and minstrel_player.is_alive():

            success = ""
            minstrel_player.role.true_self.registered_dead_minions += dead_today_minions

            to_make_drunk = [
                p for p in globvars.master_state.game.player_obj_list if \
                p.is_alive() \
                and not p.user.id == minstrel_player.user.id\
            ]

            for p in to_make_drunk:
                p.add_status_effect(Drunkenness(minstrel_player, p))

        globvars.master_state.game.replay += f"- {minstrel_player.user.name} (Minstrel) {success}makes everyone drunk\n"
