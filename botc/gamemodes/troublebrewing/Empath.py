"""Contains the Empath Character class"""

import json 
import discord
import datetime
import random
import configparser
from botc import Townsfolk, Character, BOTCUtils, NonRecurringAction
from ._utils import TroubleBrewing, TBRole
import botutils

with open('botc/gamemodes/troublebrewing/character_text.json') as json_file: 
    character_text = json.load(json_file)[TBRole.empath.value.lower()]

with open('botc/game_text.json') as json_file: 
    strings = json.load(json_file)
    empath_nightly = strings["gameplay"]["empath_nightly"]
    copyrights_str = strings["misc"]["copyrights"]

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Empath(Townsfolk, TroubleBrewing, Character, NonRecurringAction):
    """Empath: Each night, you learn how many of your 2 alive neighbors are evil.
    
    ===== EMPATH ===== 

    true_self = empath
    ego_self = empath
    social_self = empath

    commands:
    - None

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send nightly passive information
    
    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send nightly passive information
    """
    
    def __init__(self):

        Character.__init__(self)
        TroubleBrewing.__init__(self)
        Townsfolk.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/6/61/Empath_Token.png"
        self._art_link_cropped = "https://imgur.com/ZMC23sQ.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Empath"

        self._role_enum = TBRole.empath
        self._emoji = emojis["troublebrewing"]["empath"]

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
    
    def __create_droisoned_info(self):
        """Create drunk/poisoned information for the empath info"""

        import globvars
        nb_evils = random.choice(range(3))
        log_msg = f">>> Empath: [droisoned] {nb_evils} alive evil neighbours"
        globvars.logging.info(log_msg)
        return nb_evils
    
    async def send_n1_end_message(self, recipient):
        """Send the number of pairs of evils sitting together."""

        if DISABLE_DMS:
            return

        from botc.BOTCUtils import get_number_image

        player = BOTCUtils.get_player_from_id(recipient.id)

        # Dead players do not receive anything
        if not player.is_alive():
            return 

        # Poisoned info
        if player.is_droisoned():
            evil_pair_count = self.__create_droisoned_info()
        # Good info
        else:
            evil_pair_count = self.get_nb_evil_neighbours(recipient)
        link = get_number_image(evil_pair_count)

        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += empath_nightly.format(evil_pair_count)

        embed = discord.Embed(description = msg)
        embed.set_thumbnail(url = link)
        embed.set_footer(text = copyrights_str)
        embed.timestamp = datetime.datetime.utcnow()

        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            pass
    
    async def send_regular_night_end_dm(self, recipient):
        """Send the number of pairs of evils sitting together."""

        await self.send_n1_end_message(recipient)
    
    def get_nb_evil_neighbours(self, recipient):
        """Send the number of alive evil neighbours"""

        import globvars

        # Find all alive players
        alive_players = [player for player in globvars.master_state.game.sitting_order 
                         if player.is_apparently_alive()]
        
        # Find where the empath is seated
        seat_idx = -1
        for i, player in enumerate(alive_players):
            if player.user.id == recipient.id:
                seat_idx = i
                break
        assert seat_idx >= 0, "Something went wrong in Empath [send_first_night_instruction]"

        # Find the empath's neighbours
        nb_alives = len(alive_players)
        prev_neighbour = alive_players[(seat_idx - 1) % nb_alives]
        next_neighbour = alive_players[(seat_idx + 1) % nb_alives]

        # Find the number of alive evils
        nb_evils = 0
        prev_neighbour.role.set_new_social_self(prev_neighbour)
        next_neighbour.role.set_new_social_self(next_neighbour)
        if prev_neighbour.role.social_self.is_evil():
            nb_evils += 1
        if next_neighbour.role.social_self.is_evil():
            nb_evils += 1
        
        log_msg = f">>> Empath: {nb_evils} alive evil neighbours"
        globvars.logging.info(log_msg)
        
        return nb_evils
