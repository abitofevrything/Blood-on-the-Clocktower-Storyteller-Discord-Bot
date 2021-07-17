"""Global variables, for access by all modules"""

import logging
from collections import defaultdict

from botutils import MasterState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S'
)


def init_master_state():
    """Initialize master state. Must only be used by main.py"""
    global master_state
    master_state = MasterState()


def init_client():
    """Initialize client. Must only be used by main.py"""
    global client
    client = None

"""Mapping of user id to number of commands used in the last TOKEN_RESET seconds
Used to ratelimit command usage"""
ratelimit_dict = dict()

"""List of user ids who have started to vote the game
Used to keep track of who has and who has not voted to
start the game during pregame"""
start_votes = []

"""List of user ids who have started to stop the game
Used to keep track of who has and who has not voted to
stop the game during a game"""
votestop_votes = []

"""Mapping of user id to mapping of user id to UNIX timestamp (int)
Keeps track of the last whisper timestamp from a player to
another, for whisper cooldown purposes"""
last_whisper = defaultdict(lambda: defaultdict(int))

"""Mapping of user id to the last UNIX timestamp they were
pinged at by !notify
Used to determine per-user notify cooldowns"""
notify_user_ping_cooldown_map = {}
"""Mapping of playercount to the last UNIX timestamp !notify
was used at that playercount
Used to determine per-playercount notify cooldowns"""
notify_playercount_cooldown_map = {}
