"""Contains the Sailor Character class"""

import json
import globvars
import configparser
import random
from botutils import BotEmoji
from botc import Character, Townsfolk, ActionTypes, RecurringAction, GameLogic, Action, ActionTypes, SailorDrunkenness, Player, Targets
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.sailor.value.lower()]

butterfly = BotEmoji.butterfly

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Sailor(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Sailor: Each night, choose a player: either you or they are drunk until dusk. 
    You cannot die.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/0/01/Sailor_Token.png"
        self._art_link_cropped = "https://imgur.com/wXLvtmm.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Sailor"

        self._role_enum = BMRRole.sailor
        self._emoji = "<:bmrsailor:781152054906716161>"
        
    def has_finished_night_action(self, player):
        """Return True if sailor has submitted the visit action"""
        
        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.visit
        return True

    def create_n1_instr_str(self):
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

    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    async def register_visit(self, player, targets):
            """Visit command"""
            # Must be 1 target
            assert len(targets) == 1, "Received a number of targets different than 1 for sailor 'visit'"
            action = Action(player, random.choice([targets, Targets([player])]), ActionTypes.visit, globvars.master_state.game._chrono.phase_id)
            player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

            if DISABLE_DMS:
                return

            msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
            await player.user.send(msg)

    async def exec_visit(self, player, target):
        """Visit command"""
        if not player.is_droisoned() and player.is_alive():
            player.add_status_effect(SailorDrunkenness(player, target))

    async def process_night_ability(self, player):
        """Process night actions for the sailor character.
        @player : the Sailor player (Player object)
        """
        
        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The sailor has submitted an action. We call the execution function immediately
        if action:
            assert action.action_type == ActionTypes.visit, f"Wrong action type {action} in sailor"
            targets = action.target_player
            poisoned_player = targets[0]
            await self.exec_visit(player, poisoned_player)
        # The sailer has not submitted an action. We will not randomize the action since 
        # the visit ability is a "priviledged" ability
        else:
            pass

    def can_be_executed(self, player):
        return player.is_droisoned()

    def can_be_demon_killed(self, player):
        return player.is_droisoned()

    def can_be_killed(self, player):
        return player.is_droisoned()