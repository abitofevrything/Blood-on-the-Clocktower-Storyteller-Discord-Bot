"""Contains some BoTC game related utility functions"""

import asyncio
import random
import re

import toml
from discord.ext import commands, tasks
from unidecode import unidecode

import globvars
from botc import game_text
from botutils import BotEmoji
from config import MAX_MESSAGE_LENGTH

from .Category import Category
from .Team import Team

player_not_found = game_text["cmd_warnings"]["player_not_found"]
no_self_targetting_str = game_text["cmd_warnings"]["no_self_targetting_str"]
except_first_night_str = game_text["cmd_warnings"]["except_first_night_str"]
requires_one_target_str = game_text["cmd_warnings"]["requires_one_target_str"]
requires_two_targets_str = game_text["cmd_warnings"]["requires_two_targets_str"]
requires_different_targets_str = game_text["cmd_warnings"]["requires_different_targets_str"]
changes_not_allowed = game_text["cmd_warnings"]["changes_not_allowed"]
unique_ability_used = game_text["cmd_warnings"]["unique_ability_used"]
not_under_status = game_text["cmd_warnings"]["not_under_status"]
lore = game_text["lore"]
bmr_roles_only_str = game_text["cmd_warnings"]["bmr_roles_only"]
no_same_following_targets_str = game_text["cmd_warnings"]["no_same_following_targets"]
statement_unrecognized = game_text["cmd_warnings"]["statement_unrecognized"]
no_alive_targets_str = game_text["cmd_warnings"]["no_alive_targets"]
no_dead_targets_str = game_text["cmd_warnings"]["no_dead_targets"]
no_targets_allowed_str = game_text["cmd_warnings"]["no_targets_allowed_str"]
requires_one_or_three_targets_str = game_text["cmd_warnings"]["requires_one_or_three_targets_str"]

x_emoji = BotEmoji.x_emoji


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
    numbers = game_text["numbers"]
    possibilities = numbers[str(nb)]
    chosen = random.choice(possibilities)
    return chosen

