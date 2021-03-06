"""Contains the Character class"""

import json
import discord
import botutils
import datetime
import configparser
from .Category import Category
from .Team import Team
from .errors import AlreadyDead
from .BOTCUtils import LorePicker, InvalidGossipStatement, GameLogic
from .flag_inventory import Inventory, Flags
from .abilities import ActionTypes, Action
from .status import StatusList
from botutils import BotEmoji
import globvars

Preferences = configparser.ConfigParser()

Preferences.read("preferences.INI")

TOWNSFOLK_COLOR = Preferences["colors"]["TOWNSFOLK_COLOR"]
OUTSIDER_COLOR = Preferences["colors"]["OUTSIDER_COLOR"]
MINION_COLOR = Preferences["colors"]["MINION_COLOR"]
DEMON_COLOR = Preferences["colors"]["DEMON_COLOR"]

TOWNSFOLK_COLOR = int(TOWNSFOLK_COLOR, 16)
OUTSIDER_COLOR = int(OUTSIDER_COLOR, 16)
MINION_COLOR = int(MINION_COLOR, 16)
DEMON_COLOR = int(DEMON_COLOR, 16)

Config = configparser.ConfigParser()
Config.read('config.INI')

DISABLE_DMS = Config["misc"].get("DISABLE_DMS", "").lower() == "true"
PREFIX = Config["settings"]["PREFIX"]

with open('botc/game_text.json') as json_file: 
    strings = json.load(json_file)
    copyrights_str = strings["misc"]["copyrights"]
    role_dm = strings["gameplay"]["role_dm"]
    welcome_dm = strings["gameplay"]["welcome_dm"]
    blocked = strings["gameplay"]["blocked"]
    statement_unrecognized = strings["cmd_warning"]["statement_unrecognized"]

x_emoji = BotEmoji.cross

