"""Contains the Exorcist Character class"""

import json
import globvars
import configparser
from botc import Character, Townsfolk, ActionTypes, RecurringAction, GameLogic, Action, Demon, Drunkenness
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.exorcist.value.lower()]

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    butterfly = bot_text["esthetics"]["butterfly"]

with open('botc/game_text.json') as json_file:
    game_text = json.load(json_file)
    exorcist_chose_demon = game_text["gameplay"]["exorcist_chose_demon"]

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"


class Exorcist(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Exorcist: Each night*, choose a player (not the same as last night): the Demon, if chosen, 
    learns who you are & does not act tonight.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/9/9a/Exorcist_Token.png"
        self._art_link_cropped = "https://imgur.com/4Df7WYp.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Exorcist"

        self._role_enum = BMRRole.exorcist
        self._emoji = "<:bmrexorcist:781151556442521620>"

    def has_finished_night_action(self, player):
        """Return True if the exorcist has submitted the exorcise action"""

        if player.is_alive():
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.exorcise
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

    @GameLogic.except_first_night
    @GameLogic.requires_one_target
    @GameLogic.no_same_following_targets
    async def register_exorcise(self, player, targets):
        """Exorcise command"""

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for exorcist 'exorcise'"
        action = Action(player, targets, ActionTypes.exorcise, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_exorcise(self, exorcist_player, exorcised_player):
        """Execute the exorcise action (night ability interaction)"""
        
        if exorcist_player.is_alive and not exorcist_player.is_droisoned():

            if isinstance(exorcised_player.role.true_self, Demon):
                
                # Make the demon drunk for one phase so that they do not act tonight
                exorcised_player.add_status_effect(Drunkenness(exorcist_player, exorcised_player, None, 1))

                await exorcised_player.user.send(exorcist_chose_demon.format(exorcist_player.game_nametag))

    async def process_night_ability(self, player):
        """Process night actions for the exorcist character.
        @player : the Exorcist player (Player object)
        """

        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The exorcist has submitted an action. We call the execution function immediately
        if action:
            assert action.action_type == ActionTypes.exorcise, f"Wrong action type {action} in exorcist"
            targets = action.target_player
            exorcised_player = targets[0]
            await self.exec_exorcise(player, exorcised_player)
        # The exorcist has not submitted an action. We will not randomize the action because this 
        # is a priviledged ability
        else:
            pass