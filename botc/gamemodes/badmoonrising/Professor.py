"""Contains the Professor Character class"""

import datetime
import json

import discord
import toml

import globvars
from botc import (Action, ActionTypes, BOTCUtils, Category, Character, Flags,
                  GameLogic, Inventory, NonRecurringAction, Townsfolk,
                  game_text)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.professor.value.lower()]

from botc import emojis

copyrights_str = game_text["misc"]["copyrights"]

butterfly = BotEmoji.butterfly

from config import DISABLE_DMS


class Professor(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Professor: Once per game, at night, choose a dead player: if they are a Townsfolk, 
    they are resurrected.

    ===== PROFESSOR ===== 

    true_self = professor
    ego_self = professor
    social_self = professor

    commands:
    - examine <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "examine" command if the player has not used their ability yet
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/a/ac/Professor_Token.png"
        self._art_link_cropped = "https://imgur.com/6MN8udE.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Professor"

        self._role_enum = BMRRole.professor
        self._emoji = emojis["badmoonrising"]["professor"]

        self.inventory = Inventory(
            Flags.professor_unique_resurrect
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

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""

        if DISABLE_DMS:
            return

        import globvars

        player = BOTCUtils.get_player_from_id(recipient.id)

        if not player.role.ego_self.inventory.has_item_in_inventory(Flags.professor_unique_resurrect):
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

    def has_finished_night_action(self, player):
        """Return True if courtier has submitted the poison action"""

        if player.is_alive() and not globvars.master_state.game._chrono.is_night_1():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None
        return True

    @GameLogic.unique_ability(ActionTypes.examine)
    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    @GameLogic.requires_dead_targets    
    @GameLogic.except_first_night # It is not explicitly said that professor does not act n1, however they do not appear on the n1 night order
    async def register_examine(self, player, targets):
        """Examine command"""
        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for professor 'examine'"

        player.role.ego_self.inventory.remove_item_from_inventory(Flags.professor_unique_resurrect)

        action = Action(player, targets, ActionTypes.examine, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_examine(self, professor_player, examined_player):
        success = "unsuccessfully "
        if professor_player.is_alive() and not professor_player.is_droisoned():
            if examined_player.role.social_self.category == Category.townsfolk:
                success = ""
                await examined_player.revive()
                globvars.master_state.game.night_revives.append(examined_player)
        
        globvars.master_state.game.replay += f"- {professor_player.user.name} (Professor) {success}examines {examined_player.user.name} ({examined_player.role.name})\n"

    async def process_night_ability(self, player):
        """Process night actions for the poisoner character.
        @player : the Professor player (Player object)
        """
        
        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The professor has submitted an action. We call the execution function immediately
        if action and not action.action_type == ActionTypes.ability_pass:
            assert action.action_type == ActionTypes.examine, f"Wrong action type {action} in professor"
            poisoned_player = action.target_player[0]
            await self.exec_examine(player, poisoned_player)
        # The professor has not submitted an action.
        else:
            pass