def validate_statement(player, statement: str):
    statement = statement.lower().strip().rstrip('.')

    # Substitute contractions with expanded versions
    statement = statement.replace(" isn't ", " is not ")
    statement = statement.replace(" isnt ", " is not ")
    statement = statement.replace("'s ", " is ")
    statement = statement.replace(" hasn't ", " has not ")
    statement = statement.replace(" hasnt ", " has not ")
    statement = statement.replace(" wasn't ", " was not ")
    statement = statement.replace(" wasnt ", " was not ")

    while '  ' in statement:
        statement = statement.replace('  ', ' ')

    import botutils
    from botc import Character, Player
    from botc.gamemodes.badmoonrising._utils import BadMoonRising, BMRRole

    def player_is_role(args):
        target_player = BOTCUtils.get_player_from_string(args[0])
        role = botutils.find_role_in_all(args[1])

        if role is None:
            raise RoleNotFound(f"Role {args[1]} not found.")
        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        if target_player is None:
            raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        return target_player.role.social_self.name == role.name

    def player_was_role(args):
        role_matches = player_is_role(args)
        
        target_player = BOTCUtils.get_player_from_string(args[0])
        
        if target_player is None:
            raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        return target_player.is_apparently_dead() and role_matches

    def player_is_alignement(args):
        target_player = BOTCUtils.get_player_from_string(args[0])
        guess_good = args[1] == "good"

        if target_player is None:
            raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        return guess_good == target_player.role.social_self.is_good()

    def player_is_category(args):
        target_player = BOTCUtils.get_player_from_string(args[0])

        if args[1] == "town" or args[1] == "townsfolk":
            guess_category = Category.townsfolk
        elif args[1] == "outsider":
            guess_category = Category.outsider
        elif args[1] == "minion":
            guess_category = Category.minion
        else:
            guess_category = Category.demon

        if target_player is None:
            raise PlayerNotFound(player_not_found.format(player.user.mention, x_emoji))

        return target_player.role.social_self.category == guess_category
    
    def role_is_ingame(args):
        role = botutils.find_role_in_all(args[0])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        elif role is None:
            raise RoleNotFound(f"Role {args[0]} not found.")

        roles = [target_player.role.social_self.name for target_player in globvars.master_state.game.sitting_order]

        return role.name in roles

    def n_category_in_game(args):
        num = int(args[0])

        actual_num_demons = 0
        actual_num_minions = 0
        actual_num_town = 0
        actual_num_outsider = 0

        for target_player in globvars.master_state.game.sitting_order:
            pcategory = target_player.role.social_self.category
            if pcategory == Category.townsfolk:
                actual_num_town = actual_num_town + 1
            elif pcategory == Category.outsider:
                actual_num_outsider = actual_num_outsider + 1
            elif pcategory == Category.minion:
                actual_num_minions = actual_num_minions + 1
            else:
                actual_num_demons = actual_num_demons + 1

        if args[1] == "town" or args[1] == "townsfolk":
            return num == actual_num_town
        elif args[1] == "outsider":
            return num == actual_num_outsider
        elif args[1] == "minion":
            return num == actual_num_minions
        else:
            return num == actual_num_demons
    
    def less_than_n_category(args):
        num = int(args[0])

        actual_num_demons = 0
        actual_num_minions = 0
        actual_num_town = 0
        actual_num_outsider = 0

        for target_player in globvars.master_state.game.sitting_order:
            pcategory = target_player.role.social_self.category
            if pcategory == Category.townsfolk:
                actual_num_town = actual_num_town + 1
            elif pcategory == Category.outsider:
                actual_num_outsider = actual_num_outsider + 1
            elif pcategory == Category.minion:
                actual_num_minions = actual_num_minions + 1
            else:
                actual_num_demons = actual_num_demons + 1

        if args[1] == "town" or args[1] == "townsfolk":
            return num > actual_num_town
        elif args[1] == "outsider":
            return num > actual_num_outsider
        elif args[1] == "minion":
            return num > actual_num_minions
        else:
            return num > actual_num_demons

    def more_than_n_category(args):
        num = int(args[0])

        actual_num_demons = 0
        actual_num_minions = 0
        actual_num_town = 0
        actual_num_outsider = 0

        for target_player in globvars.master_state.game.sitting_order:
            pcategory = target_player.role.social_self.category
            if pcategory == Category.townsfolk:
                actual_num_town = actual_num_town + 1
            elif pcategory == Category.outsider:
                actual_num_outsider = actual_num_outsider + 1
            elif pcategory == Category.minion:
                actual_num_minions = actual_num_minions + 1
            else:
                actual_num_demons = actual_num_demons + 1

        if args[1] == "town" or args[1] == "townsfolk":
            return num < actual_num_town
        elif args[1] == "outsider":
            return num < actual_num_outsider
        elif args[1] == "minion":
            return num < actual_num_minions
        else:
            return num < actual_num_demons

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
        day_phase_id = game._chrono.phase_id - (game._chrono.phase_id % 3)
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
        day_phase_id = game._chrono.phase_id - (game._chrono.phase_id % 3)
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
            if not isinstance(arg2, BadMoonRising):
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
            if not isinstance(arg2, BadMoonRising):
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

        game = globvars.master_state.game
        last_night_phase = game._chrono.phase_id - (game._chrono.phase_id % 3) - 2

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

        phase = 0
        while phase <= globvars.master_state.game._chrono.phase_id:
            if isinstance(arg, Player):
                action = arg.action_grid.retrieve_an_action(phase)
                if action is not None:
                    return True
            else:
                for player in globvars.master_state.game.sitting_order:
                    if player.role.social_self.name == arg.name:
                        action = player.action_grid.retrieve_an_action(phase)
                        if action is not None:
                            return True
        
            phase = phase + 1

        return False

    def name_contains(args):
        role = botutils.find_role_in_all(args[0])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        elif role is None:
            if args[0] == 'demon':
                players = [p for p in globvars.master_state.game._player_obj_list if p.role.social_self.category == Category.demon]
            else:
                raise RoleNotFound(f"Role {args[0]} not found.")

        if args[0] != 'demon':
            players = BOTCUtils.get_players_from_role_name(role._role_enum)

        for target_player in players:
            if args[1] in target_player.user.name.lower():
                return True
            if target_player.user.nick is not None:
                if args[1] in target_player.user.nick.lower():
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
                if player.is_apparently_alive():
                    return True
            return False
        else:
            for player in players:
                if player.is_apparently_dead():
                    return True
            return False

    def n_alive_players(args):
        num = int(args[0])
        return num == len([p for p in globvars.master_state.game.sitting_order if p.is_apparently_alive()])

    def category_contains_role(args):
        role = botutils.find_role_in_all(args[1])

        if not isinstance(role, BadMoonRising):
            raise BMRRolesOnly(bmr_roles_only_str.format(player.user.mention, x_emoji))
        elif role is None:
            raise RoleNotFound(f"Role {args[1]} not found.")

        if args[0] == 'demon':
            roles = [p.role.social_self.name for p in BOTCUtils.get_players_from_category(Category.demon)]
        elif args[0] == 'minion':
            roles = [p.role.social_self.name for p in BOTCUtils.get_players_from_category(Category.minion)]
        elif args[0] == 'outsider':
            roles = [p.role.social_self.name for p in BOTCUtils.get_players_from_category(Category.outsider)]
        else:
            roles = [p.role.social_self.name for p in BOTCUtils.get_players_from_category(Category.townsfolk)]

        return role.name in roles

    def n_cat_or_alin_in_players(args):
        # determine if alignment is 1st or second arg
        if args[0] in ('evil', 'good', 'demon', 'minion', 'outsider', 'town', 'os', 'town'):
            players = args[1]
            cat_or_alin = args[0]
        else:
            players = args[0]
            cat_or_alin = args[1]

        # splitters: ' or ', ', ', ',', ' ', ' and '
        split = re.split(r" and | or |, |,| ", players)
        for i, player in enumerate(split):
            print(f"Get player '{player}': {BOTCUtils.get_player_from_string(player)}")
            temp = BOTCUtils.get_player_from_string(player)
            if temp is None:
                raise PlayerNotFound()
            split[i] = temp

        if cat_or_alin in ('demon'):
            return len([p for p in split if p.role.social_self.category == Category.demon]) != 0
        elif cat_or_alin in ('minion'):
            return len([p for p in split if p.role.social_self.category == Category.minion]) != 0
        elif cat_or_alin in ('os', 'outsider'):
            return len([p for p in split if p.role.social_self.category == Category.outsider]) != 0
        elif cat_or_alin in ('town', 'townsfolk'):
            return len([p for p in split if p.role.social_self.category == Category.townsfolk]) != 0
        elif cat_or_alin in ('good'):
            return len([p for p in split if p.role.social_self.team == Team.good]) != 0
        elif cat_or_alin in ('evil'):
            return len([p for p in split if p.role.social_self.team == Team.evil]) != 0
        else:
            raise InvalidGossipStatement(statement_unrecognized.format(player.user.mention, x_emoji))
                

    statement_checks = [
        # (match_checker, splitter, validator)

        # <player> is (the) <role>
        # <player> is <role>
        (r".+ is (the |)(" + "|".join(role.value.lower() for role in BMRRole) + r")", r".+(?= is)|(?<= is )(?!the ).+(?=$)|()(?<= is the ).+(?=$)", player_is_role),

        # <player> is not (the) <role>
        (r".+(is not|isnt|isn't) (the |).+", r"^.+(?= is)|((?<=the )|(?<=a )|((?<=is not )|(?<=isnt )|(?<=isn't ))(?!the|a)).+", lambda args: not player_is_role(args)),

        # <player> was (the) <role>
        (r".+ was .+", r".+(?= was)|(?<=was ).+", player_was_role),

        # <player> is <alignement>
        (r".+ is (good|evil)", r".+(?= is )|(?<= is ).+", player_is_alignement),

        # <player> is <category>
        # <player> is an <category>
        # <player> is a <category>
        (r".+ is (a |an |the |)(town|townsfolk|outsider|minion|demon)", r".+(?= is )|(?<= is )(?!(a |an |the )).+(?=$)|(?<= is a )(?!an |the ).+(?=$)|(?<= is an )(?!a ).+(?=$)|(?<= is the )(?!a |an ).+(?=$)", player_is_category),

        # <player> is not <category>
        # <player> is not a <category>
        # <player> is not an <category>
        (r".+ is not (a |an |the |)(town|townsfolk|outsider|minion|demon)", r".+(?= is )|(?<= is not )(?!(a |an |the )).+(?=$)|(?<= is not a )(?!an |the ).+(?=$)|(?<= is not an )(?!a ).+(?=$)|(?<= is not the )(?!a |an ).+(?=$)", lambda args: not player_is_category(args)),

        # (the) <role> is in game
        # (the) <role> is ingame
        # (the) <role> is in-game
        # (the) <role> is in play
        (r"(the |a |).+ is (in game|in-game|ingame|in play|in the game|in this game)", r"^(?!the ).+(?= is (in game|in-game|ingame|in play|in the game|in this game))|(?<=the ).+(?= is (in game|in-game|ingame|in play|in the game|in this game))", role_is_ingame),

        # there is a <role> is in game
        # there is a <role> is ingame
        # there is a <role> is in-game
        # there is a <role> is in play
        (r"there is a .+ (in game|in play|in-game|ingame)", r"(?<=there is a ).+(?=(in game|in play|in-game|ingame))", role_is_ingame),

        # (the) <role> is not in game
        # (the) <role> is not ingame
        # (the) <role> is not in-game
        # (the) <role> is not in play
        (r"(the |a |).+ is not (in game|in-game|ingame|in play)", r"^(?!the ).+(?= is not (in game|in-game|ingame|in play))|(?<=the ).+(?= is not (in game|in-game|ingame|in play))", lambda args: not role_is_ingame(args)),

        # there (are|is) <n> outsider(s) in play
        # there (are|is) <n> (town|townsfolk) in play
        # there (are|is) <n> minion(s) in play
        # there (are|is) <n> demon(s) in play
        (r"there (is|are) [0-9]+ (town|townsfolk|outsider|minion|demon)(s|) (in game|in-game|ingame|in play)", r"[0-9]+(?= (demon|town|townsfolk|minion|outsider))|(?<=[0-9] ).+(?<!s)(?=(s | )(in game|in-game|ingame|in play))", n_category_in_game),

        # there (are|is) less than <n> (town|townsfolk) in play
        # there (are|is) less than <n> outsider(s) in play
        # there (are|is) less than <n> minion(s) in play
        # there (are|is) less than <n> demon(s) in play
        (r"there (is|are) (less|fewer) than [0-9]+ (town|townsfolk|outsider|minion|demon)(s|) (in game|in-game|ingame|in play)", r"[0-9]+(?= (demon|town|townsfolk|minion|outsider))|(?<=[0-9] ).+(?<!s)(?=(s | )(in game|in-game|ingame|in play))", less_than_n_category),

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
        (r"(the |).+(has whispered to|whispered to) (the |).+ today", r"^(?!the ).+(?=( whispered to| has whispered to))|(?<=the ).+(?=( whispered to| has whispered to))|(?<=to the ).+(?= today)|(?<=to )(?!the ).+(?= today)", whispered_to_today),

        # (the) <role/player> has whispered to (the) <role/player>
        # (the) <role/player> whispered to (the) <role/player>
        (r"(the |).+(has whispered to|whispered to) (the |).+", r"^(?!the ).+(?<! has)(?= whispered to)|(?<=the ).+(?<! has)(?= whispered to)|^(?!the ).+(?= has whispered to)|(?<=the ).+(?= has whispered to)|(?<= whispered to )(?!the ).+|(?<= whispered to the ).+", whispered_to),

        # (the) <role> has used their ability tonight
        # (the) <role> used their ability tonight
        # <player> used their ability tonight
        # <player> has used their ability tonight
        (r"(the |).+ (has |)used (their|his|her) ability (tonight|last night)", r"^(?!the ).+(?<! has)(?= (has |)used (their|his|her) ability (tonight|last night))|(?<=the ).+(?<! has)(?= (has |)used (their|his|her) ability (tonight|last night))", ability_used_tonight),

        # (the) <role> has used their ability
        # (the) <role> used their ability
        # <player> has used their ability
        # <player> used their ability
        (r"(the |).+ (has |)used (their|his|her) ability(?! tonight)", r"^(?!the ).+(?<! has)(?= (has |)used (their|his|her) ability)|(?<=the ).+(?<! has)(?= (has |)used (their|his|her) ability)", ability_used),

        # (the) <role>'s name contains <c>
        # (the) <role>'s nickname contains <c>
        # "'s" is replaced by " is" in the contractions, so the statement will actually look like "(the) <role> is name contains <c>"
        (r"(the |).+ is (name|nickname) contains (the character |the char |).", r"^(?!the ).+(?= is (name|nickname) contains)|(?<=the ).+(?= is (name|nickname) contains)|.(?=$)", name_contains),

        # (the) <role> is (dead|alive)
        (r"(the |).+ is (alive|dead)", r"^(?!the ).+(?= is (alive|dead))|(?<=the ).+(?= is (alive|dead))|(?<= is )(alive|dead)", role_status),

        # there are <n> players alive
        (r"there (are|is) [0-9]+ player(s|) alive", r"[0-9]+(?= player(s|) alive)", n_alive_players),
        # there are <n> alive player
        (r"there (is|are) [0-9]+ alive player(s|)", r"[0-9]+(?= alive player(s|))", n_alive_players),

        # (the|a|an) <category> is (the|a|an) <role>
        (r"((the|a|an) |)(demon|minion|outsider|townsfolk|town) is ((the|an|a|) |).+", r"(?!the |a |an )((?<= )|(?<=^)).+(?= is)|((?<=is the )|(?<=is a )|(?<= is an )|(?<=is ))(?!(the|a|an)).+(?=$)", category_contains_role),

        # (the|a|an) <category> is not (the|a|an) <role>
        (r"((the|a|an) |)(demon|minion|outsider|townsfolk|town) is not ((the|an|a|) |).+", r"(?!the |a |an )((?<= )|(?<=^)).+(?= is not)|((?<=is not the )|(?<=is not a )|(?<= is not an )|(?<=is not ))(?!(the|a|an)).+(?=$)", lambda args: not category_contains_role(args)),

        # one of <players> is <category/alignment>
        # one of <players> is <category/alignment>
        # there is one <category/alignment> in <players>
        (r"one of .+ is .+|there is (one|an) .+ in .+", r"(?<=one of ).+(?= is )|(?<= is )(?<!there is ).+|(?<= in ).+|(?<=there is one ).+(?= in )|(?<=there is an ).+(?= in )", n_cat_or_alin_in_players)

    ]

    err = None

    for check in statement_checks:
        match_checker = re.compile(check[0], re.IGNORECASE | re.MULTILINE)
        if bool(match_checker.fullmatch(statement)):
            try:
                splitter = re.finditer(check[1], statement, re.IGNORECASE | re.MULTILINE)
                groups = [match.group() for match in splitter]
                return check[2](groups)
            except Exception as e:
                if err is None:
                    err = e

    if err is not None:
        raise err
    else:
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
        string = unidecode(string.lower())
        usernames = []
        discriminators = []
        nicknames = []
        ids_contains = []
        usernames_contains = []
        nicknames_contains = []
        for player in game.sitting_order:
            if string == str(player.user.id) or string.strip('<@!>') == str(player.user.id):
                return player
            if unidecode(str(player.user).lower()).startswith(string):
                usernames.append(player)
            if string.strip('#') == player.user.discriminator:
                discriminators.append(player)
            if unidecode(player.user.display_name.lower()).startswith(string):
                nicknames.append(player)
            if string in unidecode(player.user.name.lower()):
                usernames_contains.append(player)
            if string in unidecode(player.user.display_name.lower()):
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

    @staticmethod
    def get_players_from_category(category):
        return [p for p in globvars.master_state.game.player_obj_list if p.role.social_self.category == category]


