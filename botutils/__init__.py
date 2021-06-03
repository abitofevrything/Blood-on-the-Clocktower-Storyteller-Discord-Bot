"""Bot utility functions"""

import json
import globvars
import sys

try:
    with open("botutils/bot_text.json") as bot_text_file:
        bot_text = json.load(bot_text_file)
except FileNotFoundError:
    globvars.logging.error("Bot text file not found. Does the file botutils/bot_text.json exist?")
    sys.exit(1)

from .adds import (add_admin_role, add_alive_role, add_dead_role, lock_lobby,
                   remove_admin_role, remove_alive_role,
                   remove_all_alive_dead_roles_after_game,
                   remove_all_alive_roles_pregame, remove_dead_role,
                   unlock_lobby)
from .BotState import BotState
from .checks import (check_if_admin, check_if_dm, check_if_in_pregame,
                     check_if_is_pregame_player, check_if_lobby,
                     check_if_lobby_or_dm_or_admin,
                     check_if_lobby_or_spec_or_dm_or_admin,
                     check_if_not_ignored, check_if_not_in_empty,
                     check_if_not_in_game, check_if_spec, return_false,
                     return_true)
from .emoji import BotEmoji
from .GameChooser import GameChooser
from .helpers import (AmbiguousUserError, find_role_in_all, get_emoji,
                      get_member_from_string, get_member_obj, get_user_obj,
                      make_alive_ping, make_code_block, make_dead_ping,
                      make_ping, make_role_ping, make_time_string,
                      restart_bot, strip_ping, update_state_machine)
from .MasterState import MasterState, StateMachine
from .Pregame import Pregame
from .sends import (Level, create_code_block, log, send_lobby, send_replay,
                    send_pregame_stats, send_long_message)
from .tasks import (after_lobby_timeout, cycling_bot_status,
                    lobby_timeout, rate_limit_commands, start_votes_timer,
                    votestop_votes_timer)
