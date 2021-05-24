"""Blood on the Clocktower (BoTC) game specific mechanics"""

import json
import sys

import globvars

try:
    with open("botc/game_text.json") as game_text_file:
        game_text = json.load(game_text_file)
except FileNotFoundError:
    globvars.logging.error("Game text file not found. Does the file botc/game_text.json exist?")
    sys.exit(1)

try:
    with open("botc/emojis.json") as emojis_file:
        emojis = json.load(emojis_file)
except FileNotFoundError:
    globvars.logging.error("Game text file not found. Does the file botc/game_text.json exist?")
    sys.exit(1)

from .abilities import Action, ActionGrid, ActionTypes
from .BOTCUtils import (AbilityForbidden, AliveOnlyCommand, BOTCUtils,
                        DeadOnlyCommand, GameLogic, IsAPlayer, LorePicker,
                        NotAPlayer, NotDawn, NotDay, NotDMChannel,
                        NotLobbyChannel, NotNight, PlayerConverter,
                        PlayerNotFound, PlayerParser, RoleCannotUseCommand,
                        RoleConverter, RoleNotFound, WhisperConverter,
                        WhisperTooLong, get_number_image)
from .Category import Category
from .Character import Character
from .checks import (can_use_kill, can_use_learn, can_use_poison,
                     can_use_protect, can_use_read, can_use_serve,
                     can_use_slay, check_if_can_kill, check_if_can_learn,
                     check_if_can_poison, check_if_can_protect,
                     check_if_can_read, check_if_can_serve, check_if_can_slay,
                     check_if_dm, check_if_is_dawn, check_if_is_day,
                     check_if_is_night, check_if_is_player, check_if_lobby,
                     check_if_not_player, check_if_player_apparently_alive,
                     check_if_player_apparently_dead,
                     check_if_player_really_alive, check_if_player_really_dead)
from .ChoppingBlock import ChoppingBlock
from .chrono import GameChrono
from .Demon import Demon
from .errors import (AlreadyDead, GameError, IncorrectNumberOfArguments,
                     TooFewPlayers, TooManyPlayers)
from .flag_inventory import Flags, Inventory
from .Grimoire import Grimoire
from .Minion import Minion
from .Outsider import Outsider
from .Phase import Phase
from .Player import Player
from .PlayerState import PlayerState
from .RecurringAction import NonRecurringAction, RecurringAction
from .RoleGuide import RoleGuide
from .status import (ButlerService, Drunkenness, Poison, RavenkeeperActivated,
                     RedHerring, SafetyFromDemon, StatusList, Storyteller)
from .Team import Team
from .Townsfolk import Townsfolk

from .setups import load_pack  # isort: split

from .Townsquare import Townsquare
