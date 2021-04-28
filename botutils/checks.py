"""Contains checks"""

import sqlite3
import toml

import botutils
import globvars

with open("config.toml") as fd:
    config = toml.load(fd)

    LOBBY_CHANNEL_ID = config["ids"]["lobby_channel_id"]
    SPEC_CHANNEL_ID = config["ids"]["spec_channel_id"]
    OWNER_ID = config["ids"]["owner_id"]
    ADMIN_IDS = config["ids"]["admin_ids"]


def __is_lobby(ctx):
    """Check the channel of the context, return True if it is in the lobby channel"""
    return ctx.channel.id == int(LOBBY_CHANNEL_ID)


def __is_specchat(ctx):
    """Check the channel of the context, return True if it is in the spec chat"""
    return ctx.channel.id == int(SPEC_CHANNEL_ID)


def __is_admin(ctx):
    """Check the author of the context, return True if they have admin perms or higher"""
    return ctx.author.id in ADMIN_IDS or ctx.author.id == int(OWNER_ID)


def check_if_in_pregame(ctx):
    """Check if the global state of the bot is in pregame"""
    return globvars.master_state.session == botutils.BotState.pregame


def check_if_not_in_game(ctx):
    """Check if the global state of the bot is not in game"""
    return globvars.master_state.session != botutils.BotState.game


def check_if_not_in_empty(ctx):
    """Check if the global state of the bot is not in empty state"""
    return globvars.master_state.session != botutils.BotState.empty


def check_if_lobby_or_dm_or_admin(ctx):
    """Check the channel of the context, return True if it is sent in either
    lobby or in a private channel.
    Admins can bypass.
    """
    return ctx.guild is None or __is_lobby(ctx) or __is_admin(ctx)


def check_if_lobby_or_spec_or_dm_or_admin(ctx):
    """Check the channel of the context, return True if it is sent in either
    lobby, in spec chat, or in a private channel.
    Admins can bypass.
    """
    return ctx.guild is None or __is_lobby(ctx) or __is_admin(ctx) or __is_specchat(ctx)


def check_if_is_pregame_player(ctx):
    """Check the author of the context, return True if they are registered in the pregame"""
    return ctx.author.id in globvars.master_state.pregame


def check_if_dm(ctx):
    """Check the channel of the context, return True if it is sent in a private channel.
    Admins cannot bypass.
    """
    return ctx.guild is None


def check_if_admin(ctx):
    """Check the author of the context, return True if they have admin perms or higher"""
    return __is_admin(ctx)


def check_if_lobby(ctx):
    """Check the channel of the context, return True if it is sent in the lobby channel"""
    return __is_lobby(ctx)


def check_if_spec(ctx):
    """Check the channel of the context, return True if it is sent in the spec chat"""
    return __is_specchat(ctx)


def check_if_not_ignored(ctx):
    """Check the author of the context, return True if they are not ignored"""
    if __is_admin(ctx):
        return True

    with sqlite3.connect("data.sqlite3") as conn:
        c = conn.cursor()

        c.execute("SELECT EXISTS(SELECT 1 FROM ignore WHERE user_id = :user_id)", {"user_id": ctx.author.id})
        row = c.fetchone()
        ignored = row[0]

        return not ignored


def return_false(ctx):
    """Always return false. Use for debugging/testing"""
    return False


def return_true(ctx):
    """Always return true. Use for debugging/testing"""
    return True