# ========== CHECK ERRORS ==========================================================
# ----------------------------------------------------------------------------------

class WhisperTooLong(commands.CommandInvokeError):
    """Raised when a command user tries to whisper a message that is too long"""
    pass

class NotAPlayer(commands.CheckFailure):
    """Raised when a command user is not a registered player"""
    pass

class IsAPlayer(commands.CheckFailure):
    """Raised when a command user is a registered player"""
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

class MustBeOneOrThreeTargets(AbilityForbidden):
    """Must be exactly one or three targets"""
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

class NoAliveTargets(AbilityForbidden):
    """Error for when an ability that cannot target dead roles does so"""
    pass

class NoDeadTargets(AbilityForbidden):
    """Error for when an ability that cannot target alive roles does so"""
    pass

class NoTargetsAllowed(AbilityForbidden):
    """Error for when an ability that cannot specify targets does so"""
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
                from botc import ActionTypes, Flags

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

                # Professor's unique "examine" ability
                elif ability_type == ActionTypes.examine:
                    if not player.role.ego_self.inventory.has_item_in_inventory(Flags.professor_unique_resurrect):
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
    def requires_one_or_three_targets(func):
        """Decorator for abilities that require one target"""
        def inner(self, player, targets):
            if len(targets) != 1 and len(targets) != 3:
                raise MustBeOneOrThreeTargets(requires_one_or_three_targets_str.format(player.user.mention, x_emoji))
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

    @staticmethod
    def requires_dead_targets(func):
        """Decorator for abilities that do not allow alive targets"""
        def inner(self, player, targets):
            for target in targets.target_list:
                if target.is_apparently_alive():
                    raise NoAliveTargets(no_alive_targets_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def requires_alive_targets(func):
        """Decorator for abilities that do not allow dead targets"""
        def inner(self, player, targets):
            for target in targets.target_list:
                if target.is_apparently_dead():
                    raise NoDeadTargets(no_dead_targets_str.format(player.user.mention, x_emoji))
            return func(self, player, targets)
        return inner

    @staticmethod
    def no_targets_allowed(func):
        """Decorator for abilities that do not allow targets"""
        def inner(self, player, targets):
            for target in targets.target_list:
                if target.is_apparently_dead():
                    raise NoTargetsAllowed(no_targets_allowed_str.format(player.user.mention, x_emoji))
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
        if len(argument) > max(MAX_MESSAGE_LENGTH - 120, 0):
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
        [Baron Class, Butler Class, Chef Class, Drunk Class, Empath Class, Fortune Teller Class, Imp Class,
        Investigator Class, Librarian Class, Mayor Class, Monk Class, Poisoner Class, Ravenkeeper Class,
        Recluse Class, Saint Class, Scarlet Woman Class, Slayer Class, Soldier Class, Undertaker Class,
        Virgin Class, Washerwoman Class]}}}
        """
        import globvars
        editions = globvars.master_state.game_packs["botc"]["gamemodes"]
        # First check for exact matches, otherwise looking for po might return poisoner ("po" in "POisoner")
        for edition in editions:
            role_pool = editions[edition]
            for role in role_pool:
                instance = role()
                if argument.lower() == instance.name.lower():
                    return instance

        for edition in editions:
            role_pool = editions[edition]
            for role in role_pool:
                instance = role()
                if argument.lower() in instance.name.lower():
                    return instance
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
