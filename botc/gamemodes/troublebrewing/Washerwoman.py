"""Contains the Washerwoman Character class"""

import json 
import discord
import random
import datetime
import configparser
from botc import Townsfolk, Character, Category, NonRecurringAction, BOTCUtils
from ._utils import TroubleBrewing, TBRole
import globvars

with open('botc/gamemodes/troublebrewing/character_text.json') as json_file: 
    character_text = json.load(json_file)[TBRole.washerwoman.value.lower()]

with open('botc/game_text.json') as json_file: 
    strings = json.load(json_file)
    washerwoman_init = strings["gameplay"]["washerwoman_init"]
    copyrights_str = strings["misc"]["copyrights"]

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Washerwoman(Townsfolk, TroubleBrewing, Character, NonRecurringAction):
    """Washerwoman: You start knowing 1 of 2 players is a particular Townsfolk.

    ===== WASHERWOMAN ===== 

    true_self = washerwoman
    ego_self = washerwoman
    social_self = washerwoman

    commands:
    - None

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send passive initial information

    ----- Regular night
    START:
    override regular night instruction -> NO  # default is to send nothing
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
        self._action = character_text["action"]
        
        self._art_link = "https://bloodontheclocktower.com/wiki/images/4/4d/Washerwoman_Token.png"
        self._art_link_cropped = "https://imgur.com/nxfAxGm.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Washerwoman"

        self._role_enum = TBRole.washerwoman
        self._emoji = "<:tbwasherwoman:739317350884442112>"

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
    
    async def send_n1_end_message(self, recipient):
        """Send two possible players for a particular townsfolk character."""

        if DISABLE_DMS:
            return

        player = BOTCUtils.get_player_from_id(recipient.id)

        # Dead players do not receive anything
        if not player.is_alive():
            return 

        # Poisoned info
        if player.is_droisoned():
            two_player_list = self.__create_droisoned_info(player)
        # Good info
        else:
            two_player_list = self.get_two_possible_townsfolks(recipient)

        registered_townsfolk_type = two_player_list[2]
        link = registered_townsfolk_type.art_link
        assert registered_townsfolk_type.category == Category.townsfolk, "Washerwoman did not receive a townsfolk character"

        # Get rid of the last element
        two_player_list.pop()

        # Construct the message to send
        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += washerwoman_init.format(registered_townsfolk_type.name)
        msg += "```basic\n"
        msg += f"{two_player_list[0].user.display_name} ({two_player_list[0].user.id})\n"
        msg += f"{two_player_list[1].user.display_name} ({two_player_list[1].user.id})\n"
        msg += "```"

        embed = discord.Embed(description = msg)
        embed.set_thumbnail(url = link)
        embed.set_footer(text = copyrights_str)
        embed.timestamp = datetime.datetime.utcnow()

        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            pass
    
    def __create_droisoned_info(self, washerwoman_player):
        """Create the droisoned info for washerwoman"""

        # Choosing townsfolk type
        tb_townsfolk_all = BOTCUtils.get_role_list(TroubleBrewing, Townsfolk)
        registered_townsfolk_type = random.choice(tb_townsfolk_all)

        # Choosing candidates
        candidates = [player for player in globvars.master_state.game.sitting_order 
                      if player.user.id != washerwoman_player.user.id]
        random.shuffle(candidates)
        candidate_1 = candidates.pop()
        candidate_2 = candidates.pop()

        return [candidate_1, candidate_2, registered_townsfolk_type]
    
    def get_two_possible_townsfolks(self, recipient):
        """Send two possible townsfolks"""

        # First set the social self
        for player in globvars.master_state.game.sitting_order:
            player.role.set_new_social_self(player)

        # Choose the player that registers as townsfolk
        townsfolks = []
        for player in globvars.master_state.game.sitting_order:
            if player.role.social_self.category == Category.townsfolk and player.user.id != recipient.id:
                townsfolks.append(player)
        random.shuffle(townsfolks)
        townsfolk = townsfolks.pop()
        registered_townsfolk_type = townsfolk.role.social_self

        # Choose the other player
        other_possibilities = [player for player in globvars.master_state.game.sitting_order 
                               if player.user.id != townsfolk.user.id and player.user.id != recipient.id]
        other = random.choice(other_possibilities)
        
        two_player_list = [townsfolk, other]
        random.shuffle(two_player_list)
        two_player_list.append(registered_townsfolk_type)

        globvars.logging.info(f">>> Washerwoman: Sent {townsfolk} and {other} as {registered_townsfolk_type}")

        return two_player_list
