"""Contains the Assassin Character class"""

import json
import configparser
from botc import Character, Minion, ActionTypes, NonRecurringAction, Flags, Inventory, Action
from botc.errors import AlreadyDead
from botc.BOTCUtils import GameLogic
from ._utils import BadMoonRising, BMRRole
import globvars

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.assassin.value.lower()]
    
with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    butterfly = bot_text["esthetics"]["butterfly"]

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Assassin(Minion, BadMoonRising, Character, NonRecurringAction):
    """Assassin: Once per game, at night*, choose a player: they die, even if for some reason they could not.
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
        self._emoji = "<:bmrassassin:781151556665344010>"

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

    @GameLogic.unique_ability(ActionTypes.assassinate)
    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
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

        if assassin_player.is_alive() and not assassin_player.is_droisoned():
            try:
                await killed_player.exec_real_death()
            except AlreadyDead:
                pass
            else:
                globvars.master_state.game.night_deaths.append(killed_player)

    def has_finished_night_action(self, player):
        """Return True if assassin has submitted the assassinate action"""
        
        if player.is_alive():
            # First night, assassin does not act
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.assassinate
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
            if action:
                assert action.action_type == ActionTypes.assassinate,  f"Wrong action type {action} in assassin"
                targets = action.target_player
                killed_player = targets[0]
                await self.exec_assassinate(player, killed_player)


