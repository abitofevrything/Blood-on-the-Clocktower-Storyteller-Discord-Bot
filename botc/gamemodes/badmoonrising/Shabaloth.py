"""Contains the Shabaloth Character class"""

import json
import random
import asyncio

import discord
import toml

import botutils
import globvars
from botc import (Action, ActionTypes, BOTCUtils, Character, Demon, GameLogic,
                  Outsider, RecurringAction, ShabalothRevive, Townsfolk,
                  game_text, Category)

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.shabaloth.value.lower()]

demon_bluff_str = game_text["gameplay"]["demonbluffs"]
demon_learn_lunatic = game_text["gameplay"]["demon_learn_lunatic"]
action_assign = game_text["gameplay"]["action_assign"]
demon_learn_lunatic_attack = game_text["gameplay"]["demon_learn_lunatic_attack"]

from botc import emojis
from config import DISABLE_DMS, BASE_NIGHT


class Shabaloth(Demon, BadMoonRising, Character, RecurringAction):
    """Shabaloth: Each night*, choose 2 players: they die. A dead player you chose last night 
    might be regurgitated.

    ===== SHABALOTH =====

    true_self = shabaloth
    ego_self = shabaloth
    social_self = shabaloth

    commands:
    - kill <player1> and <player2>

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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/7/75/Shabaloth_Token.png"
        self._art_link_cropped = "https://imgur.com/vWrBrvS.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Shabaloth"

        self._role_enum = BMRRole.shabaloth
        self._emoji = emojis["badmoonrising"]["shabaloth"]
    
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
                from . import Po, Pukka, Zombuul
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

        globvars.logging.info(f">>> Shabaloth: Received three demon bluffs {bluff_1}, {bluff_2} and {bluff_3}.")
        return (bluff_1, bluff_2, bluff_3)

    async def send_opening_dm_embed(self, recipient):
        await super().send_opening_dm_embed(recipient)
        # Fake lunatic might be a pukka, in which case we deal with it here
        if globvars.master_state.game._chrono.is_night_1():
            await self.send_regular_night_start_dm(recipient)
    
    async def send_regular_night_start_dm(self, recipient):
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

        if not globvars.master_state.game._chrono.is_night_1():
            await super().send_regular_night_start_dm(recipient)

    
    def has_finished_night_action(self, player):
        """Return True if shabaloth has submitted the kill action"""
        
        if player.is_alive():
            # First night, shabaloth does not act
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None
        return True

    @GameLogic.requires_two_targets
    @GameLogic.except_first_night
    @GameLogic.changes_not_allowed
    @GameLogic.requires_different_targets
    async def register_kill(self, player, targets):
        """Kill command"""

        # Must be 2 targets
        assert len(targets) == 2, "Received a number of targets different than 1 for shabaloth 'kill'"
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

        msg = botutils.BotEmoji.butterfly + " " + character_text["feedback"].format(targets[0].game_nametag, targets[1].game_nametag)
        await player.user.send(msg)

    async def exec_kill(self, shabaloth_player, targets):

        success = "unsuccessfully "
        if shabaloth_player.is_alive() and not shabaloth_player.is_droisoned():
            success = ""
            for target in targets:
                if target.role.true_self.can_be_demon_killed(target):
                    await target.role.ego_self.on_being_demon_killed(target)

            if random.random() < 0.2:
                # One of the players will be regurgitated tomorrow
                
                revived = random.choice(targets)

                if revived.is_apparently_dead():
                    revived.add_status_effect(ShabalothRevive(shabaloth_player, revived))

        globvars.master_state.game.replay += f"- {shabaloth_player.user.name} ({shabaloth_player.role.name}) {success}kills {targets[0].user.name} ({targets[0].role.name})" \
            f" and {targets[1].user.name} ({targets[1].role.name})\n"


    async def process_night_ability(self, player):
        """Process night actions for the shabaloth character.
        @player : the Shabaloth player (Player object)
        """

        # We only do any of the following if the shabaloth is alive. Otherwise skip everything.
        if player.is_alive():
        
            phase = globvars.master_state.game._chrono.phase_id
            action = player.action_grid.retrieve_an_action(phase)
            # The shabaloth has submitted an action. We call the execution function immediately
            if action and not action.action_type == ActionTypes.ability_pass:
                assert action.action_type == ActionTypes.kill, f"Wrong action type {action} in shabaloth"
                targets = action.target_player
                await self.exec_kill(player, targets)
            # The shabaloth has not submitted an action. We will randomize the action and make 
            # the shabaloth kill one random player that is not the zombuul. 
            else:
                if player.is_alive():
                    game = globvars.master_state.game

                    possible_kills = [p for p in game.player_obj_list if p.is_apparently_alive() and not p.user.id == player.user.id]

                    while len(possible_kills) < 2:
                        possible_kills.append(next((p for p in game.player_obj_list if p.is_apparently_dead()), None))

                    random.shuffle(possible_kills)

                    while len(possible_kills) > 2:
                        possible_kills.pop()

                    await self.exec_kill(player, possible_kills)

                    if DISABLE_DMS:
                        return

                    if player.role.true_self.name == BMRRole.lunatic.value:
                        for p in [p for p in globvars.master_state.game.player_obj_list if p.role.true_self.category == Category.demon]:
                            try:
                                await p.user.send(demon_learn_lunatic_attack.format(player.game_nametag, f"{possible_kills[0].game_nametag} and {possible_kills[1].game_nametag}"))
                            except discord.Forbidden:
                                pass

                    msg = botutils.BotEmoji.butterfly
                    msg += " "
                    msg += action_assign.format(", ".join(map(lambda p: p.game_nametag, possible_kills)))
                    try:
                        await player.user.send(msg)
                    except discord.Forbidden:
                        pass
