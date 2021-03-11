"""Contains the Gambler Character class"""

import json
import globvars
import configparser
from botc import Character, Townsfolk, ActionTypes, RecurringAction, GameLogic, BMRRolesOnly, ActionTypes, Action, AlreadyDead
from botutils import BotEmoji
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.gambler.value.lower()]

with open('botutils/bot_text.json') as json_file:
    bot_text = json.load(json_file)

with open('botc/emojis.json') as json_file:
    emojis = json.load(json_file)

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)
    x_emoji = documentation["cmd_warnings"]["x_emoji"]
    bmr_roles_only_str = documentation["cmd_warnings"]["bmr_roles_only"]

butterfly = BotEmoji.butterfly

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Gambler(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Gambler: Each night*, choose a player & guess their character: if you guess wrong, you die.
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/f/f5/Gambler_Token.png"
        self._art_link_cropped = "https://imgur.com/vkiURKP.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Gambler"

        self._role_enum = BMRRole.gambler
        self._emoji = emojis["badmoonrising"]["gambler"]

    def has_finished_night_action(self, player):
        """Return True if gambler has submitted the guess action"""
        
        if player.is_alive():
            # First night, gambler does not act
            if globvars.master_state.game._chrono.is_night_1():
                return True
            current_phase_id = globvars.master_state.game._chrono.phase_id
            received_action = player.action_grid.retrieve_an_action(current_phase_id)
            return received_action is not None and received_action.action_type == ActionTypes.guess
        return True

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

    @GameLogic.except_first_night
    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    async def register_guess(self, player, targets):
        """Guess command"""

        # Implement the bmr roles only check ourselves, as
        # the gamelogic class will not handle this type of
        # target

        role_list = [x.value for x in BMRRole]
        for character in targets:
            if character[1].name not in role_list:
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))

        assert len(targets) == 1, "Received a number of targets different than 1 for gambler 'guess'"
        action = Action(player, targets, ActionTypes.guess, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)
        
        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0][0].game_nametag, targets[0][1].name)
        await player.user.send(msg)

    async def exec_guess(self, gambler_player, gamble):
        """Execute the exorcise action (night ability interaction)"""
        
        if gambler_player.is_alive and not gambler_player.is_droisoned():

            guess_target = gamble[0]
            guess_role = gamble[1]

            if not guess_target.role.true_self.name == guess_role.name:
                if gambler_player.role.true_self.can_be_killed(gambler_player):
                    try:
                        await gambler_player.exec_real_death()
                    except AlreadyDead:
                        pass
                    else:
                        globvars.master_state.game.night_deaths.append(gambler_player)


    async def process_night_ability(self, player):
        """Process night actions for the exorcist character.
        @player : the Exorcist player (Player object)
        """

        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The gambler has submitted an action. We call the execution function immediately
        if action:
            assert action.action_type == ActionTypes.guess, f"Wrong action type {action} in gambler"
            targets = action.target_player
            guess = targets[0]
            await self.exec_guess(player, guess)
        # The exorcist has not submitted an action. We will not randomize the action because this 
        # is a priviledged ability
        else:
            pass
