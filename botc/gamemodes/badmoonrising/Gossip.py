"""Contains the Gossip Character class"""

import json
import random

import botutils
import globvars
from botc import (
    Action, ActionTypes, AlreadyDead, Category, Character, Flags,
    RecurringAction, Townsfolk, validate_statement)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.gossip.value.lower()]

butterfly = BotEmoji.butterfly

from botc import emojis


class Gossip(Townsfolk, BadMoonRising, Character, RecurringAction):
    """Gossip: Each day, you may make a public statement. Tonight, if it was true, a player dies.

    ===== GOSSIP ===== 

    true_self = gossip
    ego_self = gossip
    social_self = gossip

    commands:
    - gossip <statement>

    initialize setup? -> NO
    initialize role? -> NO

    ----- First night
    START:
    override first night instruction? -> NO

    ----- Regular night
    START:
    override regular night instruction? -> NO
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/b/b8/Gossip_Token.png"
        self._art_link_cropped = "https://imgur.com/uhcVkwz.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Gossip"

        self._role_enum = BMRRole.gossip
        self._emoji = emojis["badmoonrising"]["gossip"]
        
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
    
    def add_action_field_n1(self, embed_obj):
        """Send the stats list n1"""

        msg = self.action
        embed_obj.add_field(name = butterfly + " **「 Your Action 」**", value = msg, inline = False)
        return embed_obj

    async def send_regular_night_start_dm(self, recipient):
        pass

    async def register_gossip(self, gossip_player, statement):
        """Gossip command"""

        from ._utils import register_gossip

        statement_truthy = validate_statement(gossip_player, statement)
        register_gossip(gossip_player)

        if statement_truthy and gossip_player.action_grid.retrieve_an_action(globvars.master_state.game._chrono.phase_id + 1) is None:
            target_player = random.choice([player for player in globvars.master_state.game.sitting_order if \
                not player.role.true_self.category == Category.demon or \
                player.role.true_self.inventory.has_item_in_inventory(Flags.zombuul_unique_death_escape) or \
                BMRRole.mastermind.value in [player.role.true_self.name for player in globvars.master_state.game.sitting_order if player.is_alive()]
            ])
            action = Action(gossip_player, [target_player], ActionTypes.gossip, globvars.master_state.game._chrono.phase_id)
            gossip_player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id + 1)

        await botutils.send_lobby(character_text["feedback"].format(statement))

        globvars.master_state.game.replay += f"- {gossip_player.user.name} (Gossip) states that {statement}, which is {statement_truthy}\n"

    async def exec_gossip(self, gossip_player, target):
        """Gossip command."""

        success = "unsuccessfully "

        if gossip_player.is_alive() and not gossip_player.is_droisoned():
            success = ""
            if target.role.true_self.can_be_killed(target):
                try:
                    await target.exec_real_death()
                except AlreadyDead:
                    pass
                else:
                    globvars.master_state.game.night_deaths.append(target)

        globvars.master_state.game.replay += f"- {gossip_player.user.name} (Gossip) {success}kills {target.user.name} ({target.role.name})\n"

    async def process_night_ability(self, player):
        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The gossip has submitted an action. We call the execution function immediately
        if action and not action.action_type == ActionTypes.ability_pass:
            assert action.action_type == ActionTypes.gossip, f"Wrong action type {action} in gambler"
            targets = action.target_player
            target = targets[0]
            await self.exec_gossip(player, target)
        # The gossip has not submitted an action.
        else:
            pass
