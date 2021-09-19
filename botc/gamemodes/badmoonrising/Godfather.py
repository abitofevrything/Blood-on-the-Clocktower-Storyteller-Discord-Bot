"""Contains the Godfather Character class"""

import datetime
import json
import random

import discord
import toml

import botutils
import globvars
from botc import (Action, ActionTypes, AlreadyDead, BOTCUtils, Category,
                  Character, GameLogic, Minion, Outsider, RecurringAction,
                  Townsfolk, game_text)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.godfather.value.lower()]

from botc import emojis

copyrights_str = game_text["misc"]["copyrights"]

butterfly = botutils.BotEmoji.butterfly

from config import DISABLE_DMS


class Godfather(Minion, BadMoonRising, Character, RecurringAction):
    """Godfather: You start knowing which Outsiders are in-play. If 1 died today, 
    choose a player tonight: they die. [-1 or +1 Outsider]

    ===== GODFATHER ===== 

    true_self = godfather
    ego_self = godfather
    social_self = godfather

    commands:
    - execute <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send demon and minion identities to this minion if 7 players or more

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "execute" command if an outsider died today
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/e/ef/Godfather_Token.png"
        self._art_link_cropped = "https://imgur.com/7JlfMLc.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Godfather"

        self._role_enum = BMRRole.godfather
        self._emoji = emojis["badmoonrising"]["godfather"]

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

    def has_finished_night_action(self, player):
        """Return True if godfather has submitted the godfather action or if an outsider was not executed today"""
        executed_today = globvars.master_state.game.today_executed_player

        if executed_today is None:
            return True
        elif not isinstance(executed_today.role.true_self, Outsider):
            return True
        else:
            if player.is_alive():
                current_phase_id = globvars.master_state.game._chrono.phase_id
                received_action = player.action_grid.retrieve_an_action(current_phase_id)
                return received_action is not None
            return True

    async def send_n1_end_message(self, recipient):
        if DISABLE_DMS:
            return

        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n\n"

        outsiders = [
            ("the **" + p.role.social_self.name + "**") for p in globvars.master_state.game.player_obj_list \
            if p.role.social_self.category == Category.outsider
        ]

        if len(outsiders) == 0:
            msg += character_text["learn_no_outsiders"]
        else:
            if len(outsiders) == 1:
                outsider_str = outsiders[0]
            else:
                outsider_str = ", ".join(outsiders[:-1]) + ", and " + outsiders[-1]
            msg += character_text["learn_outsiders"].format(
                outsider_str,
                ("is" if len(outsiders) == 1 else "are")
            )

        globvars.master_state.game.replay += f'{BOTCUtils.get_player_from_id(recipient.id).user.name} (Godfather) learns that '\
            f'{("there are no outsiders" if len(outsiders) == 0 else (outsider_str + (" is" if len(outsiders) == 1 else " are")))} in play\n'

        embed = discord.Embed(description = msg)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text = copyrights_str)
        
        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            pass

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""

        # For godfather, only send DM if Outsider was executed today

        executed_today = globvars.master_state.game.today_executed_player

        if executed_today is None:
            return
        elif not isinstance(executed_today.role.true_self, Outsider):
            return

        player = BOTCUtils.get_player_from_id(recipient.id)

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

    def exec_init_setup(self, townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list):
        """Add or remove one outsider from the setup"""
        
        if random.choice([True, False]) or len(outsider_obj_list) == 0:
            # +1 Outsider

            townsfolk_obj_list.pop()

            bmr_outsider_all = BOTCUtils.get_role_list(BadMoonRising, Outsider)

            for outsider in bmr_outsider_all:
                if str(outsider) not in [str(role) for role in outsider_obj_list]:
                    outsider_obj_list.append(outsider)
                    break

            return [townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list]
        else:
            # -1 Outsider

            outsider_obj_list.pop()

            bmr_townsfolk_all = BOTCUtils.get_role_list(BadMoonRising, Townsfolk)

            for townsfolk in bmr_townsfolk_all:
                if str(townsfolk) not in [str(role) for role in townsfolk_obj_list]:
                    townsfolk_obj_list.append(townsfolk)
                    break

            return [townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list]

    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    async def register_execute(self, player, targets):
        """Execute command"""

        # Ignore command if godfather shouldn't execute tonight

        executed_today = globvars.master_state.game.today_executed_player

        if executed_today is None:
            return
        elif not isinstance(executed_today.role.true_self, Outsider):
            return

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for godfather 'execute'"
        action = Action(player, targets, ActionTypes.execute, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_execute(self, player, killed_player):
        success = "unsuccessfully "
        if player.is_alive() and not player.is_droisoned():
            if  killed_player.role.true_self.can_be_killed(killed_player):
                success = ""
                try:
                    await killed_player.exec_real_death()
                except AlreadyDead:
                    pass
                else:
                    globvars.master_state.game.night_deaths.append(killed_player)

        globvars.master_state.game.replay += f"- {player.user.name} (Godfather) {success}executes {killed_player.user.name} ({killed_player.role.name})\n"

    async def process_night_ability(self, player):
        """Process night actions for the exorcist character.
        @player : the Godfather player (Player object)
        """

        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The godfather has submitted an action. We call the execution function immediately
        if action and not action.action_type == ActionTypes.ability_pass:
            assert action.action_type == ActionTypes.execute, f"Wrong action type {action} in exorcist"
            targets = action.target_player
            exorcised_player = targets[0]
            await self.exec_execute(player, exorcised_player)
        # The godfather has not submitted an action. We will not randomize the action because this 
        # is a priviledged ability
        else:
            pass
