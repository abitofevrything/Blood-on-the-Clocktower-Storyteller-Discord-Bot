"""Contains the Investigator Character class"""

import datetime
import json
import random

import discord
import toml

import botutils
import globvars
from botc import (BOTCUtils, Category, Character, Minion, NonRecurringAction,
                  Townsfolk, emojis, game_text)
from botc.gamemodes.troublebrewing.Drunk import Drunk

from . import character_texts
from ._utils import TBRole, TroubleBrewing

character_text = character_texts[TBRole.investigator.value.lower()]

investigator_init = game_text["gameplay"]["investigator_init"]
copyrights_str = game_text["misc"]["copyrights"]

from config import DISABLE_DMS


class Investigator(Townsfolk, TroubleBrewing, Character, NonRecurringAction):
    """Investigator: You start knowing 1 of 2 players is a particular Minion.

    ===== INVESTIGATOR =====

    true_self = investigator
    ego_self = investigator
    social_self = investigator

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
    override regular night instruction? -> NO  # default is to send nothing
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/e/ec/Investigator_Token.png"
        self._art_link_cropped = "https://imgur.com/9B2WNCc.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Investigator"

        self._role_enum = TBRole.investigator
        self._emoji = emojis["troublebrewing"]["investigator"]

        self.two_player_list = []
        self.registered_minion_type = None

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

    async def send_n1_end_message(self, recipient):
        """Send two possible players for a particular minion character."""

        player = BOTCUtils.get_player_from_id(recipient.id)

        if DISABLE_DMS:
            return

        # Dead players do not receive anything
        if not player.is_alive():
            return

        link = self.registered_minion_type.art_link

        # Construct the message to send
        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += investigator_init.format(self.registered_minion_type.name)
        msg += "```basic\n"
        msg += f"{self.two_player_list[0].user.display_name} ({self.two_player_list[0].user.id})\n"
        msg += f"{self.two_player_list[1].user.display_name} ({self.two_player_list[1].user.id})\n"
        msg += "```"

        embed = discord.Embed(description = msg)
        embed.set_thumbnail(url = link)
        embed.set_footer(text = copyrights_str)
        embed.timestamp = datetime.datetime.utcnow()

        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            pass

    def __create_droisoned_info(self, investigator_player):
        """Create the droisoned info for investigator"""

        # Choosing minion type
        tb_minion_all = BOTCUtils.get_role_list(TroubleBrewing, Minion)
        registered_minion_type = random.choice(tb_minion_all)

        # Choosing candidates
        candidates = [player for player in globvars.master_state.game.sitting_order
                      if player.user.id != investigator_player.user.id]
        random.shuffle(candidates)
        candidate_1 = candidates.pop()
        candidate_2 = candidates.pop()

        return [candidate_1, candidate_2, registered_minion_type]

    def get_two_possible_minions(self, investigator_player):
        """Send two possible minions"""

        # First set the social self
        for player in globvars.master_state.game.sitting_order:
            player.role.set_new_social_self(player)

        # Choose the player that registers as minion
        minions = []
        registered_minion_type = None
        for player in globvars.master_state.game.sitting_order:
            if player.role.social_self.category == Category.minion:
                minions.append(player)

        # If we found a minion
        if minions:
            random.shuffle(minions)
            minion = minions.pop()
            registered_minion_type = minion.role.social_self

        # No minion found through social self: meaning that some registered as townsfolks.
        else:
            minions = globvars.master_state.game.setup.minions
            minion = minions.pop()
            registered_minion_type = minion.role.true_self

        # Choose the other player
        other_possibilities = [player for player in globvars.master_state.game.sitting_order
                               if player.user.id != minion.user.id and player.user.id != investigator_player.user.id]
        other = random.choice(other_possibilities)

        # Construct the message
        two_player_list = [minion, other]
        two_player_list.append(registered_minion_type)

        globvars.logging.info(f">>> Investigator: Sent {minion} and {other} as {registered_minion_type}")

        return two_player_list

    async def process_night_ability(self, player):
        # Poisoned info
        if player.is_droisoned():
            self.two_player_list = self.__create_droisoned_info(player)
        # Good info
        else:
            self.two_player_list = self.get_two_possible_minions(player)
        
        self.two_player_list[0].add_reminder_token('botc/assets/tb_reminder_tokens_cropped/investigator_minion.png')
        self.two_player_list[1].add_reminder_token('botc/assets/tb_reminder_tokens_cropped/investigator_wrong.png')

        # Get rid of the last element (the minion type)
        self.registered_minion_type = self.two_player_list.pop()
        random.shuffle(self.two_player_list)
        
        assert self.registered_minion_type.category == Category.minion, f"Investigator received {self.registered_minion_type}" 

        # Add information to replay
        drunk = "Drunk " if player.role.true_self.name == Drunk().name else ""
        globvars.master_state.game.replay += f"- {player.user.name} ({drunk}Investigator) knows that "\
                        f"{self.two_player_list[0].user.name} ({self.two_player_list[0].role.true_self}) or "\
                        f"{self.two_player_list[1].user.name} ({self.two_player_list[1].role.true_self}) is "\
                        f"{self.registered_minion_type}\n"
