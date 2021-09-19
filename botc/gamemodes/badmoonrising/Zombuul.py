"""Contains the Zombuul Character class"""

import datetime
import json
import asyncio
import random

import discord
import toml

import botutils
import globvars
from botc import (AbilityForbidden, Action, ActionTypes, BOTCUtils, Character,
                  Demon, Flags, GameLogic, Inventory, Outsider, PlayerState,
                  RecurringAction, Category, Townsfolk, game_text)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.zombuul.value.lower()]

demon_bluff_str = game_text["gameplay"]["demonbluffs"]
action_assign = game_text["gameplay"]["action_assign"]
demon_learn_lunatic = game_text["gameplay"]["demon_learn_lunatic"]
no_killing_if_execution_str = game_text["cmd_warnings"]["no_killing_if_execution"]
copyrights_str = game_text["misc"]["copyrights"]
demon_learn_lunatic_attack = game_text["gameplay"]["demon_learn_lunatic_attack"]

from botc import emojis

x_emoji = BotEmoji.x_emoji
butterfly = BotEmoji.butterfly

from config import DISABLE_DMS, BASE_NIGHT


class NoKillingIfExecutionOccured(AbilityForbidden):
    """Class for when zombuul tries to kill when there was an execution"""
    pass

class Zombuul(Demon, BadMoonRising, Character, RecurringAction):
    """Zombuul: Each night*, if no-one died today, choose a player: they die. The 1st time you die,
    you do not, but appear to.

    ===== ZOMBUUL =====

    true_self = zombuul
    ego_self = zombuul
    social_self = zombuul

    commands:
    - kill <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send 3 demon bluffs
                                      => Send demon and minion identities to this minion if 7 players or more

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "kill" command
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/c/c6/Zombuul_Token.png"
        self._art_link_cropped = "https://imgur.com/Z84oOaA.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Zombuul"

        self._role_enum = BMRRole.zombuul
        self._emoji = emojis["badmoonrising"]["zombuul"]

        self.inventory = Inventory(
            Flags.zombuul_unique_death_escape
        )

        # Fake lunatic for lunatic
        self._fake_lunatic = None
        self._fake_lunatic_role = None
    
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

    async def send_n1_end_message(self, recipient):
        if DISABLE_DMS:
            return

        if BOTCUtils.get_player_from_id(recipient.id).role.true_self.name == BMRRole.lunatic.value:
            # Lunatic can get its own "lunatic" (which can be any player but the lunatic themselves)
            # Chance of lunatic in any game : num_outsiders / 4
            chance = len([p for p in globvars.master_state.game.sitting_order if isinstance(p.role.true_self, Outsider)]) / 4
            if random.random() < chance:
                # Send a "lunatic"
                chosen = random.choice([p for p in globvars.master_state.game.sitting_order if p.role.true_self.name is not BMRRole.lunatic.value])
                self._fake_lunatic = chosen
                from . import Po, Pukka, Shabaloth
                self._fake_lunatic_role = random.choice([Po, Pukka, Shabaloth, Zombuul])()
                try:
                    await recipient.send(demon_learn_lunatic.format(chosen.game_nametag))
                except discord.Forbidden:
                    pass
        else:
            for player in globvars.master_state.game.sitting_order:
                if player.role.social_self.name == BMRRole.lunatic.value:
                    try:
                        await recipient.send(demon_learn_lunatic.format(player.game_nametag))
                    except discord.Forbidden:
                        pass

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""

        if self._fake_lunatic and self._fake_lunatic.is_apparently_alive():
            # Player has a fake lunatic, schedule fake demon learn attack message
            async def send_fake_learn_message():
                # Send after a random amount of time
                await asyncio.sleep(random.randint(5, BASE_NIGHT - 5))

                msg = ''
                if self._fake_lunatic_role.name == BMRRole.po.value:
                    # Po: 1 kill every night except n1
                    if not globvars.master_state.game._chrono.is_night_1():
                        msg = demon_learn_lunatic_attack.format(self._fake_lunatic.game_nametag, random.choice([p for p in globvars.master_state.game.sitting_order if p.is_apparently_alive() and not p == self._fake_lunatic]).game_nametag)
                elif self._fake_lunatic_role.name == BMRRole.pukka.value:
                    # Pukka: 1 kill every night
                    msg = demon_learn_lunatic_attack.format(self._fake_lunatic.game_nametag, random.choice([p for p in globvars.master_state.game.sitting_order if p.is_apparently_alive() and not p == self._fake_lunatic]).game_nametag)
                elif self._fake_lunatic_role.name == BMRRole.shabaloth.value:
                    # Shabaloth: 2 kills every night except n1
                    if not globvars.master_state.game._chrono.is_night_1():
                        msg = demon_learn_lunatic_attack.format(self._fake_lunatic.game_nametag, ' and '.join(random.choices([p.game_nametag for p in globvars.master_state.game.sitting_order if p.is_apparently_alive() and not p == self._fake_lunatic], k=2)))
                elif self._fake_lunatic_role.name == BMRRole.zombuul.value:
                    # Zombuul: 1 kill per night except n1 and days with executions
                    if not globvars.master_state.game._chrono.is_night_1() and globvars.master_state.game.today_executed_player is None:
                        msg = demon_learn_lunatic_attack.format(self._fake_lunatic.game_nametag, random.choice([p for p in globvars.master_state.game.sitting_order if p.is_apparently_alive() and not p == self._fake_lunatic]).game_nametag)
            
                try:
                    await recipient.send(msg)
                except discord.Forbidden:
                    return

            asyncio.create_task(send_fake_learn_message())

        if globvars.master_state.game._chrono.is_night_1():
            return

        if globvars.master_state.game.today_executed_player is not None:
            return

        if DISABLE_DMS:
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

            msg2 = self._action
            msg2 += globvars.master_state.game.create_sitting_order_stats_string()
            embed.add_field(name = butterfly + " **「 Your Action 」**", value = msg2, inline = False)
            
            try:
                await recipient.send(embed = embed)
            except discord.Forbidden:
                pass
    
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

        globvars.logging.info(f">>> Zombuul: Received three demon bluffs {bluff_1}, {bluff_2} and {bluff_3}.")
        return (bluff_1, bluff_2, bluff_3)

    def has_finished_night_action(self, player):
        """Return True if imp has submitted the kill action"""

        if globvars.master_state.game.today_executed_player is not None:
            return True

        if player.is_alive():
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None
        return True

    async def send_opening_dm_embed(self, recipient):
        await super().send_opening_dm_embed(recipient)
        # Fake lunatic might be a pukka, in which case we deal with it here
        if globvars.master_state.game._chrono.is_night_1():
            await self.send_regular_night_start_dm(recipient)

    @GameLogic.except_first_night
    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    async def register_kill(self, player, targets):
        """Kill command"""

        if globvars.master_state.game.today_executed_player is not None:
            raise NoKillingIfExecutionOccured(no_killing_if_execution_str.format(player.user.mention, x_emoji))

        butterfly = botutils.BotEmoji.butterfly

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for zombuul 'kill'"
        action = Action(player, targets, ActionTypes.kill, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        if player.role.true_self.name == BMRRole.lunatic.value:
            targets_str = targets[-1].game_nametag
            if len(targets) > 1:
                targets_str = ', '.join([p.game_nametag for p in targets[:-1]]) + ' and ' + targets_str
            for p in [p for p in globvars.master_state.game.player_obj_list if p.role.true_self.category == Category.demon]:
                try:
                    await p.user.send(demon_learn_lunatic_attack.format(player.game_nametag, targets_str))
                except discord.Forbidden:
                    pass

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_kill(self, demon_player, killed_player):
        """Execute the kill action (night ability interaction)"""

        success = "unsuccessfully "
        if demon_player.is_alive() and not demon_player.is_droisoned():
            # Players who have received a status effect granting them safety from the demon
            # do not die
            if killed_player.role.true_self.can_be_demon_killed(killed_player):
                success = ""
                await killed_player.role.true_self.on_being_demon_killed(killed_player)
        
        globvars.master_state.game.replay += f"- {demon_player.user.name} ({demon_player.role.name}) {success}kills {killed_player.user.name} ({killed_player.role.name})\n"
        
    async def on_being_executed(self, executed_player):
        """Funtion that runs after the player has been executed.
        Overriding the parent behaviour.
        The first time the zombuul dies, only the fake death state is applied.
        """
        # The first time the zombuul dies
        if executed_player.is_apparently_alive() and not executed_player.is_droisoned():

            await executed_player.exec_apparent_death()
            game = globvars.master_state.game
            game.today_executed_player = executed_player

            executed_player.role.true_self.inventory.remove_item_from_inventory(Flags.zombuul_unique_death_escape)

            return

        # The second time the zombuul dies
        if (executed_player.is_alive() and executed_player.is_apparently_dead()) or executed_player.is_droisoned():

            await executed_player.exec_real_death()
            game = globvars.master_state.game
            game.today_executed_player = executed_player
            return

    def check_winning_conditions(self, player):
        # If zombuul has died by some other form but still
        # has the death escape flag, revive then but keep
        # them apparently dead
        if player.is_dead() and player.role.true_self.inventory.has_item_in_inventory(Flags.zombuul_unique_death_escape) and not player.is_droisoned():
            player.role.true_self.inventory.remove_item_from_inventory(Flags.zombuul_unique_death_escape)

            player._state_obj = PlayerState.alive

        return True

    async def process_night_ability(self, player):
        """Process night actions for the zombuul character.
        @player : the Zombuul player (Player object)
        """

        # We only do any of the following if the zombuul is alive. Otherwise skip everything.
        if player.is_alive():

            if globvars.master_state.game.today_executed_player is not None:
                return

            phase = globvars.master_state.game._chrono.phase_id
            action = player.action_grid.retrieve_an_action(phase)
            # The zombuul has submitted an action. We call the execution function immediately
            if action and not action.action_type == ActionTypes.ability_pass:
                assert action.action_type == ActionTypes.kill, f"Wrong action type {action} in zombuul"
                targets = action.target_player
                killed_player = targets[0]
                await self.exec_kill(player, killed_player)
            # The zombuul has not submitted an action. We will randomize the action and make
            # the zombuul kill one random player that is not the zombuul.
            else:
                if player.is_alive():
                    killed_player = BOTCUtils.get_random_player_excluding(player)
                    await self.exec_kill(player, killed_player)

                    if DISABLE_DMS:
                        return

                    if player.role.true_self.name == BMRRole.lunatic.value:
                        for p in [p for p in globvars.master_state.game.player_obj_list if p.role.true_self.category == Category.demon]:
                            try:
                                await p.user.send(demon_learn_lunatic_attack.format(player.game_nametag, killed_player.game_nametag))
                            except discord.Forbidden:
                                pass

                    msg = botutils.BotEmoji.butterfly
                    msg += " "
                    msg += action_assign.format(killed_player.game_nametag)
                    try:
                        await player.user.send(msg)
                    except discord.Forbidden:
                        pass
                else:
                    pass