class Character:
    """Character class
    Methods starting with "playtest" are used for console game creation for playtesting purposes.
    """
    
    def __init__(self):

        # Parent attributes
        self._main_wiki_link = "https://bloodontheclocktower.com/wiki/Main_Page"  # Main page url -> string
        self._botc_demon_link = "https://bloodontheclocktower.com/img/website/demon-head.png?" \
                              "rel=1589188746616"  # Demon head art url -> string
        self._botc_logo_link = "https://bloodontheclocktower.com/wiki/images/logo.png"  # Logo art url -> string

        # Override by child role class:
        self._desc_string = None
        self._examp_string = None
        self._instr_string = None
        self._lore_string = None
        self._brief_string = None
        self._action = None
        self._art_link = None
        self._art_link_cropped = None
        self._wiki_link = None
        self._role_enum = None
        self._true_role = self
        self._ego_role = self
        self._social_role = self
        self.inventory = Inventory(
            Flags.slayer_unique_attempt
        )

        # Override by gamemode class
        self._gm_of_appearance = None
        self._gm_art_link = None

        # Override by category class
        self._category = None
        self._team = None

        # Other
        self._emoji = None
        self._demon_head_emoji = "<:demonhead:736692927505367190>"
    
    # -------------------- Character Properties --------------------
    
    def is_good(self):
        """Return True if the character is on the good team, False otherwise"""
        return self.team == Team.good
    
    def is_evil(self):
        """Return True if the character is on the evil team, False otherwise"""
        return self.team == Team.evil
    
    @property
    def true_self(self):
        """Layers of Role Identity:
        1. true_self = what the game uses for win-con computations
        """
        return self._true_role

    @property
    def ego_self(self):
        """Layers of Role Identity:
        2. ego_self = what the player thinks they are
        """
        return self._ego_role

    @property
    def social_self(self):
        """Layers of Role Identity:
        3. social_self = what the other players think the player is
        """
        return self._social_role
    
    def set_new_true_self(self):
        return
    
    def set_new_ego_self(self):
        return
    
    def set_new_social_self(self, player):
        return
    
    @property
    def emoji(self):
        return self._emoji
    
    @property
    def demon_head_emoji(self):
        return self._demon_head_emoji
    
    @property
    def main_wiki_link(self):
        return self._main_wiki_link
    
    @property
    def botc_demon_link(self):
        return self._botc_demon_link
    
    @property
    def botc_logo_link(self):
        return self._botc_logo_link
    
    @property
    def description(self):
        return self._desc_string
    
    @property
    def examples(self):
        return self._examp_string
    
    @property
    def instruction(self):
        return self._instr_string
    
    @property
    def lore(self):
        return self._lore_string
    
    @property
    def brief(self):
        return self._brief_string
    
    @property
    def action(self):
        return self._action
    
    @property
    def art_link(self):
        return self._art_link
    
    @property
    def wiki_link(self):
        return self._wiki_link

    @property
    def name(self):
        return self._role_enum.value
    
    @property
    def gm_of_appearance(self):
        return self._gm_of_appearance
    
    @property
    def gm_art_link(self):
        return self._gm_art_link
    
    @property
    def category(self):
        return self._category
    
    @property
    def team(self):
        return self._team
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name + " Obj"
    
    # -------------------- Character Mechanics --------------------

    async def send_role_card_embed(self, ctx):
        """Create the role card embed object and return it"""

        if DISABLE_DMS:
            return

        def make_embed(emote,
                       role_name, 
                       role_category, 
                       card_color, 
                       gm, 
                       gm_art_link, 
                       desc_str, 
                       ex_str, 
                       pic_link, 
                       wiki_link):

            embed = discord.Embed(title = "{} [{}] {}".format(role_name, role_category, emote), 
                                  description = "*{}*".format(self.lore), 
                                  color = card_color)
            embed.set_author(name = "Blood on the Clocktower - {}".format(gm), icon_url = gm_art_link)
            embed.set_thumbnail(url = pic_link)
            embed.add_field(name = ":small_orange_diamond: Description", value = desc_str, inline = False)
            embed.add_field(name = ":small_orange_diamond: Examples", value = ex_str + "\n" + wiki_link, inline = False)
            embed.set_footer(text = copyrights_str)

            return embed

        if self.category == Category.townsfolk:
            color = TOWNSFOLK_COLOR
        elif self.category == Category.outsider:
            color = OUTSIDER_COLOR
        elif self.category == Category.minion:
            color = MINION_COLOR
        elif self.category == Category.demon:
            color = DEMON_COLOR

        gm_art_link = self.gm_art_link if self.gm_art_link else self.botc_logo_link
        pic_link = self.art_link if self.art_link else self.botc_demon_link
        wiki_link = ":paperclip: " + self.wiki_link if self.wiki_link else ":paperclip: " + self.main_wiki_link

        embed = make_embed(self.emoji,
                           self.__str__(), 
                           self.category.value, 
                           color, 
                           self.gm_of_appearance.value, 
                           gm_art_link, 
                           self.description, 
                           self.examples, 
                           pic_link, 
                           wiki_link)
        await ctx.send(embed=embed)

    def exec_init_setup(self, townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list):
        """Allow for roles that change the setup to modify the role list
        Overridden by child classes that do need to modify the setup.
        """
        return [townsfolk_obj_list, outsider_obj_list, minion_obj_list, demon_obj_list] 
    
    def exec_init_role(self, setup):
        """Allow for roles that need to initialize certain status or flags to do so after the setup 
        is generated.
        Overridden by child classes that do need to set flags and initializations.
        """
        return

    def has_finished_night_action(self, player):
        """Has the player finished their night action? (For phase fastforwarding)
        To be overriden in child classes
        """
        return True
    
    def has_finished_dawn_action(self, player):
        """Has the player finished their dawn action? (For phase fastforwarding)
        To be overriden in child classes
        """
        return True

    def can_be_executed(self, player):
        """Can the player be executed?
        Default is to check whether the player has the safety_from_execution status.
        To be overriden in child classes. Should only be called when no other means of death avoidance is possible.
        """
        return not player.has_status_effect(StatusList.safety_from_execution)

    def can_be_demon_killed(self, player):
        """Can the player be demon killed?
        Default is to check if the player has the safety_from_demon status.
        To be overriden in child classes. Should only be called when no other means of death avoidance is possible.
        """
        return not player.has_status_effect(StatusList.safety_from_demon)

    def can_be_killed(self, player):
        """Can the player be killed in any way other than execution or demon kill?
        To be overriden by child classes. Should only be called when no other means of death avoidance is possible.
        """
        return True

    # -------------------- Character DM's --------------------
    
    async def send_opening_dm_embed(self, recipient):
        """Create the opening DM (on game start) embed object and return it"""

        if DISABLE_DMS:
            return

        if self.ego_self.category == Category.townsfolk:
            color = TOWNSFOLK_COLOR  
        elif self.ego_self.category == Category.outsider:
            color = OUTSIDER_COLOR
        elif self.ego_self.category == Category.minion:
            color = MINION_COLOR
        else:
            color = DEMON_COLOR

        opening_dm = role_dm.format(
            user = recipient.name + recipient.discriminator,
            role_name_str = self.ego_self.name,
            category_str = self.ego_self.category.value,
            team_str = self.ego_self.team.value,
            prefix = PREFIX)

        embed = discord.Embed(title = welcome_dm.format(self.ego_self.name.upper()),
                              url = self.ego_self.wiki_link,
                              description=opening_dm, color=color)
        embed.timestamp = datetime.datetime.utcnow()
        embed.add_field(name = "**「 Instruction 」**", value = self.create_n1_instr_str(), inline = True)
        embed.set_author(name = "{} Edition - Blood on the Clocktower (BoTC)".format(self.ego_self.gm_of_appearance.value),
                         icon_url = self.ego_self.gm_art_link)
        embed.set_thumbnail(url = self.ego_self.botc_logo_link)
        embed.set_footer(text = copyrights_str)

        # If we have an evil team member, send evil list (if 7p or more)
        if globvars.master_state.game.nb_players >= 7:
            if self.is_evil():
                msg = globvars.master_state.game.setup.create_evil_team_string()
                embed.add_field(name = "**「 Evil Team 」**", value = msg, inline = True)
        
        # Send the stats list if necessary
        embed = self.add_action_field_n1(embed)

        embed.set_image(url = self.ego_self._art_link_cropped)

        try:
            await recipient.send(embed = embed)
        except discord.Forbidden:
            await botutils.send_lobby(blocked.format(recipient.mention))
            pass

    def add_action_field_n1(self, embed_obj):
        """Process the opening dm to add a field at the end to query for night actions.
        To be overriden by child classes. The default is to add nothing.
        """
        return embed_obj
    
    def create_n1_instr_str(self):
        """Create the instruction field on the n1 D. 
        Must be implemented by all child classes.
        """
        raise NotImplementedError
    
    async def send_n1_end_message(self, recipient):
        """Send n1 end message to a player.
        Override by child classes. The default is to send nothing.
        """
        pass
    
    ## Commented out for inheritence resolution order (RecurringAction class)
    # async def send_regular_night_start_dm(self, recipient):
    #     """Send regular night start DM message to a player, for all nights except for the 
    #     first.
    #     Override by child classes. The default is to send nothing.
    #     """
    #     pass

    async def send_regular_night_end_dm(self, recipient):
        """Send regular night end DM message to a player, for all nights except for the 
        first.
        Override by child classes. The default is to send nothing.
        """
        pass

    async def send_regular_dawn_start_dm(self, player):
        """Send the query message at dawn for some abilities that take place at dawn.
        Override by child classes. The default is to send nothing.
        """
        pass

    def check_wincon_after_day(self, player):
        """Perform a win con check after the day phase ends.
        Override by child classes.
        """
        return
    
    # -------------------- Event "Listeners" --------------------

    async def on_being_nominated(self, nominator_player, nominated_player):
        """Function that runs after the player is nominated.
        Override by child classes and/or other classes inherited by child classes.
        """
        from botc.gameloops import nomination_loop
        nomination_loop.start(globvars.master_state.game, nominator_player, nominated_player)
    
    async def on_being_executed(self, executed_player):
        """Funtion that runs after the player has been executed.
        Default behaviour is to execute the player's real death (real state)
        Override by child classes and / or other classes inherited by child classes.
        """
        try:
            await executed_player.exec_real_death()
        except AlreadyDead:
            pass
        else:
            game = globvars.master_state.game
            game.today_executed_player = executed_player
    
    async def on_being_demon_killed(self, killed_player):
        """Function that runs after the player has been killed by the demon at night.
        Default behaviour is to make the player die (real death state)
        Override by child classes and / or other classes inherited by child classes.
        """
        try:
            await killed_player.exec_real_death()
        except AlreadyDead:
            pass
        else:
            globvars.master_state.game.night_deaths.append(killed_player)

    async def on_being_targeted(self, targeted_player, action):
        """Function that runs when the player is the target of another player's action
        Default behaviour is to do nothing.
        Override by child classes and / or other classes inherited by child classes
        """
        pass
    
    # -------------------- Character ABILITIES --------------------

    async def process_night_ability(self, player):
        """Process night ability for a character.
        This is the sole function called by the night interaction processing function.
        Default is to do nothing. Override by child classes
        """
        return
    
    async def exec_serve(self, player, targets):
        """Serve command. Override by child classes."""
        raise NotImplementedError

    async def register_serve(self, player, targets):
        """Serve command. Override by child classes"""
        raise NotImplementedError

    async def exec_poison(self, player, targets):
        """Poison command. Override by child classes"""
        raise NotImplementedError

    async def register_poison(self, player, targets):
        """Poison command. Override by child classes"""
        raise NotImplementedError

    async def exec_learn(self, player, targets):
        """Learn command. Override by child classes"""
        raise NotImplementedError

    async def register_learn(self, player, targets):
        """Learn command. Override by child classes"""
        raise NotImplementedError

    async def exec_read(self, player, targets):
        """Read command. Override by child classes"""
        raise NotImplementedError

    async def register_read(self, player, targets):
        """Read command. Override by child classes"""
        raise NotImplementedError

    async def exec_kill(self, player, targets):
        """Kill command. Override by child classes"""
        raise NotImplementedError

    async def register_kill(self, player, targets):
        """Kill command. Override by child classes"""
        raise NotImplementedError

    async def exec_slay(self, slayer_player, slain_player):
        """Execute the slay action (immediate effect)

        The Slayer character will override this to have actual effect.
        All non-slayers characters will be able to use the slay command just like the slayer, 
        but without any consequences for the game.
        """

        # Remove the unique use ability from the player's inventory
        slayer_player.role.ego_self.inventory.remove_item_from_inventory(Flags.slayer_unique_attempt)
        # The ability fails no matter what, because the player is not a slayer
        string = LorePicker().pick(LorePicker().SLAY_FAIL)
        string = string.format(
            slayer = slayer_player.game_nametag, 
            slain = slain_player.game_nametag
        )
        await botutils.send_lobby(string)

    @GameLogic.unique_ability(ActionTypes.slay)
    @GameLogic.requires_one_target
    async def register_slay(self, player, targets):
        """Slay command"""

        # Must be 1 target
        assert len(targets) == 1, "Received a number of targets different than 1 for slayer 'slay'"
        action = Action(player, targets, ActionTypes.slay, globvars.master_state.game._chrono.phase_id)
        player.action_grid.register_an_action(action, globvars.master_state.game._chrono.phase_id)
        await self.exec_slay(player, targets[0])

    async def exec_protect(self, player, targets):
        """Protect command. Override by child classes"""
        raise NotImplementedError

    async def register_protect(self, player, targets):
        """Protect command. Override by child classes"""
        raise NotImplementedError

    async def register_assassinate(self, player, targets):
        """Assassinate command. Override by child classes"""
        raise NotImplementedError

    async def exec_assassinate(self, player, targets):
        """Assassinate command. Override by child classes"""
        raise NotImplementedError

    async def register_see(self, player, targets):
        """See command. Override by child classes"""
        raise NotImplementedError

    async def exec_see(self, player, targets):
        """See command. Override by child classes"""
        raise NotImplementedError

    async def register_exorcise(self, player, targets):
        """Exorcise command. Override by child classes"""
        raise NotImplementedError

    async def exec_exorcise(self, player, targets):
        """Exorcise command. Override by child classes"""
        raise NotImplementedError

    async def register_guess(self, player, targets):
        """Guess command. Override by child classes"""
        raise NotImplementedError

    async def exec_guess(self, player, targets):
        """Guess command. Override by child classes"""
        raise NotImplementedError

    async def register_execute(self, player, targets):
        """Execute command. Override by child classes"""
        raise NotImplementedError

    async def exec_execute(self, player, targets):
        """Execute command. Override by child classes"""
        raise NotImplementedError

    async def register_gossip(self, player, statement):
        """Gossip command.
        Returns True if the statement is true, False otherwise.
        Raises an exception if the statement could not be parsed.
        """
        statement = statement.lower()

        import botutils
        from botc.gamemodes.badmoonrising._utils import BadMoonRising
        from BOTCUtils import BOTCUtils, BMRRolesOnly, bmr_roles_only_str, x_emoji, \
            PlayerNotFound, player_not_found, RoleNotFound # Being lazy and importing these from BOTCUtils

        def player_is_role(args):
            player = BOTCUtils.get_player_from_string(args[0])
            role = botutils.find_role_in_all(args[1])

            if not isinstance(role, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
            if player is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
            if role is None:
                raise RoleNotFound(f"Role {args[1]} not found.")

            return player.role.true_self.name == role.name

        def player_was_role(args):
            role_matches = player_is_role(args)
            
            player = BOTCUtils.get_player_from_string(args[0])

            return player.is_dead() and role_matches

        def player_is_alignement(args):
            player = BOTCUtils.get_player_from_string(args[0])
            guess_good = args[0] == "true"

            if player is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

            return guess_good == player.role.true_self.is_good()

        def player_is_category(args):
            player = BOTCUtils.get_player_from_string(args[0])

            if args[1] == "town" or args[1] == "townsfolk":
                guess_category = Category.townsfolk
            elif args[1] == "outsider":
                guess_category = Category.outsider
            elif args[1] == "minion":
                guess_category = Category.minion
            else:
                guess_category = Category.demon

            if player is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

            return player.role.true_self.category == guess_category
        
        def role_is_ingame(args):
            role = botutils.find_role_in_all(args[0])

            if not isinstance(role, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
            elif role is None:
                raise RoleNotFound(f"Role {args[0]} not found.")

            roles = [player.role.true_self.name for player in globvars.master_state.game.sitting_order]

            return role.name in roles

        
        statement_checks = [
            # (match_checker, splitter, validator)

            # <player> is the <role>
            (r".+ is the .+", r".+(?= is the)|(?<=is the ).+", player_is_role),
            # <player> is <role>
            (r".+ is .+", r".+(?= is)|(?<=is ).+", player_is_role),
            # <player> was <role>
            (r".+ was .+", r".+(?= was)|(?<=was ).+", player_was_role),

            # <player> is <alignement>
            (r".+ is (good|evil)", r".+(?= is )|(?<= is ).+", player_is_alignement),

            # <player> is <category>
            (r".+ is (town|townsfolk|outsider|minion|demon)", r".+(?= is )|(?<= is ).+", player_is_category),
            # <player> is an <category>
            (r".+ is an (town|townsfolk|outsider|minion|demon)", r".+(?= is an )|(?<= is an ).+", player_is_category),
            # <player> is a <category>
            (r".+ is a (town|townsfolk|outsider|minion|demon)", r".+(?= is a )|(?<= is a ).+", player_is_category),

            # (the) <role> is in game
            (r"(the |).+ is in game", r"^(?!the ).+(?= is in game)|(?<=the ).+(?= is in game)", role_is_ingame),
            # (the) <role> is ingame
            (r"(the |).+ is ingame", r"^(?!the ).+(?= is ingame)|(?<=the ).+(?= is ingame)", role_is_ingame),
            # (the) <role> is in-game
            (r"(the |).+ is in-game", r"^(?!the ).+(?= is in-game)|(?<=the ).+(?= is in-game)", role_is_ingame),
            # (the) <role> is in play
            (r"(the |).+ is in play", r"^(?!the ).+(?= is in play)|(?<=the ).+(?= is in play)", role_is_ingame),

            # (the) <role> is not in game
            (r"(the |).+ is not in game", r"^(?!the ).+(?= is not in game)|(?<=the ).+(?= is not in game)", lambda args: not role_is_ingame(args)),
            # (the) <role> is not ingame
            (r"(the |).+ is not ingame", r"^(?!the ).+(?= is not ingame)|(?<=the ).+(?= is not ingame)", lambda args: not role_is_ingame(args)),
            # (the) <role> is not in-game
            (r"(the |).+ is not in-game", r"^(?!the ).+(?= is not in-game)|(?<=the ).+(?= is not in-game)", lambda args: not role_is_ingame(args)),
            # (the) <role> is not in play
            (r"(the |).+ is not in play", r"^(?!the ).+(?= is not in play)|(?<=the ).+(?= is not in play)", lambda args: not role_is_ingame(args)),

            # there (are|is) <n> outsider(s) in play
            # there (are|is) <n> (town|townsfolk) in play
            # there (are|is) <n> minion(s) in play
            # there (are|is) <n> demon(s)

            # <player> is neighbouring <player>
            # <player> is <player>'s neighbour
            # <player> has <player> as a neighbour

            # <player> has <player> as an alive neighbour

            # <player> is neighbouring (the) <role>
            # <player> is (the) <role>'s neighbour
            # <player> has (the) <role> as a neighbour

            # (the) <role> is neighbouring (the) <role>
            # (the) <role> is (the) <role>'s neighboir
            # (the) <role> has (the) <role> as a neighbour

            # (the) <role> is neighbouring <player>
            # (the) <role> is <player>'s neighbour
            # (the) <role> has <player> as a neighbour

            # (the) <role> whispered today
            # (the) <role> has whispered today

            # (the) <role> has whispered

            # (the) <role> has whispered to <player> today
            # (the) <role> whispered to <player> today

            # (the) <role> has whispered to <player>

            # (the) <role> has whispered to (the) <role> today
            # (the) <role> whispered to (the) <role> today

            # (the) <role> has whispered to (the) <role>

            # <player> has whispered to (the) <role> today
            # <player> whispered to (the) <role> today

            # <player> has whispered to (the) <role>

            # <player> has whispered to <player> today
            # <player> whispered to <player> today

            # <player> has whispered to <player>

            # (the) <role> has used their ability tonight
            # (the) <role> has used their ability
            # (the) <role> used their ability tonight
            # (the) <role> used their ability

            # <player> has used their ability tonight
            # <player> has used their ability
            # <player> used their ability tonight
            # <player> used their ability

            # (the) <role>'s name contains <c>
            # (the) <role>'s nickname contains <c>

            # (the) <role> is (dead|alive)

        ]

        import re

        for check in statement_checks:
            match_checker = re.compile(check[0], re.IGNORECASE)
            if bool(match_checker.fullmatch(statement)):
                splitter = re.compile(check[1], re.IGNORECASE)
                return check[2](splitter.findall(statement))

        raise InvalidGossipStatement(statement_unrecognized.format(player.user.mention, x_emoji))

    async def exec_gossip(self, player, statement_truth):
        """Gossip command. Override by child classes"""
        raise NotImplementedError