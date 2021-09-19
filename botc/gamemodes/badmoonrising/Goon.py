"""Contains the Goon Character class"""

import json

import discord
import toml

import globvars
from botc import (Character, Drunkenness, Flags, Inventory, Outsider,
                  RecurringAction)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.goon.value.lower()]

from botc import emojis
from config import DISABLE_DMS


class Goon(Outsider, BadMoonRising, Character, RecurringAction):
    """Goon: Each night, the 1st player to choose you with their ability is drunk until dusk. 
    You become their alignment.

    ===== GOON ===== 

    true_self = goon
    ego_self = goon
    social_self = goon

    commands:

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> NO

    ON_BEING_TARGETED:
    override regular behaviour? -> YES # Default is to do nothing
                                => Send the new alignement to the Goon
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/a/a4/Goon_Token.png"
        self._art_link_cropped = "https://imgur.com/NaRvjH3.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Goon"

        self._role_enum = BMRRole.goon
        self._emoji = emojis["badmoonrising"]["goon"]

        self.registered_as_good = True
        self.previous_registered_as_good = True

        self.inventory = Inventory(
            Flags.goon_alignement_take
        )

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

    def is_good(self):
        return self.registered_as_good

    def is_evil(self):
        return not self.registered_as_good

    async def process_dawn_ability(self, player):
        # Restore the flag back to the goon
        self.inventory.add_item_to_inventory(Flags.goon_alignement_take)

    async def on_being_targeted(self, target_player, action):
        if self.inventory.has_item_in_inventory(Flags.goon_alignement_take):
            self.inventory.remove_item_from_inventory(Flags.goon_alignement_take)

            self.registered_as_good = action.source_player.role.true_self.is_good()

            action.source_player.add_status_effect(Drunkenness(target_player, action.source_player))

            globvars.master_state.game.replay += f"- {target_player.user.name} (Goon) becomes {'good' if self.registered_as_good else 'evil'} after being targeted by "\
                f"{action.source_player.user.name} ({action.source_player.role.name})\n"

            if DISABLE_DMS:
                return

            if self.registered_as_good != self.previous_registered_as_good:
                self.previous_registered_as_good = self.registered_as_good
                try:
                    await target_player.user.send(character_text["feedback"].format("good" if self.registered_as_good else "evil"))
                except discord.Forbidden:
                    pass

    async def send_n1_end_message(self, recipient):
        pass

    async def send_regular_night_start_dm(self, recipient):
        pass
