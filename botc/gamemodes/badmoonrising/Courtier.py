"""Contains the Courtier Character class"""

import json
import globvars
import configparser
from botc import Character, Townsfolk, NonRecurringAction, GameLogic, ActionTypes, Action, CourtierPoison, BOTCUtils, Flags, Inventory
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.courtier.value.lower()]

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)
    butterfly = bot_text["esthetics"]["butterfly"]

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Courtier(Townsfolk, BadMoonRising, Character, NonRecurringAction):
    """Courtier: Once per game, at night, choose a character: they are drunk for 3 nights & 3 days.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/7/7d/Courtier_Token.png"
        self._art_link_cropped = "https://imgur.com/c1wt8jB.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Courtier"

        self._role_enum = BMRRole.courtier
        self._emoji = "<:bmrcourtier:781151556128342058>"

        self.inventory = Inventory(
            Flags.courtier_unique_poison
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
    
    def has_finished_night_action(self, player):
        """Return True if courtier has submitted the poison action"""

        if player.is_alive():
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.poison
        return True
    
    @GameLogic.unique_ability(ActionTypes.poison)
    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    @GameLogic.requires_bmr_roles
    async def register_poison(self, player, targets):
        """Poison command"""
        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for courtier 'poison'"

        print("Courtier: registered poison")

        player.role.ego_self.inventory.remove_item_from_inventory(Flags.courtier_unique_poison)

        possible_poisoned_players = BOTCUtils.get_players_from_role_name(targets[0]._role_enum)

        # Courtier can poison non in-game characters, but we only process the poison if the characetr is in game
        if len(possible_poisoned_players) is not 0:
            poisoned_player = possible_poisoned_players[0]

            action = Action(player, poisoned_player, ActionTypes.poison, globvars.master_state.game._chrono.phase_id)
            player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].name)
        await player.user.send(msg)

    async def exec_poison(self, poisoner_player, poisoned_player):
        """Execute the poison actions (night interaction)"""
        if not poisoner_player.is_droisoned() and poisoner_player.is_alive():

            print(f"Courtier: poisoned {poisoned_player}")

            poisoned_player.add_status_effect(CourtierPoison(poisoner_player, poisoned_player))
    
    async def process_night_ability(self, player):
        """Process night actions for the poisoner character.
        @player : the Courtier player (Player object)
        """
        
        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The courtier has submitted an action. We call the execution function immediately
        if action:
            assert action.action_type == ActionTypes.poison, f"Wrong action type {action} in courtier"
            poisoned_player = action.target_player
            await self.exec_poison(player, poisoned_player)
        # The courtier has not submitted an action.
        else:
            pass
