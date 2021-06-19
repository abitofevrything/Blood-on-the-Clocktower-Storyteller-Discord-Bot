"""Contains the Spy Character class"""

import datetime
import json
import random

import discord
import toml

import botutils
import globvars
from botc import (BOTCUtils, Character, Minion, NonRecurringAction, Outsider,
                  Townsfolk, emojis, game_text)
from config import DISABLE_DMS, GRIMOIRE_SHOW_TIME

from . import character_texts
from ._utils import TBRole, TroubleBrewing

character_text = character_texts[TBRole.spy.value.lower()]

copyrights_str = game_text["misc"]["copyrights"]
spy_nightly = game_text["gameplay"]["spy_nightly"]


class Spy(Minion, TroubleBrewing, Character, NonRecurringAction):
    """Spy: The Spy might appear to be a good character, but is actually evil.
    They also see the Grimoire, so they know the characters (and status) of all players.

    ===== SPY =====

    true_self = spy
    ego_self = spy
    social_self = [townsfolk] / [outsider] / spy *ephemeral

    commands:
    - None

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send demon and minion identities to this minion if 7 players or more

    ----- Regular night
    START:
    override regular night instruction? -> NO  # default is to send nothing
    """

    def __init__(self):

        Character.__init__(self)
        TroubleBrewing.__init__(self)
        Minion.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/3/31/Spy_Token.png"
        self._art_link_cropped = "https://imgur.com/Je21heV.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Spy"

        self._role_enum = TBRole.spy
        self._emoji = emojis["troublebrewing"]["spy"]

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
        The spy may register as a townsfolk, an outsider, or as spy, even if dead.
        """

        # The spy may register as good, or as spy, even if dead, except when poisoned
        if not player.is_droisoned():
            possibilities = [role_class() for role_class in TroubleBrewing.__subclasses__()
                            if issubclass(role_class, Townsfolk) or issubclass(role_class, Outsider)]
            possibilities.append(Spy())
            random.shuffle(possibilities)
            chosen = random.choice(possibilities)
            self._social_role = chosen
            globvars.logging.info(f">>> Spy [social_self] Registered as {chosen}.")

            # Add information to replay
            globvars.master_state.game.replay += f"- {player.user.name} (Spy) registers as {chosen}\n"

        else:
            self._social_role = Spy()
            globvars.logging.info(f">>> Spy [social_self] Registered as {Spy()}.")

            # Add information to replay
            globvars.master_state.game.replay += f"- {player.user.name} (Spy) unsuccessfully registers\n"

    async def __send_grimoire(self, recipient):
        """Send the spy grimoire"""

        if DISABLE_DMS:
            return

        from botc import Grimoire
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: Grimoire.create(globvars.master_state.game))
        except Exception as e:
            print("Grimoire image was not able to be generated: " + str(e))

        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += spy_nightly

        embed = discord.Embed(description = msg)
        file = discord.File(Grimoire.GRIMOIRE_PATH, filename="grimoire.png")
        embed.set_image(url="attachment://grimoire.png")
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text = copyrights_str)

        try:
            await recipient.send(file = file, embed = embed, delete_after = GRIMOIRE_SHOW_TIME)

        except discord.Forbidden:
            pass

    async def send_n1_end_message(self, recipient):
        """Send the spy grimoire"""
        player = BOTCUtils.get_player_from_id(recipient.id)
        if player.is_alive():
            await self.__send_grimoire(recipient)

    async def send_regular_night_end_dm(self, recipient):
        """Send the spy grimoire"""
        player = BOTCUtils.get_player_from_id(recipient.id)
        if player.is_alive():
            await self.__send_grimoire(recipient)
