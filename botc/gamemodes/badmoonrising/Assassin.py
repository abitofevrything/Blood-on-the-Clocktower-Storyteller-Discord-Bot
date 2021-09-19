"""Contains the Assassin Character class"""

import datetime
import json

import discord
import toml

import globvars
from botc import (Action, ActionTypes, Character, Flags, Inventory, Minion,
                  NonRecurringAction, StatusList, game_text)
from botc.BOTCUtils import BOTCUtils, GameLogic
from botc.errors import AlreadyDead
from botutils import BotEmoji, bot_text
from config import DISABLE_DMS

from ._utils import BadMoonRising, BMRRole

copyrights_str = game_text["misc"]["copyrights"]

butterfly = BotEmoji.butterfly

from . import character_texts

character_text = character_texts[BMRRole.assassin.value.lower()]

from botc import emojis


class Assassin(Minion, BadMoonRising, Character, NonRecurringAction):
    """Assassin: Once per game, at night*, choose a player: they die, even if for some reason they could not.

    ===== ASSASSIN ===== 

    true_self = assassin
    ego_self = assassin
    social_self = assassin

    commands:
    - assassinate <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send demon and minion identities to this minion if 7 players or more

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "assasinate" command if ability has not been used
    """

    def __init__(self):

        Character.__init__(self)
        BadMoonRising.__init__(self)
        Minion.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/e/e0/Assassin_Token.png"
        self._art_link_cropped = "https://imgur.com/aiJxUkC.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Assassin"

        self._role_enum = BMRRole.assassin
        self._emoji = emojis["badmoonrising"]["assassin"]

        self.inventory = Inventory(
            Flags.assassin_unique_kill
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
    
    def add_action_field_n1(self, embed_obj):
        """Send the stats list n1"""

        msg = self.action
        msg += globvars.master_state.game.create_sitting_order_stats_string()
        embed_obj.add_field(name = butterfly + " **「 Your Action 」**", value = msg, inline = False)
        return embed_obj

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""

        if DISABLE_DMS:
            return

        import globvars

        player = BOTCUtils.get_player_from_id(recipient.id)

        if not player.role.ego_self.inventory.has_item_in_inventory(Flags.assassin_unique_kill):
            return

        if player.is_alive():

            # Construct the message to send
            msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
            msg += "\n"
            msg += self.emoji + " " + self.instruction
            msg += "\n"

            embed = discord.Embed(description = msg)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text = copyrights_str)

            msg2 = self.action
            msg2 += globvars.master_state.game.create_sitting_order_stats_string()
            embed.add_field(name = butterfly + " **「 Your Action 」**", value = msg2, inline = False)
            
            try:
                await recipient.send(embed = embed)
            except discord.Forbidden:
                pass

    @GameLogic.unique_ability(ActionTypes.assassinate)
    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    @GameLogic.except_first_night
    async def register_assassinate(self, player, targets):
        """Assasinate command
        @player : Player object
        @target : Target object
        """
        
        # Must be one target
        assert len(targets) == 1, "Received a number of targets different than 1 for assassin 'assasinate'"
        action = Action(player, targets, ActionTypes.assassinate, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_assassinate(self, assassin_player, killed_player):
        """Execute the assasinate action (night ability interaction)"""

        assassin_player.role.ego_self.inventory.remove_item_from_inventory(Flags.assassin_unique_kill)

        success = "unsuccessfully "

        if assassin_player.is_alive() and next((e for e in assassin_player.status_effects if (e.effect == StatusList.poison or \
            e.effect == StatusList.drunkenness) and e.source_player.role.true_self.role.name is not BMRRole.goon.value and e.is_active()), None) == None \
            and not assassin_player.is_droisoned():
            success = ""
            try:
                await killed_player.exec_real_death()
            except AlreadyDead:
                pass
            else:
                globvars.master_state.game.night_deaths.append(killed_player)

        globvars.master_state.game.replay += f"- {assassin_player.user.name} (Assassin) {success}" \
            f"assassinates {killed_player.user.name} ({killed_player.role.true_self.name})\n"

    def has_finished_night_action(self, player):
        """Return True if assassin has submitted the assassinate action"""

        if player.is_alive():
            # First night, assassin does not act
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None
        return True

    async def process_night_ability(self, player):
        """Process night actions for the assassin player
        @player : The assassin player (Player object)
        """

        # We only do the following if the assassin is alive
        if player.is_alive():
            phase = globvars.master_state.game._chrono.phase_id
            action = player.action_grid.retrieve_an_action(phase)

            # The assassin submitted their unique kill. Kill the target player
            if action and not action.action_type == ActionTypes.ability_pass:
                assert action.action_type == ActionTypes.assassinate,  f"Wrong action type {action} in assassin"
                targets = action.target_player
                killed_player = targets[0]
                await self.exec_assassinate(player, killed_player)


