"""Contains the bot config & preferences"""

import toml
import globvars

import sys

# Config
try:
    with open("config.toml") as config_file:
        config = toml.load(config_file)

        # bot
        BOT = config["bot"]
        TOKEN = BOT["token"]
        PREFIX = BOT["prefix"]
        MAX_MESSAGE_LENGTH = BOT["max_message_len"]

        # ids
        IDS = config["ids"]
        OWNER_ID = IDS["owner_id"]
        ADMIN_IDS = IDS["admin_ids"]
        SERVER_ID = IDS["server_id"]
        LOBBY_CHANNEL_ID = IDS["lobby_channel_id"]
        SPEC_CHANNEL_ID = IDS["spec_channel_id"]
        LOGGING_CHANNEL_ID = IDS["logging_channel_id"]
        REPLAY_CHANNEL_ID = IDS["replay_channel_id"]
        ALIVE_ROLE_ID = IDS["alive_role_id"]
        DEAD_ROLE_ID = IDS["dead_role_id"]
        ADMIN_ROLE_ID = IDS["admins_role_id"]

        # lock
        LOCK_CHANNEL_IDS = config["lock"].get("channel_ids", [])
        SPECIAL_LOCK_CHANNEL_IDS = config.get("special_channel_ids", [])

        # playtesters
        PLAYTESTERS = config["commands"]["playtest"].get("playtesters", [])

        # top
        TOP_LIMIT = config["commands"]["top"].get("limit", 15)

        # top.winrate
        TOP_WINRATE_MIN_GAMES = config["commands"]["top"]["winrate"].get("min_games", 15)

        # debug
        DEBUG = config["debug"]
        DISABLE_DMS = DEBUG.get("disable_dms", False)
        DISABLE_PINGS = DEBUG.get("disable_pings", False)
        FORCE_VOTES = DEBUG.get("force_votes", False)
        NO_INVALIDATE = DEBUG.get("no_invalidate", False)

except FileNotFoundError:
    globvars.logging.error("Config file not found. Do you have a file named config.toml in the root directory?")
    sys.exit(1)
except KeyError as e:
    globvars.logging.error(f"Invalid config file: missing key {e.args[0]}")
    sys.exit(1)

# Preferences
try:
    with open("preferences.toml") as preferences_file:
        preferences = toml.load(preferences_file)

        # colors
        COLORS = preferences["colors"]
        NORMAL_CARD_COLOR = COLORS.get("card_normal", 0xffffff)
        NIGHT_CARD_COLOR = COLORS.get("card_night", 0x226b6c)
        DAWN_CARD_COLOR = COLORS.get("card_dawn", 0xa88497)
        DAY_CARD_COLOR = COLORS.get("card_day", 0xd6bb50)
        NORMAL_IN_GAME_CARD_COLOR = COLORS.get("in_game_normal", 0xff8647)
        TOWNSFOLK_CARD_COLOR = COLORS.get("townsfolk_color", 0x0776f2)
        OUTSIDER_CARD_COLOR = COLORS.get("outsider_color", 0x0776f2)
        MINION_CARD_COLOR = COLORS.get("minion_color", 0xe10600)
        DEMON_CARD_COLOR = COLORS.get("demon_color", 0xe10600)
        LYNCH_CARD_COLOR = COLORS.get("card_lynch", 0x669d34)
        NO_LYNCH_CARD_COLOR = COLORS.get("card_no_lynch", 0xb51a00)

        # botc
        BOTC = preferences["botc"]
        BASE_NIGHT = BOTC.get("base_night", 30)
        NIGHT_MULTIPLER = BOTC.get("night_multipler", 0)
        BASE_DAWN = BOTC.get("base_dawn", 15)
        DAWN_MULTIPLIER = BOTC.get("dawn_multiplier", 0)
        VOTE_TIMEOUT = BOTC.get("vote_timeout", 8)
        DELETE_VOTE_AFTER = BOTC.get("delete_vote_after", 45)
        DEBATE_TIME = BOTC.get("debate_time", 45)
        INCREMENT = BOTC.get("increment", 15)
        WHISPER_COOLDOWN = BOTC.get("whisper_cooldown", 15)
        TOWNSQUARE_COOLDOWN = BOTC.get("townsquare_cooldown", 60)
        GRIMOIRE_SHOW_TIME = BOTC.get("grimoire_show_time", 40)
        WHISPER_SHOW_TIME = BOTC.get("whisper_show_time", 30)
        CLAIM_SHOW_TIME = BOTC.get("claim_show_time", 30)

        # duration
        DURATION = preferences["duration"]
        START_CLEAR = DURATION.get("start_clear", 60)
        LOBBY_TIMEOUT = DURATION.get("lobby_timeout", 1200)
        TOKENS_GIVEN = DURATION.get("tokens_given", 5)
        TOKEN_RESET = DURATION.get("token_reset", 10)
        IGNORE_THRESHOLD = DURATION.get("ignore_threshold", 7)
        STATUS_CYCLE = DURATION.get("status_cycle", 20)
        BACKUP_INTERVAL_MIN = DURATION.get("backup_interval_min", 5)
        NOTIFY_COOLDOWN = DURATION.get("notify_cooldown", 3600)
        VOTESTOP_CLEAR = DURATION.get("votestop_clear", 30)
        STREAK_COOLDOWN = DURATION.get("streak_cooldown", 60)

        # location
        TIMEZONE = preferences["location"].get("timezone", "Canada/Eastern")

except FileNotFoundError:
    globvars.logging.error("Preferences file not found. Do you have a file named preferences.toml in the root directory?")
    sys.exit(1)
except KeyError as e:
    globvars.logging.error(f"Invalid preferences file: missing key {e.args[0]}")
    sys.exit(1)