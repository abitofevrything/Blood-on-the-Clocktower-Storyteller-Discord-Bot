"""Contains the Washerwoman Character class"""

import datetime
import json
import random

import discord
import toml

import botutils
import globvars
from botc import (BOTCUtils, Category, Character, NonRecurringAction,
                  Townsfolk, emojis, game_text)
from botc.gamemodes.troublebrewing.Drunk import Drunk

from . import character_texts
from ._utils import TBRole, TroubleBrewing

character_text = character_texts[TBRole.washerwoman.value.lower()]

washerwoman_init = game_text["gameplay"]["washerwoman_init"]
copyrights_str = game_text["misc"]["copyrights"]

from config import DISABLE_DMS


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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/4/4d/Washerwoman_Token.png"
        self._art_link_cropped = "https://imgur.com/nxfAxGm.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Washerwoman"

        self._role_enum = TBRole.washerwoman
        self._emoji = emojis["troublebrewing"]["washerwoman"]

        self.two_player_list = []
        self.registered_townsfolk_type = None

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
        """Send two possible players for a particular townsfolk character."""

        if DISABLE_DMS:
            return

        link = self.registered_townsfolk_type.art_link

        # Construct the message to send
        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += washerwoman_init.format(self.registered_townsfolk_type.name)
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
        two_player_list.append(registered_townsfolk_type)

        globvars.logging.info(f">>> Washerwoman: Sent {townsfolk} and {other} as {registered_townsfolk_type}")

        return two_player_list

    async def process_night_ability(self, player):
        # Dead players do not receive anything
        if not player.is_alive():
            return

        # Poisoned info
        if player.is_droisoned():
            self.two_player_list = self.__create_droisoned_info(player)
        # Good info
        else:
            self.two_player_list = self.get_two_possible_townsfolks(player.user)

        # Get rid of the last element
        self.registered_townsfolk_type = self.two_player_list.pop()

        self.two_player_list[0].add_reminder_token('botc/assets/tb_reminder_tokens_cropped/washerwoman_townsfolk.png')
        self.two_player_list[1].add_reminder_token('botc/assets/tb_reminder_tokens_cropped/washerwoman_wrong.png')

        random.shuffle(self.two_player_list)
        assert self.registered_townsfolk_type.category == Category.townsfolk, "Washerwoman did not receive a townsfolk character"

        # Add information to replay
        drunk = "Drunk " if player.role.true_self.name == Drunk().name else ""
        globvars.master_state.game.replay += f"- {player.user.name} ({drunk}Washerwoman) knows that "\
                        f"{self.two_player_list[0].user.name} ({self.two_player_list[0].role.true_self}) or "\
                        f"{self.two_player_list[1].user.name} ({self.two_player_list[1].role.true_self}) is "\
                        f"{self.registered_townsfolk_type}\n"