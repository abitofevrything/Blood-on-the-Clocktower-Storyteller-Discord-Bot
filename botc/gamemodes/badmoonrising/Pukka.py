"""Contains the Pukka Character class"""

import random
import json
from botc import Character, Demon, BOTCUtils, Townsfolk, Outsider
from ._utils import BadMoonRising, BMRRole
import botutils
import globvars

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.pukka.value.lower()]

with open('botc/game_text.json') as json_file: 
    strings = json.load(json_file)
    demon_bluff_str = strings["gameplay"]["demonbluffs"]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)


class Pukka(Demon, BadMoonRising, Character):
    """Pukka: Each night, choose a player: they are poisoned until tomorrow night, then die. 
    You act on the first night.
    """

    def __init__(self):

        Character.__init__(self)
        BadMoonRising.__init__(self)
        Demon.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/9/90/Pukka_Token.png"
        self._art_link_cropped = "https://imgur.com/vg3nwAN.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Pukka"

        self._role_enum = BMRRole.pukka
        self._emoji = emojis["badmoonrising"]["pukka"]
    
    def create_n1_instr_str(self):
        """Create the instruction field on the opening dm card"""
        
        # First line is the character instruction string
        msg = f"{self.emoji} {self.instruction}" 
        addendum = character_text["n1_addendum"]

        # Some characters have a line of addendum
        if addendum:
            scroll_emoji = botutils.BotEmoji.scroll
            msg += f"\n{scroll_emoji} {addendum}"

        # Seven or more players, send the evil list and three demon bluffs
        if globvars.master_state.game.nb_players >= 7:
            bluffs = self.get_demon_bluffs()
            msg += f"\n{self.demon_head_emoji} {demon_bluff_str.format(bluffs[0], bluffs[1], bluffs[2])}"

        return msg
    
    def get_demon_bluffs(self):
        """Get the list of 3 demon bluffs"""

        # 3 demon bluffs: 2 townsfolk characters + 1 outsider character
        # Exclusing all characters taken by other players, as well as the drunk's ego_self
        all_townsfolks = BOTCUtils.get_role_list(BadMoonRising, Townsfolk)
        all_outsiders = BOTCUtils.get_role_list(BadMoonRising, Outsider)
        taken_townsfolks = [player.role.name for player in globvars.master_state.game.setup.townsfolks]
        taken_outsiders = [player.role.name for player in globvars.master_state.game.setup.outsiders]

        possible_townsfolk_bluffs = [character for character in all_townsfolks 
                                        if character.name not in taken_townsfolks]
        possible_outsider_bluffs = [character for character in all_outsiders 
                                    if character.name not in taken_outsiders]
        random.shuffle(possible_townsfolk_bluffs)
        random.shuffle(possible_outsider_bluffs)

        # For the first two bluffs, we want a townsfolk, definitely
        bluff_1 = possible_townsfolk_bluffs.pop()
        bluff_2 = possible_townsfolk_bluffs.pop()

        # For the third bluff, if the outsider list is not empty, we will take an outsider. Otherwise
        # it's 40% chance outsider, 60% chance townsfolk
        if possible_outsider_bluffs:
            town_or_out = random.choices(
                ["t", "o"],
                weights=[0.6, 0.4]
            )
            if town_or_out[0] == "t":
                bluff_3 = possible_townsfolk_bluffs.pop()
            else:
                bluff_3 = possible_outsider_bluffs.pop()
        else:
            bluff_3 = possible_townsfolk_bluffs.pop()

        globvars.logging.info(f">>> Pukka: Received three demon bluffs {bluff_1}, {bluff_2} and {bluff_3}.")
        return (bluff_1, bluff_2, bluff_3)
