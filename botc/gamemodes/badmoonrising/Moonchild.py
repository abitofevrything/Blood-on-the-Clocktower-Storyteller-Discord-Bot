"""Contains the Moonchild Character class"""

import datetime
import json

import discord
import toml

import globvars
from botc import (Action, ActionTypes, AlreadyDead, BOTCUtils, Character,
                  GameLogic, NonRecurringAction, Outsider, Team, game_text)
from botutils import BotEmoji

from . import character_texts
from ._utils import BadMoonRising, BMRRole

character_text = character_texts[BMRRole.moonchild.value.lower()]

from botc import emojis

action_assign = game_text["gameplay"]["action_assign"]
copyrights_str = game_text["misc"]["copyrights"]
    
from config import DISABLE_DMS


class Moonchild(Outsider, BadMoonRising, Character, NonRecurringAction):
    """Moonchild: When you learn you are dead, choose 1 alive player: if good, they die tonight.

    ===== MOONCHILD ===== 

    true_self = moonchild
    ego_self = moonchild
    social_self = moonchild

    commands:
    - choose <player>

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
        Outsider.__init__(self)

        self._desc_string = character_text["description"]
        self._examp_string = character_text["examples"]
        self._instr_string = character_text["instruction"]
        self._lore_string = character_text["lore"]
        self._brief_string = character_text["brief"]
        self._action = character_text["action"]

        self._art_link = "https://bloodontheclocktower.com/wiki/images/4/4c/Moonchild_Token.png"
        self._art_link_cropped = "https://imgur.com/iVnwFvV.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Moonchild"

        self._role_enum = BMRRole.moonchild
        self._emoji = emojis["badmoonrising"]["moonchild"]
  
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

    def check_action_completed(self, player):
        current_phase_id = globvars.master_state.game._chrono.phase_id
        if not player.apparent_death_phase_id == globvars.master_state.game._chrono.phase_id - 1:
            return True
        received_action = player.action_grid.retrieve_an_action(current_phase_id)
        return received_action is not None

    # Delegate both action complete checks to the function above
    def has_finished_dawn_action(self, player):
        return self.check_action_completed(player)

    def has_finished_night_action(self, player):
        return self.check_action_completed(player)

    async def exec_choose(self, player, target):
        success = "unsuccessfully "
        if not player.is_droisoned():
            if target.role.social_self.team == Team.good:
                success = ""
                if target.role.true_self.can_be_killed(target):
                    try:
                        await target.exec_real_death()
                    except AlreadyDead:
                        pass
                    else:
                        globvars.master_state.game.night_deaths.append(target)

        globvars.master_state.game.replay += f"- {player.user.name} (Moonchild) {success}chooses {target.user.name} ({target.role.name})\n"
            
    @GameLogic.requires_one_target
    @GameLogic.no_self_targetting
    @GameLogic.requires_alive_targets
    async def register_choose(self, player, targets):
        """Choose command"""

        # If the current phase is not the activation phase, ignore the command
        if not player.apparent_death_phase_id == globvars.master_state.game._chrono.phase_id - 1:
            return

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for moonchild 'choose'"
        action = Action(player, targets, ActionTypes.choose, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = BotEmoji.butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def process_ability(self, player):
        # We only do any of the following if the moonchild is dead in the last phase. Otherwise skip everything.
        if player.is_apparently_dead() and player.apparent_death_phase_id == globvars.master_state.game._chrono.phase_id - 1:
        
            phase = globvars.master_state.game._chrono.phase_id
            action = player.action_grid.retrieve_an_action(phase)
            # The moonchild has submitted an action. We call the execution function immediately
            if action and not action.action_type == ActionTypes.ability_pass:
                assert action.action_type == ActionTypes.choose, f"Wrong action type {action} in moonchild"
                targets = action.target_player
                chosen = targets[0]
                await self.exec_choose(player, chosen)
            # The moonchild has not submitted an action. We will randomize the action and make 
            # the moonchild kill one random player
            else:
                chosen = BOTCUtils.get_random_player_excluding(player)
                await self.exec_choose(player, chosen)

                if DISABLE_DMS:
                    return

                msg = BotEmoji.butterfly
                msg += " "
                msg += action_assign.format(chosen.game_nametag)
                try:
                    await player.user.send(msg)
                except discord.Forbidden:
                    pass

    # Delegate both ability processing to the above function
    async def process_night_ability(self, player):
        """Process night actions for the moonchild character.
        @player : the Moonchild player (Player object)
        """
        await self.process_ability(player)
        

    async def process_dawn_ability(self, player):
        """Process dawn actions for the moonchild character.
        @player : the Moonchild player (Player object)
        """
        await self.process_ability(player)


    async def send_ability_prompt(self, recipient):
        """Send the query for night / dawn action"""

        if DISABLE_DMS:
            return

        import globvars

        # Construct the message to send
        msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
        msg += "\n"
        msg += self.emoji + " " + self.instruction
        msg += "\n"

        embed = discord.Embed(description = msg)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text = copyrights_str)

        msg2 = self.action
        msg2 += globvars.master_state.game.create_sitting_order_stats_string()
        embed.add_field(name = BotEmoji.butterfly + " **「 Your Action 」**", value = msg2, inline = False)
        
        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            pass

    async def send_regular_night_start_dm(self, recipient):
        player = BOTCUtils.get_player_from_id(recipient.id)
        if player.apparent_death_phase_id == globvars.master_state.game._chrono.phase_id - 1:
            await self.send_ability_prompt(recipient)

    async def send_regular_dawn_start_dm(self, recipient):
        player = BOTCUtils.get_player_from_id(recipient.id)
        if player.apparent_death_phase_id == globvars.master_state.game._chrono.phase_id - 1:
            await self.send_ability_prompt(recipient)
