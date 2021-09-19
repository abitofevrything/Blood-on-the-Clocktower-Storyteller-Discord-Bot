"""Contains the Grandmother Character class"""

import datetime
import json
import random

import discord

import globvars
from botc import (AlreadyDead, Character, NonRecurringAction, StatusList,
                  Townsfolk, game_text)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.grandmother.value.lower()]

from botc import emojis

copyrights_str = game_text["misc"]["copyrights"]

class Grandmother(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Grandmother: You start knowing a good player & character. If the Demon kills them, you die too.

    ===== GRANDMOTHER ===== 

    true_self = grandmother
    ego_self = grandmother
    social_self = grandmother

    commands:

    initialize setup? -> NO
    initialize role? -> YES
                     => Choose grandchild

    ----- First night
    START:
    override first night instruction? -> NO

    END:
    override first night end? -> YES
                              => Send grandchild and role

    ----- Regular night
    START:
    override regular night instruction? -> NO

    END:
    override regular night end? -> YES
                                => Trigger death if necessary
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/3/3a/Grandmother_Token.png"
        self._art_link_cropped = "https://imgur.com/goIkjnU.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Grandmother"

        self._role_enum = BMRRole.grandmother
        self._emoji = emojis["badmoonrising"]["grandmother"]

        self._grandchild = None # Player object representing the grandmother's grandchild
        
    def exec_init_role(self, setup):
        choices = []
        for role in setup.role_dict:
            player = setup.role_dict[role]
            if player.role.social_self.is_good() and not player.role.true_self.name == BMRRole.grandmother.value:
                choices.append(player)

        self._grandchild = random.choice(choices)

        globvars.master_state.game.replay += f"- {self._grandchild.user.name} ({self._grandchild.role.name}) is the grandmother's grandchild.\n"

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

    async def send_n1_end_message(self, recipient):
        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += character_text["feedback"].format(self._grandchild.game_nametag, self._grandchild.role.social_self.name)
        embed = discord.Embed(description=msg)


        embed.set_thumbnail(url=self._art_link_cropped)
        embed.set_footer(text = copyrights_str)
        embed.timestamp = datetime.datetime.utcnow()

        try:
            await recipient.send(embed=embed)
        except discord.Forbidden:
            pass
