"""Contains the Tinker Character class"""

import asyncio
import json
import random
import time
from threading import Thread

import botutils
import globvars
from botc import (AlreadyDead, Category, Character, NonRecurringAction,
                  Outsider, Team, game_text, gameloops)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.tinker.value.lower()]

from botc import emojis

day_death_str = game_text["gameplay"]["day_death"]

class Tinker(Outsider, BadMoonRising, Character, NonRecurringAction):
    """Tinker: You might die at any time.

    ===== TINKER =====

    true_self = tinker
    ego_self = tinker
    social_self = tinker

    commands:
    - kill <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> NO

    END:
    override regular night end? -> YES
                                => Chance of dying
    """

    def __init__(self):

        Character.__init__(self)
        BadMoonRising.__init__(self)
        Outsider.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/e/e8/Tinker_Token.png"
        self._art_link_cropped = "https://imgur.com/T2aCAyq.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Tinker"

        self._role_enum = BMRRole.tinker
        self._emoji = emojis["badmoonrising"]["tinker"]
    
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

    async def process_night_ability(self, player):
        game = globvars.master_state.game

        # Tinker shouldnt die n1 (n1 is storyteller death)
        if game._chrono.is_night_1():
            return

        # Tinker should not die if there are only 3 alive players (instant win for evil)
        # If game as at 3p, evil should be able to kill to end the game anyways,
        # but in the case of idle / zombuul tinker should still not die
        if len(game.list_alive_players) == 3:
            return

        if player.is_alive():
            # Tinker chance of death at night (favorises evil):
            # ( 1/(num_players-2) + 0.2*dead_minions - 0.05*(alive_outsiders-1) ) / 2
            chance = 1 / (len(game.player_obj_list) - 2)
            # Check true self because this is not an ability check - it is a game balance check
            chance += 0.2 * len([p for p in game.player_obj_list if p.is_dead() and p.role.true_self.category == Category.minion])
            chance -= 0.05 * len([p for p in game.player_obj_list if p.is_alive() and p.role.true_self.category == Category.outsider])

            chance = chance / 2

            if random.random() < chance:
                globvars.master_state.game.replay += f"- {player.user.name} (Tinker) dies at night.\n"
                # Tinker dies
                if player.role.true_self.can_be_killed(player):
                    try:
                        await player.exec_real_death()
                    except AlreadyDead:
                        pass
                    else:
                        globvars.master_state.game.night_deaths.append(player)

    async def process_dawn_ability(self, player):
        # Tinker chance of death at day (favorises good):
        # 1 / (num_alive_players - num_alive_evil_players) * 0.75
        # Might throw a division by 0 exception (should be impossible, but might still happen), so we have to catch that

        game = globvars.master_state.game

        try:
            alive_players = [p for p in game.player_obj_list if p.is_alive()]

            num_alive_evil_players = len([p for p in alive_players if p.role.true_self.team == Team.evil])
            num_alive_players = len(alive_players)

            chance = 1 / (num_alive_players - num_alive_evil_players) * 0.75

            if random.random() < chance:
                # Tinker dies later in the day
                # Minimum wait time is 30s

                # Tinker can die anytime during the day, and up to halfway through nomination period (base durations)
                day_plus_half_noms = gameloops.calculate_base_day_duration(game) + 90/2

                countdown = random.random() * day_plus_half_noms

                # Do not die during dawn, but since this method
                # is only called at the end of dawn there is
                # no need to delay for long
                countdown += 5

                async def kill_tinker():
                    # Do not let tinker die at 3p, instant win for evil
                    if num_alive_players == 3:
                        return
                    await asyncio.sleep(countdown)
                    globvars.master_state.game.replay += f"- {player.user.name} (Tinker) dies at day.\n"
                    if player.role.true_self.can_be_killed(player):
                        try:
                            await player.exec_real_death()
                        except AlreadyDead:
                            pass
                        else:
                            await botutils.send_lobby(day_death_str.format(player.game_nametag))

                asyncio.create_task(kill_tinker())

        except ZeroDivisionError:
            pass



