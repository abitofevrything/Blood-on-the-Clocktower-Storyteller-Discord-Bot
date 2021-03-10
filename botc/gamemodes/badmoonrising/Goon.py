"""Contains the Goon Character class"""

import json
from botc import Character, Outsider, RecurringAction, Inventory, Flags
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.goon.value.lower()]


class Goon(Outsider, BadMoonRising, Character, RecurringAction):
    """Goon: Each night, the 1st player to choose you with their ability is drunk until dusk. 
    You become their alignment.
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
        self._emoji = "<:bmrgoon:781151556330192966>"

        self.registered_as_good = True

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
            with open("botutils/bot_text.json") as json_file:
                bot_text = json.load(json_file)
                scroll_emoji = bot_text["esthetics"]["scroll"]
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
        print(f"Goon: targeted action {action}")

        if self.inventory.has_item_in_inventory(Flags.goon_alignement_take):
            self.inventory.remove_item_from_inventory(Flags.goon_alignement_take)

            self.registered_as_good = action.source_player.role.true_self.is_good()

            print(f"Goon: registered as good? {self.registered_as_good}")

    async def send_n1_end_message(self, recipient):
        pass

    async def send_regular_night_start_dm(self, recipient):
        pass