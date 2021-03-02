"""Contains the Fool Character class"""

import json
from botc import Character, Townsfolk, NonRecurringAction, StatusList, Flags, Inventory
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.fool.value.lower()]


class Fool(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Fool: The first time you die, you don't.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/b/ba/Fool_Token.png"
        self._art_link_cropped = "https://imgur.com/nA8CXp1.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Fool"

        self._role_enum = BMRRole.fool
        self._emoji = "<:bmrfool:781151556254564353>"

        self.inventory = Inventory(
            Flags.fool_death_evasion
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

    # The following three methods are only as the last check before death,
    # so we can safely assume that we should remove the flag if these
    # methods are called

    def can_be_executed(self, player):
        """Can the player be executed?
        Default is to check whether the player has the safety_from_execution status.
        To be overriden in child classes.
        """
        if player.has_status_effect(StatusList.safety_from_execution):
            return False

        if player.role.true_self.has_item_in_inventory(Flags.fool_death_evasion):
            player.role.true_self.inventory.remove_item_from_inventory(Flags.fool_death_evasion)
            return False

        return True

    def can_be_demon_killed(self, player):
        """Can the player be demon killed?
        Default is to check if the player has the safety_from_demon status.
        To  be overriden in child classes.
        """
        if player.has_status_effect(StatusList.safety_from_demon):
            return False

        if player.role.true_self.has_item_in_inventory(Flags.fool_death_evasion):
            player.role.true_self.inventory.remove_item_from_inventory(Flags.fool_death_evasion)
            return False

        return True

    def can_be_killed(self, player):
        """Can the player be killed in any way other than execution or demon kill?
        To be overriden by child classes.
        """
        if player.role.true_self.has_item_in_inventory(Flags.fool_death_evasion):
            player.role.true_self.inventory.remove_item_from_inventory(Flags.fool_death_evasion)
            return False

        return True