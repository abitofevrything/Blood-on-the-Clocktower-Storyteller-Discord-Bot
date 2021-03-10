"""Contains the Godfather Character class"""

import json
import random
import globvars
import discord
import datetime
import botutils
import configparser
from botc import Character, Minion, RecurringAction, BOTCUtils, Outsider, Townsfolk, ActionTypes, GameLogic, Action, AlreadyDead
from ._utils import BadMoonRising, BMRRole

with open('botc/gamemodes/badmoonrising/character_text.json') as json_file: 
    character_text = json.load(json_file)[BMRRole.godfather.value.lower()]

with open('botc/game_text.json') as json_file: 
    strings = json.load(json_file)
    copyrights_str = strings["misc"]["copyrights"]

butterfly = botutils.BotEmoji.butterfly

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"

class Godfather(Minion, BadMoonRising, Character, RecurringAction):
    """Godfather: You start knowing which Outsiders are in-play. If 1 died today, 
    choose a player tonight: they die. [-1 or +1 Outsider]
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

        self._art_link = "https://bloodontheclocktower.com/wiki/images/e/ef/Godfather_Token.png"
        self._art_link_cropped = "https://imgur.com/7JlfMLc.png"
        self._wiki_link = "https://bloodontheclocktower.com/wiki/Godfather"

        self._role_enum = BMRRole.godfather
        self._emoji = "<:bmrgodfather:781151556204625930>"

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

    def has_finished_night_action(self, player):
        """Return True if godfather has submitted the godfather action or if an outsider was not executed today"""
        executed_today = globvars.master_state.game.today_executed_player

        if executed_today is None:
            return True
        elif not isinstance(executed_today.role.true_self, Outsider):
            return True
        else:
            if player.is_alive():
                current_phase_id = globvars.master_state.game._chrono.phase_id
                received_action = player.action_grid.retrieve_an_action(current_phase_id)
                return received_action is not None and received_action.action_type == ActionTypes.execute
            return True

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""

        # For godfather, only send DM if Outsider was executed today

        print(f"Godfather : in send_dm method")

        executed_today = globvars.master_state.game.today_executed_player

        print(f"Godfather : executed today is {executed_today}")

        if executed_today is None:
            return
        elif not isinstance(executed_today.role.true_self, Outsider):
            return

        player = BOTCUtils.get_player_from_id(recipient.id)

        if player.is_alive():

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
            embed.add_field(name = butterfly + " **「 Your Action 」**", value = msg2, inline = False)
            
            try:
                await recipient.send(embed = embed)
            except discord.Forbidden:
                pass

    def exec_init_setup(self, townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list):
        """Add or remove one outsider from the setup"""
        
        if random.choice([True, False]) or len(outsider_obj_list) is 0:
            # +1 Outsider

            townsfolk_obj_list.pop()

            bmr_outsider_all = BOTCUtils.get_role_list(BadMoonRising, Outsider)

            for outsider in bmr_outsider_all:
                if str(outsider) not in [str(role) for role in outsider_obj_list]:
                    outsider_obj_list.append(outsider)
                    break

            return [townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list]
        else:
            # -1 Outsider

            outsider_obj_list.pop()

            bmr_townsfolk_all = BOTCUtils.get_role_list(BadMoonRising, Townsfolk)

            for townsfolk in bmr_townsfolk_all:
                if str(townsfolk) not in [str(role) for role in townsfolk_obj_list]:
                    townsfolk_obj_list.append(townsfolk)
                    break

            return [townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list]

    @GameLogic.requires_one_target
    @GameLogic.changes_not_allowed
    async def register_execute(self, player, targets):
        """Execute command"""

        # Ignore command if godfather shouldn't execute tonight

        executed_today = globvars.master_state.game.today_executed_player

        if executed_today is None:
            return
        elif not isinstance(executed_today.role.true_self, Outsider):
            return

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for godfather 'execute'"
        action = Action(player, targets, ActionTypes.execute, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)

        if DISABLE_DMS:
            return

        msg = butterfly + " " + character_text["feedback"].format(targets[0].game_nametag)
        await player.user.send(msg)

    async def exec_execute(self, player, killed_player):
        if player.is_alive() and not player.is_droisoned():
            if  killed_player.role.true_self.can_be_killed(killed_player):
                try:
                    await killed_player.exec_real_death()
                except AlreadyDead:
                    pass
                else:
                    globvars.master_state.game.night_deaths.append(killed_player)

    async def process_night_ability(self, player):
        """Process night actions for the exorcist character.
        @player : the Godfather player (Player object)
        """

        phase = globvars.master_state.game._chrono.phase_id
        action = player.action_grid.retrieve_an_action(phase)
        # The godfather has submitted an action. We call the execution function immediately
        if action:
            assert action.action_type == ActionTypes.execute, f"Wrong action type {action} in exorcist"
            targets = action.target_player
            exorcised_player = targets[0]
            await self.exec_execute(player, exorcised_player)
        # The godfather has not submitted an action. We will not randomize the action because this 
        # is a priviledged ability
        else:
            pass
