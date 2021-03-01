"""Contains the Devil's Advocate Character class"""

import json
import globvars
import configparser
from botc import Character, Minion, ActionTypes, RecurringAction, GameLogic, Action, ActionTypes, SafetyFromExecution
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.devilsadvocate.value.lower()]

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    butterfly = bot_text["esthetics"]["butterfly"]

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class DevilsAdvocate(Minion, BadMoonRising, Character, RecurringAction):
    """Devil's Advocate: Each night, choose a living player (not the same as last night): 
    if executed tomorrow, they do not die.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/2/23/Devils_Advocate_Token.png"
        self._art_link_cropped = "https://imgur.com/b2rcp8E.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Devil%27s_Advocate"

        self._role_enum = BMRRole.devilsadvocate
        self._emoji = "<:bmrdevilsadvocate:781151556493639680>"

    def has_finished_night_action(self, player):
        """Return True if the devil's advocate has submitted the protect action"""

        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.protect
        return True

    def add_action_field_n1(self, embed_obj):
        """Send the stats list n1"""

        msg = self.action
        msg += globvars.master_state.game.create_sitting_order_stats_string()
        embed_obj.add_field(name = butterfly + " **「 Your Action 」**", value = msg, inline = False)
        return embed_obj

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

    @GameLogic.changes_not_allowed
    @GameLogic.requires_one_target
    @GameLogic.no_same_following_targets
    async def register_protect(self, player, targets):
        """Protect command"""

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for devil's advocate 'protect'"
        action = Action(player, targets, ActionTypes.protect, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)
    
    async def exec_protect(self, da_player, protected_player):
        """Execute the protection action (night ability interaction)"""

        if not da_player.is_droisoned() and da_player.is_alive():
            protected_player.add_status_effect(SafetyFromExecution(da_player, protected_player))

    async def process_night_ability(self, player):
        """Process night actions for the devil's advocate character.
        @player : the Devil's advocate player (Player object)
        """
        
        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The devil's advocate has submitted an action. We call the execution function immediately
        if action:
            assert action.action_type == ActionTypes.protect, f"Wrong action type {action} in devil's advocate"
            targets = action.target_player
            protected_player = targets[0]
            await self.exec_protect(player, protected_player)
        # The devil's advocate has not submitted an action. We will not randomize the action because this 
        # is a priviledged ability
        else:
            pass