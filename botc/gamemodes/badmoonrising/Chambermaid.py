"""Contains the Chambermaid Character class"""

import json
import globvars
<<<<<<< HEAD
import discord
import configparser
import datetime
import random
from botc import Character, Townsfolk, ActionTypes, RecurringAction, GameLogic, Action, Flags
=======
from botc import Character, Townsfolk, ActionTypes, RecurringAction
>>>>>>> db0cfaf0fcb930ba41046bb892537db816a5d67d
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.chambermaid.value.lower()]

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    butterfly = bot_text["esthetics"]["butterfly"]

<<<<<<< HEAD
with open('botc/game_text.json') as json_file: 
    strings = json.load(json_file)
    chambermaid_nightly = strings["gameplay"]["chambermaid_nightly"]
    copyrights_str = strings["misc"]["copyrights"]

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Chambermaid(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Chambermaid
    Each night, choose 2 alive players (not yourself): you learn how many woke 
=======
class Chambermaid(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Chambermaid Each night, choose 2 alive players (not yourself): you learn how many woke 
>>>>>>> db0cfaf0fcb930ba41046bb892537db816a5d67d
    tonight due to their ability.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/8/87/Chambermaid_Token.png"
        self._art_link_cropped = "https://imgur.com/eNn6hQa.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Chambermaid"

        self._role_enum = BMRRole.chambermaid
        self._emoji = "<:bmrchambermaid:781151556053499925>"

    def has_finished_night_action(self, player):
        """Return True if the Chambermaid has submitted the see action"""

        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.see
        return True

    def create_n1_instr_str(self):
<<<<<<< HEAD
        """Create the instruction field on the opening dm card"""

        # First line is the character instruction string
        msg = f"{self.emoji} {self.instruction}"
        addendum = character_text["n1_addendum"]
        
        # Some characters have a line of addendum
        if addendum:
            with open("botutils/bot_text.json") as json_file:
                bot_text = json.load(json_file)
                scroll_emoji = bot_text["esthetics"]["scroll"]
            msg += f"\n{scroll_emoji} {addendum}"
            
        return msg

    def add_action_field_n1(self, embed_obj):
        """Send the stats list n1"""

        msg = self.action
        msg += globvars.master_state.game.create_sitting_order_stats_string()
        embed_obj.add_field(name = butterfly + " **「 Your Action 」**", value = msg, inline = False)
        return embed_obj

    @GameLogic.no_self_targetting
    @GameLogic.requires_two_targets
    @GameLogic.requires_different_targets
    async def register_see(self, player, targets):
        """See command
        @player: Player object
        @targets: Target object
        """

        # Must be two targets
        assert len(targets) == 2, "Received a number of targets different than 2 for chambermaid 'sees'"
        action = Action(player, targets, ActionTypes.see, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag, targets[1].game_nametag)
        await player.user.send(msg)

    async def exec_see(self, chambermaid_player, targets):
        """Execute the see action (night ability interaction)"""

        if DISABLE_DMS:
            return

        from botc.BOTCUtils import get_number_image

        wakes_every_night_if_alive = [
            BMRRole.sailor,
            BMRRole.chambermaid,
            BMRRole.devilsadvocate,
            BMRRole.pukka
        ]

        wakes_every_night_if_alive_except_n1 = [
            BMRRole.exorcist,
            BMRRole.innkeeper,
            BMRRole.gambler,
            BMRRole.zombuul,
            BMRRole.shabaloth,
            BMRRole.po
        ]

        wakes_if_condition_met = {
            BMRRole.courtier.value : lambda player : player.is_alive() and player.role.ego_self.inventory.has_item_in_inventory(Flags.courtier_unique_poison),
            BMRRole.professor.value : lambda player : player.is_alive() and player.role.ego_self.inventory.has_item_in_inventory(Flags.professor_unique_resurrect) and not globvars.master_state.game._chrono.is_night_1(),
            BMRRole.assassin.value : lambda player : player.is_alive() and player.role.ego_self.inventory.has_item_in_inventory(Flags.assassin_unique_kill) and not globvars.master_state.game._chrono.is_night_1()
        }

        for role in wakes_every_night_if_alive:
            wakes_if_condition_met[role.value] = lambda player : player.is_alive()

        for role in wakes_every_night_if_alive_except_n1:
            wakes_if_condition_met[role.value] = lambda player : player.is_alive() and not globvars.master_state.game._chrono.is_night_1()

        for role in BMRRole:
            if role.value not in wakes_if_condition_met:
                wakes_if_condition_met[role.value] = lambda _ : False

        target_1_woke = wakes_if_condition_met[targets[0].role.social_self._role_enum.value](targets[0])
        target_2_woke = wakes_if_condition_met[targets[1].role.social_self._role_enum.value](targets[1])

        if not chambermaid_player.is_droisoned():
            if not target_1_woke and not target_2_woke:
                total = 0
            elif target_1_woke ^ target_2_woke:
                total = 1
            else:
                total = 2
        else:
            total = random.choice([0, 1, 2])

        link = get_number_image(total)

        recipient = chambermaid_player.user

        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"
        msg += chambermaid_nightly.format(total)

        embed = discord.Embed(description = msg)
        embed.set_thumbnail(url = link)
        embed.set_footer(text = copyrights_str)
        embed.timestamp = datetime.datetime.utcnow()

        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            pass


    async def process_night_ability(self, player):
        """Process night abilities for the chambermaid player
        @player: the chambermaid player (Player obj)
        """

        # We only do the following if the chambermaid is alive
        if player.is_alive():
            phase = globvars.master_state.game._chrono.phase_id
            action = player.action_grid.retrieve_an_action(phase)

            # The chambermaid submitted their see action
            if action:
                assert action.action_type == ActionTypes.see,  f"Wrong action type {action} in chambermaid"
                targets = action.target_player
                await self.exec_see(player, targets)

            # We do not randomize the chambermaid read
            else:
                pass
=======
        return "not_implemented"
>>>>>>> db0cfaf0fcb930ba41046bb892537db816a5d67d
