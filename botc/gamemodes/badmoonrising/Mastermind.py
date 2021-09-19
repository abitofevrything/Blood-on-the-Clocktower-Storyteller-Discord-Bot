"""Contains the Mastermind Character class"""

import json

import globvars
from botc import Category, Character, Minion, NonRecurringAction, Phase, Team
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.mastermind.value.lower()]

from botc import emojis


class Mastermind(Minion, BadMoonRising, Character, NonRecurringAction):
    """Mastermind: If the Demon dies by execution, play for 1 more day. If a player 
    is then executed, their team loses

    ===== MASTERMIND ===== 

    true_self = courtier
    ego_self = courtier
    social_self = courtier

    commands:
    - poison <player>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> YES  # default is to send instruction string only
                                      => Send query for "poison" command

    ----- Regular night
    START:
    override regular night instruction? -> YES  # default is to send nothing
                                        => Send query for "poison" command if the player has not used their ability yet
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/d/d5/Mastermind_Token.png"
        self._art_link_cropped = "https://imgur.com/rM0fbDu.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Mastermind"

        self._role_enum = BMRRole.mastermind
        self._emoji = emojis["badmoonrising"]["mastermind"]

        self._trigger_phase = None
        
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

    def check_winning_conditions(self, mastermind_player):
        game = globvars.master_state.game

        if mastermind_player.is_dead():
            return True

        if game.today_executed_player is not None:
            if mastermind_player.role.true_self._trigger_phase is None and game.today_executed_player.role.true_self.category == Category.demon:
                # Zombuul fake death does not trigger mastermind
                if game.today_executed_player.is_alive():
                    return True
                mastermind_player.role.true_self._trigger_phase = game._chrono.phase_id
                return False
            elif mastermind_player.role.true_self._trigger_phase is not None:
                if mastermind_player.role.true_self._trigger_phase + 3 > game._chrono.phase_id:
                    # Mastermind is preventing the game from ending
                    return False
                else:
                    # Check who was executed, and end the game accordingly
                    if game.today_executed_player.role.true_self.team == Team.evil:
                        game.winners = Team.good
                    else:
                        game.winners = Team.evil
                    game.gameloop.cancel()
                    return False
        elif mastermind_player.role.true_self._trigger_phase is not None:
            if mastermind_player.role.true_self._trigger_phase + 3 >= game._chrono.phase_id:
                # No player was executed, evil team loses
                game.winners = Team.good
                game.gameloop.cancel()

                return False

            # Mastermind is preventing game from ending
            return False
        else:
            return True
