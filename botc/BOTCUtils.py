"""Contains some BoTC game related utility functions"""

import asyncio
import json
import configparser
import random
import globvars
from .Category import Category
from discord.ext import commands, tasks

Config = configparser.ConfigParser()
Config.read("config.INI")

MAX_MESSAGE_LEN = Config["misc"]["MAX_MESSAGE_LEN"]
MAX_MESSAGE_LEN = int(MAX_MESSAGE_LEN)

with open('botc/game_text.json') as json_file:
    documentation = json.load(json_file)
    x_emoji = documentation["cmd_warnings"]["x_emoji"]
    player_not_found = documentation["cmd_warnings"]["player_not_found"]
    no_self_targetting_str = documentation["cmd_warnings"]["no_self_targetting_str"]
    except_first_night_str = documentation["cmd_warnings"]["except_first_night_str"]
    requires_one_target_str = documentation["cmd_warnings"]["requires_one_target_str"]
    requires_two_targets_str = documentation["cmd_warnings"]["requires_two_targets_str"]
    requires_different_targets_str = documentation["cmd_warnings"]["requires_different_targets_str"]
    changes_not_allowed = documentation["cmd_warnings"]["changes_not_allowed"]
    unique_ability_used = documentation["cmd_warnings"]["unique_ability_used"]
    not_under_status = documentation["cmd_warnings"]["not_under_status"]
    lore = documentation["lore"]
    bmr_roles_only_str = documentation["cmd_warnings"]["bmr_roles_only"]
    no_same_following_targets_str = documentation["cmd_warnings"]["no_same_following_targets"]
    statement_unrecognized = documentation["cmd_warnings"]["statement_unrecognized"]


# ========== TARGETS ===============================================================
# ----------------------------------------------------------------------------------

class Targets(list):
    """Targets class for storing BoTC characters' targets"""

    def __init__(self, target_list):
        self.target_list = target_list
        self.target_nb = len(self.target_list)

    def __len__(self):
        return len(self.target_list)

    def __iter__(self):
        yield from self.target_list

    def __getitem__(self, index):
        return list.__getitem__(self.target_list, index)

class PlayerWhisper():
    """Class to represent a player whisper"""

    def __init__(self, source_player, target_player, message, phase_id):
        self.source_player = source_player
        self.target_player = target_player
        self.message = message
        self.phase_id = phase_id



def get_number_image(nb):
    """Get a random bloodied number image corresponding to the input integer"""
    assert nb in [1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "Number received is not a digit"
    numbers = documentation["numbers"]
    possibilities = numbers[str(nb)]
    chosen = random.choice(possibilities)
    return chosen

def validate_statement(player, statement):
    statement = statement.lower()

    import botutils
    from botc.gamemodes.badmoonrising._utils import BadMoonRising
    from BOTCUtils import BOTCUtils, BMRRolesOnly, bmr_roles_only_str, x_emoji, \
        PlayerNotFound, player_not_found, RoleNotFound # Being lazy and importing these from BOTCUtils
    from botc import Player, Character

    def player_is_role(args):
        player = BOTCUtils.get_player_from_string(args[0])
        role = botutils.find_role_in_all(args[1])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        if player is None:
            raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        if role is None:
            raise RoleNotFound(f"Role {args[1]} not found.")

        return player.role.social_self.name == role.name

    def player_was_role(args):
        role_matches = player_is_role(args)
        
        player = BOTCUtils.get_player_from_string(args[0])

        return player.is_apparently_dead() and role_matches

    def player_is_alignement(args):
        player = BOTCUtils.get_player_from_string(args[0])
        guess_good = args[0] == "true"

        if player is None:
            raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        return guess_good == player.role.social_self.is_good()

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

        return player.role.social_self.category == guess_category
    
    def role_is_ingame(args):
        role = botutils.find_role_in_all(args[0])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        elif role is None:
            raise RoleNotFound(f"Role {args[0]} not found.")

        roles = [player.role.social_self.name for player in globvars.master_state.game.sitting_order]

        return role.name in roles

    def n_category_in_game(args):
        num = int(args[0])

        actual_num_demons = 0
        actual_num_minions = 0
        actual_num_town = 0
        actual_num_outsider = 0

        for player in globvars.master_state.game.sitting_order:
            pcategory = player.role.social_self.category
            if pcategory == Category.townsfolk:
                actual_num_town = actual_num_town + 1
            elif pcategory == Category.outsider:
                actual_num_outsider = actual_num_outsider + 1
            elif pcategory == Category.minion:
                actual_num_minions = actual_num_minions + 1
            else:
                actual_num_demons = actual_num_demons + 1

        if args[0] == "town" or args[0] == "townsfolk":
            return num == actual_num_town
        elif args[0] == "outsider":
            return num == actual_num_outsider
        elif args[0] == "minion":
            return num == actual_num_minions
        else:
            return num == actual_num_demons
    
    def less_than_n_category(args):
        num = int(args[0])

        actual_num_demons = 0
        actual_num_minions = 0
        actual_num_town = 0
        actual_num_outsider = 0

        for player in globvars.master_state.game.sitting_order:
            pcategory = player.role.social_self.category
            if pcategory == Category.townsfolk:
                actual_num_town = actual_num_town + 1
            elif pcategory == Category.outsider:
                actual_num_outsider = actual_num_outsider + 1
            elif pcategory == Category.minion:
                actual_num_minions = actual_num_minions + 1
            else:
                actual_num_demons = actual_num_demons + 1

        if args[0] == "town" or args[0] == "townsfolk":
            return num < actual_num_town
        elif args[0] == "outsider":
            return num < actual_num_outsider
        elif args[0] == "minion":
            return num < actual_num_minions
        else:
            return num < actual_num_demons

    def more_than_n_category(args):
        num = int(args[0])

        actual_num_demons = 0
        actual_num_minions = 0
        actual_num_town = 0
        actual_num_outsider = 0

        for player in globvars.master_state.game.sitting_order:
            pcategory = player.role.social_self.category
            if pcategory == Category.townsfolk:
                actual_num_town = actual_num_town + 1
            elif pcategory == Category.outsider:
                actual_num_outsider = actual_num_outsider + 1
            elif pcategory == Category.minion:
                actual_num_minions = actual_num_minions + 1
            else:
                actual_num_demons = actual_num_demons + 1

        if args[0] == "town" or args[0] == "townsfolk":
            return num > actual_num_town
        elif args[0] == "outsider":
            return num > actual_num_outsider
        elif args[0] == "minion":
            return num > actual_num_minions
        else:
            return num > actual_num_demons

    def neighbour_check(args):
        arg1 = botutils.find_role_in_all(args[0])
        if arg1 is None:
            arg1 = BOTCUtils.get_player_from_string(args[0])
            if arg1 is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        else:
            if not isinstance(arg1, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))

        arg2 = botutils.find_role_in_all(args[1])
        if arg2 is None:
            arg2 = BOTCUtils.get_player_from_string(args[1])
            if arg2 is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        else:
            if not isinstance(arg2, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji)) 

        if isinstance(arg1, Player) and isinstance(arg2, Player):
            return abs(globvars.master_state.game.sitting_order.index(arg1) - globvars.master_state.game.sitting_order.index(arg2)) == 1
        elif isinstance(arg1, Character) and isinstance(arg2, Player):
            i = globvars.master_state.game.sitting_order.index(arg2)
            l = len(globvars.master_state.game.sitting_order)
            return globvars.master_state.game.sitting_order[(i + 1) % l].role.social_self.name == arg1.name or globvars.master_state.game.sitting_order[(i - 1) % l].role.social_self.name == arg1.name
        elif isinstance(arg1, Player) and isinstance(arg2, Character):
            i = globvars.master_state.game.sitting_order.index(arg1)
            l = len(globvars.master_state.game.sitting_order)
            return globvars.master_state.game.sitting_order[(i + 1) % l].role.social_self.name == arg2.name or globvars.master_state.game.sitting_order[(i - 1) % l].role.social_self.name == arg2.name
        else:
            l = len(globvars.master_state.game.sitting_order)
            so = globvars.master_state.game.sitting_order
            for i in range(l + 1):
                if (so[i % l].role.social_self.name == arg1.name and so[(i + 1) % l].role.social_self.name == arg2.name) or (so[i % l].role.social_self.name == arg2.name and so[(i + 1) % l].role.social_self.name == arg1.name):
                    return True
            return False

    def today_whispered(args):
        game = globvars.master_state.game
        day_phase_id = game._chrono.phase_id % 3
        today_whispers = [whisper for whisper in game.whispers if whisper.phase_id == day_phase_id]

        arg = botutils.find_role_in_all(args[0])
        if arg is not None:
            if not isinstance(arg, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg = BOTCUtils.get_player_from_string(args[0])
            if arg is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        
        if isinstance(arg, Character):
            for whisper in today_whispers:
                if whisper.source_player.role.social_self.name == arg.name:
                    return True
            return False
        else:
            for whisper in today_whispers:
                if whisper.source_player.user.id == arg.user.id:
                    return True
            return False

    def whispered(args):
        game = globvars.master_state.game

        arg = botutils.find_role_in_all(args[0])
        if arg is not None:
            if not isinstance(arg, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg = BOTCUtils.get_player_from_string(args[0])
            if arg is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        
        if isinstance(arg, Character):
            for whisper in game.whisperes:
                if whisper.source_player.role.social_self.name == arg.name:
                    return True
            return False
        else:
            for whisper in game.whispers:
                if whisper.source_player.user.id == arg.user.id:
                    return True
            return False

    def whispered_to_today(args):
        game = globvars.master_state.game
        day_phase_id = game._chrono.phase_id % 3
        today_whispers = [whisper for whisper in game.whispers if whisper.phase_id == day_phase_id]

        arg1 = botutils.find_role_in_all(args[0])
        if arg1 is not None:
            if not isinstance(arg1, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg1 = BOTCUtils.get_player_from_string(args[0])
            if arg1 is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        arg2 = botutils.find_role_in_all(args[1])
        if arg2 is not None:
            if not isinstance(arg1, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg2 = BOTCUtils.get_player_from_string(args[1])
            if arg2 is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        
        if isinstance(arg1, Character) and isinstance(arg2, Character):
            for whisper in today_whispers:
                if whisper.source_player.role.social_self.name == arg1.name and whisper.target_player.role.social_self.name == arg2.name:
                    return True
                return False
        elif isinstance(arg1, Player) and isinstance(arg2, Character):
            for whisper in today_whispers:
                if whisper.source_player.user.id == arg1.user.id and whisper.target_player.role.social_self.name == arg2.name:
                    return True
            return False
        elif isinstance(arg1, Character) and isinstance(arg2, Player):
            for whisper in today_whispers:
                if whisper.target_player.user.id == arg2.user.id and whisper.source_player.role.social_self.name == arg1.name:
                    return True
            return False
        else:
            for whisper in today_whispers:
                if whisper.source_player.user.id == arg1.user.id and whisper.target_player.user.id == arg2.user.id:
                    return True
            return False
        
    def whispered_to(args):
        game = globvars.master_state.game
        whispers = game.whispers

        arg1 = botutils.find_role_in_all(args[0])
        if arg1 is not None:
            if not isinstance(arg1, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg1 = BOTCUtils.get_player_from_string(args[0])
            if arg1 is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        arg2 = botutils.find_role_in_all(args[1])
        if arg2 is not None:
            if not isinstance(arg1, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg2 = BOTCUtils.get_player_from_string(args[1])
            if arg2 is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))
        
        if isinstance(arg1, Character) and isinstance(arg2, Character):
            for whisper in whispers:
                if whisper.source_player.role.social_self.name == arg1.name and whisper.target_player.role.social_self.name == arg2.name:
                    return True
                return False
        elif isinstance(arg1, Player) and isinstance(arg2, Character):
            for whisper in whispers:
                if whisper.source_player.user.id == arg1.user.id and whisper.target_player.role.social_self.name == arg2.name:
                    return True
            return False
        elif isinstance(arg1, Character) and isinstance(arg2, Player):
            for whisper in whispers:
                if whisper.target_player.user.id == arg2.user.id and whisper.source_player.role.social_self.name == arg1.name:
                    return True
            return False
        else:
            for whisper in whispers:
                if whisper.source_player.user.id == arg1.user.id and whisper.target_player.user.id == arg2.user.id:
                    return True
            return False

    def ability_used_tonight(args):
        arg = botutils.find_role_in_all(args[0])
        if arg is not None:
            if not isinstance(arg, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg = BOTCUtils.get_player_from_string(args[0])
            if arg is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        last_night_phase = globvars.master_state.game._chrono.phase_id % 3 - 2

        if isinstance(arg, Player):
            action = arg.action_grid.retrieve_an_action(last_night_phase)
            return action is not None
        else:
            for player in globvars.master_state.game.sitting_order:
                if player.role.social_self.name == arg.name:
                    action = player.action_grid.retrieve_an_action(last_night_phase)
                    if action is not None:
                        return True
            return False

    def ability_used(args):
        arg = botutils.find_role_in_all(args[0])
        if arg is not None:
            if not isinstance(arg, BadMoonRising):
                raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        else:
            arg = BOTCUtils.get_player_from_string(args[0])
            if arg is None:
                raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        night_phase = globvars.master_state.game._chrono.phase_id % 3 - 2
        while night_phase >= 0:
            if isinstance(arg, Player):
                action = arg.action_grid.retrieve_an_action(night_phase)
                if action is not None:
                    return True
            else:
                for player in globvars.master_state.game.sitting_order:
                    if player.role.social_self.name == arg.name:
                        action = player.action_grid.retrieve_an_action(night_phase)
                        if action is not None:
                            return True
        
            night_phase = night_phase - 3

        return False

    def name_contains(args):
        role = botutils.find_role_in_all(args[0])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        elif role is None:
            raise RoleNotFound(f"Role {args[0]} not found.")

        players = BOTCUtils.get_players_from_role_name(role._role_enum)

        for player in players:
            if args[1] in player.user.name or args[1] in player.user.nick:
                return True
        return False

    def role_status(args):
        role = botutils.find_role_in_all(args[0])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        elif role is None:
            raise RoleNotFound(f"Role {args[0]} not found.")

        players = BOTCUtils.get_players_from_role_name(role._role_enum)

        if args[1] == "alive":
            for player in players:
                if player.is_apparenty_alive():
                    return True
            return False
        else:
            for player in players:
                if player.is_apparenty_dead():
                    return True
            return False

    def n_alive_players(args):
        num = int(args[0])
        return num == len([p for p in globvars.master_state.game.sitting_order is p.is_apparently_alive()])

    statement_checks = [
        # (match_checker, splitter, validator)

        # <player> is (the) <role>
        # <player> is <role>
        (r".+ is (the |).+", r".+(?= is)|(?<= is )(?!the ).+(?=$)|()(?<= is the).+(?=$)", player_is_role),

        # <player> was (the) <role>
        (r".+ was .+", r".+(?= was)|(?<=was ).+", player_was_role),

        # <player> is <alignement>
        (r".+ is (good|evil)", r".+(?= is )|(?<= is ).+", player_is_alignement),

        # <player> is <category>
        # <player> is an <category>
        # <player> is a <category>
        (r".+ is (a |an |)(town|townsfolk|outsider|minion|demon)", r"^.+(?= is (a |an |))|(?<= is )(?!(a |an )).+(?=$)|(?<= is a )(?!an ).+(?=$)|(?<= is an )(?!a ).+(?=$)", player_is_category),

        # (the) <role> is in game
        # (the) <role> is ingame
        # (the) <role> is in-game
        # (the) <role> is in play
        (r"(the |).+ is (in game|in-game|ingame|in play)", r"^(?!the ).+(?= is (in game|in-game|ingame|in play))|(?<=the ).+(?= is (in game|in-game|ingame|in play))", role_is_ingame),

        # (the) <role> is not in game
        # (the) <role> is not ingame
        # (the) <role> is not in-game
        # (the) <role> is not in play
        (r"(the |).+ is not (in game|in-game|ingame|in play)", r"^(?!the ).+(?= is not (in game|in-game|ingame|in play))|(?<=the ).+(?= is not (in game|in-game|ingame|in play))", lambda args: not role_is_ingame(args)),

        # there (are|is) <n> outsider(s) in play
        # there (are|is) <n> (town|townsfolk) in play
        # there (are|is) <n> minion(s) in play
        # there (are|is) <n> demon(s) in play
        (r"there (is|are) [0-9]+ (town|townsfolk|outsider|minion|demon)(s|) (in game|in-game|ingame|in play)", r"[0-9]+(?= (demon|town|townsfolk|minion|outsider))|(?<=[0-9] ).+(?<!s)(?=(s | )(in game|in-game|ingame|in play))", n_category_in_game),

        # there (are|is) less than <n> (town|townsfolk) in play
        # there (are|is) less than <n> outsider(s) in play
        # there (are|is) less than <n> minion(s) in play
        # there (are|is) less than <n> demon(s) in play
        (r"there (is|are) less than [0-9]+ (town|townsfolk|outsider|minion|demon)(s|) (in game|in-game|ingame|in play)", r"[0-9]+(?= (demon|town|townsfolk|minion|outsider))|(?<=[0-9] ).+(?<!s)(?=(s | )(in game|in-game|ingame|in play))", less_than_n_category),

        # there (are|is) more than <n> (town|townsfolk) in play
        # there (are|is) more than <n> outsider(s) in play
        # there (are|is) more than <n> minion(s) in play
        # there (are|is) more than <n> demon(s) in play
        (r"there (is|are) more than [0-9]+ (town|townsfolk|outsider|minion|demon)(s|) (in game|in-game|ingame|in play)", r"[0-9]+(?= (demon|town|townsfolk|minion|outsider))|(?<=[0-9] ).+(?<!s)(?=(s | )(in game|in-game|ingame|in play))", more_than_n_category),

        # (the) <player/role> is neighbouring (the) <player/role>
        # (the) <player/role> is (the) <player/role>'s neighbour
        # (the) <player/role> has (the) <player/role> as a neighbour

        (r"(.+ is neighbouring .+)|(.+ is .+'s neighbour)|(.+ has .+ as a neighbour)", r"^(?!the).+(?= (is neighbouring |is |has ))|(?<=the ).+(?= (is neighbouring |is |has ))|(?<=is neighbouring )(?!the).+|(?<=is neighbouring the ).+|(?<=is )(?!the ).+(?='s neighbour)|(?<=is the ).+(?='s neighbour)|(?<=has )(?!the).+(?= as a neighbour)|(?<=has the ).+(?= as a neighbour)", neighbour_check),

        # (the) <role/player> whispered today
        # (the) <role/player> has whispered today
        (r"(the |).+ (has |)whispered today", r"^(?!the ).+(?<! has)(?= whispered today)|(?<=the ).+(?<! has)(?= whispered today)|^(?!the ).+(?= has whispered today)|(?<=the ).+(?= has whispered today)", today_whispered),

        # (the) <role/player> has whispered
        (r"(the |).+ has whispered( this game|(?!.+))", r"^(?!the ).+(?= has whispered)|(?<=the ).+(?= has whispered)", whispered),

        # (the) <role/player> has whispered to (the) <role/player> today
        # (the) <role/player> whispered to (the) <role/player> today
        (r"(the |).+ (has whispered|whispered) to (the |).+ today", r"^(?!the ).+(?=( whispered to| has whispered to))|(?<=the ).+(?=( whispered to| has whispered to))|(?<=to the ).+(?= today)|(?<=to )(?!the ).+(?= today)", whispered_to_today),

        # (the) <role/player> has whispered to (the) <role/player>
        # (the) <role/player> whispered to (the) <role/player>
        (r"(the |).+(has whispered to|whispered to) (the |).+", r"^(?!the ).+(?= has whispered to| whispered to)|(?<=the ).+(?= has whispered to| whispered to)|(?<= whispered to )(?!the ).+|(?<= whispered to the ).+", whispered_to),

        # (the) <role> has used their ability tonight
        # (the) <role> used their ability tonight
        # <player> used their ability tonight
        # <player> has used their ability tonight
        (r"(the |).+ (has |)used (their|his|her) ability tonight", r"^(?!the ).+(?<! has)(?= (has |)used (their|his|her) ability tonight)|(?<=the ).+(?<! has)(?= (has |)used (their|his|her) ability tonight)", ability_used_tonight),

        # (the) <role> has used their ability
        # (the) <role> used their ability
        # <player> has used their ability
        # <player> used their ability
        (r"(the |).+ (has |)used (their|his|her) ability(?! tonight)", r"^(?!the ).+(?<! has)(?= (has |)used (their|his|her) ability)|(?<=the ).+(?<! has)(?= (has |)used (their|his|her) ability)", ability_used),

        # (the) <role>'s name contains <c>
        # (the) <role>'s nickname contains <c>
        (r"(the |).+'s (name|nickname) contains (the character |the char |).", r"^(?!the ).+(?='s (name|nickname) contains)|(?<=the).+(?='s (name|nickname) contains)|.(?=$)", name_contains),

        # (the) <role> is (dead|alive)
        (r"(the |).+ is (alive|dead)", r"^(?!the ).+(?= is (alive|dead))|(?<=the ).+(?= is (alive|dead))", role_status),

        # there are <n> players alive
        (r"there (are|is) [0-9]+ player(s|) alive", r"[0-9]+(?= player(s|) alive)", n_alive_players),
        # there are <n> alive player
        (r"there (is|are) [0-9]+ alive player(s|)", r"[0-9]+(?= alive player(s|))", n_alive_players)

    ]

    import re

    for check in statement_checks:
        match_checker = re.compile(check[0], re.IGNORECASE)
        if bool(match_checker.fullmatch(statement)):
            splitter = re.compile(check[1], re.IGNORECASE)
            return check[2](splitter.findall(statement))

    raise InvalidGossipStatement(statement_unrecognized.format(player.user.mention, x_emoji))

class BOTCUtils:
    """Some utility functions"""

    @staticmethod
    def has_alive_demons():
        """Return true if the game still has alive demons. Using real life state."""
        import globvars
        game = globvars.master_state.game
        for player in game.sitting_order:
            if player.is_alive():
                if player.role.true_self.category == Category.demon:
                    return True
        return False

    @staticmethod
    def get_players_from_role_name(character_name_enum):
        """Return the list of players holding a certain character, using ego_self"""
        import globvars
        game = globvars.master_state.game
        ret = []
        for player in game.sitting_order:
            if player.role.ego_self.name == character_name_enum.value:
                ret.append(player)
        return ret

    @staticmethod
    def get_all_minions():
        """Return the list of players that are minions, using true_self"""
        import globvars
        game = globvars.master_state.game
        ret = []
        for player in game.sitting_order:
            if player.role.true_self.category == Category.minion:
                ret.append(player)
        return ret

    @staticmethod
    def get_random_player():
        """Get any random player from the game"""
        import globvars
        game = globvars.master_state.game
        return random.choice(game.sitting_order)

    @staticmethod
    def get_random_player_excluding(player):
        """Get any random player that is not the player passed in the argument"""
        import globvars
        game = globvars.master_state.game
        possibilities = [p for p in game.sitting_order if p.user.id != player.user.id]
        return random.choice(possibilities)

    @staticmethod
    def get_role_list(edition, category):
        """Get the entire list of an edition and a category"""
        return [role_class() for role_class in edition.__subclasses__() if issubclass(role_class, category)]

    @staticmethod
    def get_player_from_id(userid):
        """Find a player object from a user ID"""
        import globvars
        game = globvars.master_state.game
        userid = int(userid)
        for player in game.sitting_order:
            if player.user.id == userid:
                return player

    @staticmethod
    def get_player_from_string(string):
        """Find a player object from user input string.
        Code inspired from belungawhale's discord werewolf project.
        """
        import globvars
        game = globvars.master_state.game
        string = string.lower()
        usernames = []
        discriminators = []
        nicknames = []
        ids_contains = []
        usernames_contains = []
        nicknames_contains = []
        for player in game.sitting_order:
            if string == str(player.user.id) or string.strip('<@!>') == str(player.user.id):
                return player
            if str(player.user).lower().startswith(string):
                usernames.append(player)
            if string.strip('#') == player.user.discriminator:
                discriminators.append(player)
            if player.user.display_name.lower().startswith(string):
                nicknames.append(player)
            if string in player.user.name.lower():
                usernames_contains.append(player)
            if string in player.user.display_name.lower():
                nicknames_contains.append(player)
            if string in str(player.user.id):
                ids_contains.append(player)
        if len(usernames) == 1:
            return usernames[0]
        if len(discriminators) == 1:
            return discriminators[0]
        if len(nicknames) == 1:
            return nicknames[0]
        if len(usernames_contains) == 1:
            return usernames_contains[0]
        if len(nicknames_contains) == 1:
            return nicknames_contains[0]
        if len(ids_contains) == 1:
            return ids_contains[0]
        return None


# ========== CHECK ERRORS ==========================================================
# ----------------------------------------------------------------------------------

class WhisperTooLong(commands.CommandInvokeError):
    """Raised when a command user tries to whisper a message that is too long"""
    pass

class NotAPlayer(commands.CheckFailure):
    """Raised when a command user is not a registered player"""
    pass


class RoleCannotUseCommand(commands.CheckFailure):
    """Raised when a command user doesn't have a character that allows for a command to be used """
    pass


class NotDMChannel(commands.CheckFailure):
    """Raised when a command user used the command in a channel that is not the bot dm"""
    pass


class NotLobbyChannel(commands.CheckFailure):
    """Raised when a command user used the command in a channel that is not the lobby"""
    pass


class NotDay(commands.CheckFailure):
    """Raised when a command user used the command during another phase than
    day when not supposed to
    """
    pass


class NotDawn(commands.CheckFailure):
    """Raised when a command user used the command during another phase than
    dawn when not supposed to
    """
    pass


class NotNight(commands.CheckFailure):
    """Raised when a command user used the command during another phase than
    night when not supposed to
    """
    pass


class DeadOnlyCommand(commands.CheckFailure):
    """Raised when a command user used a command reserved for dead players only."""
    pass


class AliveOnlyCommand(commands.CheckFailure):
    """Raised when a command user used a command reserved for alive players only."""
    pass


# ========== GAME LOGIC ============================================================
# ----------------------------------------------------------------------------------

class AbilityForbidden(commands.errors.CommandInvokeError):
    """Custom parent classes for all the following exceptions"""
    pass


class UniqueAbilityError(AbilityForbidden):
    """Attempt to use unique ability twice in game"""
    pass


class NotUnderStatus(AbilityForbidden):
    """Attempt to use an ability that works only under a certain status effect"""
    pass


class FirstNightNotAllowed(AbilityForbidden):
    """Attempt to use action on first night when not allowed"""
    pass


class ChangesNotAllowed(AbilityForbidden):
    """Attempt to resubmit an action after it's been submitted once during the night"""
    pass


class MustBeOneTarget(AbilityForbidden):
    """Must be exactly one target"""
    pass


class MustBeTwoTargets(AbilityForbidden):
    """Must be exactly two targets"""
    pass


class NoSelfTargetting(AbilityForbidden):
    """Does not allow self targetting in command input"""
    pass


class NoRepeatTargets(AbilityForbidden):
    """Does not allow repeat targets. Ex. kill player1 and player1"""
    pass

class BMRRolesOnly(AbilityForbidden):
    """Error for when a role argument is not from the bmr edition"""
    pass

class NoSameFollowingTargets(AbilityForbidden):
    """Error for when a role that connot choose the same target two times in a row does so"""
    pass

class InvalidGossipStatement(AbilityForbidden):
    """Error for when the gossip submits an invalid or non-recognized statement"""
    pass

class GameLogic:
    """Game logic decorators to be used on ability methods in character classes"""

    @staticmethod
    def no_self_targetting(func):
        """Decorator for abilities that disallow the player to target themself"""
        def inner(self, player, targets):
            for target in targets:
                if target.user.id == player.user.id:
                    raise NoSelfTargetting(no_self_targetting_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def requires_status(status_effect):
        """Decorator for abilities that require the player to be under a specific status.
        Decorator factory that creates decorators based on the status type.

        @status_effect: StatusList enum object
        """
        def decorator(func):
            def inner(self, player, targets):
                if not player.has_status_effect(status_effect):
                    raise NotUnderStatus(not_under_status.format(player.user.mention, x_emoji))
                return func(self, player, targets)
            return inner
        return decorator

    @staticmethod
    def unique_ability(ability_type):
        """Decorator for unique abilities to be used once per game. Decorator factory that
        creates decorators based on the ability type.

        @ability_type: ActionTypes() enum object
        """
        def decorator(func):
            def inner(self, player, targets):
                from botc import Flags, ActionTypes
                # Slayer's unique "slay" ability. Everyone may use it publicy once.
                if ability_type == ActionTypes.slay:
                    if not player.role.ego_self.inventory.has_item_in_inventory(Flags.slayer_unique_attempt):
                        raise UniqueAbilityError(unique_ability_used.format(player.user.mention, x_emoji))

                # Assassin's unique "assasinate" ability
                elif ability_type == ActionTypes.assassinate:
                    if not player.role.ego_self.inventory.has_item_in_inventory(Flags.assassin_unique_kill):
                        raise UniqueAbilityError(unique_ability_used.format(player.user.mention, x_emoji))

                # Courtier's unique "poison" ability
                elif ability_type == ActionTypes.poison:
                    if not player.role.ego_self.inventory.has_item_in_inventory(Flags.courtier_unique_poison):
                        raise UniqueAbilityError(unique_ability_used.format(player.user.mention, x_emoji))

                # Future roles that have a unique ability must go into elif blocks, or else the uncaught
                # ones will automatically trigger an assertion error.
                else:
                    assert 0, "Unique ability check went wrong."
                return func(self, player, targets)
            return inner
        return decorator

    @staticmethod
    def except_first_night(func):
        """Decorator for abilities that cannot be used on the first night"""
        def inner(self, player, targets):
            import globvars
            if globvars.master_state.game.is_night() and globvars.master_state.game.current_cycle == 1:
                raise FirstNightNotAllowed(except_first_night_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def changes_not_allowed(func):
        """Decorator for abilities that cannot modify targets after inputting them"""
        def inner(self, player, targets):
            import globvars
            if player.role.ego_self.has_finished_night_action(player):
                raise ChangesNotAllowed(changes_not_allowed.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def changes_not_allowed_dawn(func):
        """Decorator for abilities that cannot modify targets after inputting them"""
        def inner(self, player, targets):
            import globvars
            if player.role.ego_self.has_finished_dawn_action(player):
                raise ChangesNotAllowed(changes_not_allowed.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def requires_one_target(func):
        """Decorator for abilities that require one target"""
        def inner(self, player, targets):
            if len(targets) != 1:
                raise MustBeOneTarget(requires_one_target_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def requires_two_targets(func):
        """Decorator for abilities that require two targets"""
        def inner(self, player, targets):
            if len(targets) != 2:
                raise MustBeTwoTargets(requires_two_targets_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def requires_different_targets(func):
        """Decorator for abilities that do not allow repeat players in the targets"""
        def inner(self, player, targets):
            id_list = [target.user.id for target in targets]
            if len(id_list) != len(set(id_list)):
                raise NoRepeatTargets(requires_different_targets_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def requires_bmr_roles(func):
        """Decorator for abilities ony allow roles from the bmr edition"""
        def inner(self, player, targets):
            from .gamemodes.badmoonrising._utils import BMRRole
            role_list = [x.value for x in BMRRole]
            for character in targets:
                if character.name not in role_list:
                    raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def no_same_following_targets(func):
        """Decorator for abilities that do not allow the same target twice in a row"""
        def inner(self, player, targets):
            last_action = player.action_grid.retrieve_an_action(globvars.master_state.game._chrono.phase_id - 3) # Previous night, dawn or day, depending on current phase
            if last_action:
                for target in targets.target_list:
                    if target in last_action.target_player.target_list:
                        raise NoSameFollowingTargets(no_same_following_targets_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner


# ========== CONVERTERS ============================================================
# ----------------------------------------------------------------------------------

class PlayerNotFound(commands.BadArgument):
    """Error for when a player argument passed is not found"""
    pass


class RoleNotFound(commands.BadArgument):
    """Error for when a role argument passed is not found"""
    pass

class GamemodeNotFound(commands.BadArgument):
    """Error for when a gamemode argument passed is not found"""
    pass


class PlayerConverter(commands.Converter):
    """Parse the player name input arguments from commands"""

    async def convert(self, ctx, argument):
        """Convert to player objects"""
        player = BOTCUtils.get_player_from_string(argument)
        if player:
            return player
        raise PlayerNotFound(f"Player {argument} not found.")


class WhisperConverter(commands.Converter):
    """Parse the whisper content"""

    async def convert(self, ctx, argument):
        """Convert to a string while also checking for the maximum length"""
        if len(argument) > max(MAX_MESSAGE_LEN - 120, 0):
            raise WhisperTooLong("Whisper is too long")
        return argument


class RoleConverter(commands.Converter):
    """Convert a role name to a botc character class"""

    async def convert(self, ctx, argument):
        """
        Find a role name amongst the botc pack.
        Return the role class if it is found, else return None

        The game_packs variable is coded in the following way:

        {'botc': {'game_obj': <botc.Game.Game object at 0x1187bffd0>, 'gamemodes': {'trouble-brewing':
        [Baron Obj, Butler Obj, Chef Obj, Drunk Obj, Empath Obj, Fortune Teller Obj, Imp Obj,
        Investigator Obj, Librarian Obj, Mayor Obj, Monk Obj, Poisoner Obj, Ravenkeeper Obj,
        Recluse Obj, Saint Obj, Scarlet Woman Obj, Slayer Obj, Soldier Obj, Undertaker Obj,
        Virgin Obj, Washerwoman Obj]}}}
        """
        import globvars
        editions = globvars.master_state.game_packs["botc"]["gamemodes"]
        # First check for exact matches, otherwise looking for po might return poisoner ("po" in "POisoner")
        for edition in editions:
            role_pool = editions[edition]
            for role in role_pool:
                if argument.lower() == role.name.lower():
                    return role

        for edition in editions:
            role_pool = editions[edition]
            for role in role_pool:
                if argument.lower() in role.name.lower():
                    return role
        raise RoleNotFound(f"Role {argument} not found.")


class PlayerParser(commands.Converter):
    """Parse the player name input arguments from game commands"""

    async def convert(self, ctx, argument):
        """Convert to player objects, and split at "and" keyword"""
        raw_targets = argument.split(" and ")
        actual_targets = []
        for raw in raw_targets:
            player = BOTCUtils.get_player_from_string(raw)
            if player:
                actual_targets.append(player)
            else:
                msg = player_not_found.format(ctx.author.mention, x_emoji)
                await ctx.author.send(msg)
                raise commands.BadArgument(f"Player {raw} not found.")
        return Targets(actual_targets)


# ========== MISCELLANEOUS =========================================================
# ----------------------------------------------------------------------------------

class LorePicker:
    """Helps to pick lore strings from the json file"""

    SLAY_SUCCESS = "slay_success"
    SLAY_FAIL = "slay_fail"

    def pick(self, category):
        """Pick the lore string based on the weighted random function"""
        chosen = random.choices(
           lore[category]["outputs"],
           weights = lore[category]["weights"]
        )
        return chosen[0]
