"""Contains other helper functions"""

import datetime
import json
import os
import re
import sys

import emoji
import toml

import botutils
import globvars
from botutils import bot_text
from config import ALIVE_ROLE_ID, DEAD_ROLE_ID, SERVER_ID

error_str = bot_text["system"]["error"]

class AmbiguousUserError(Exception):
    pass


def make_ping(userid):
    """Turn a user ID into a ping"""
    return f"<@{userid}>"


def make_role_ping(roleid):
    """Turn a role ID into a ping"""
    return f"<@&{roleid}>"


def make_alive_ping():
    """Ping the @alive role."""
    global ALIVE_ROLE_ID
    return f"<@&{ALIVE_ROLE_ID}>"


def make_dead_ping():
    """Ping the @dead role."""
    global DEAD_ROLE_ID
    return f"<@&{DEAD_ROLE_ID}>"


def strip_ping(raw):
    """Strip a ping to get the user ID"""
    return raw.strip("<@!>")


def get_member_obj(userid):
    """Get the member object from the user ID"""
    return globvars.client.get_guild(SERVER_ID).get_member(int(userid))


def get_user_obj(userid):
    """Get the user object from the user ID"""
    return globvars.client.get_user(int(userid))


def make_code_block(msg):
    """Turn a message into a code block"""
    return f"```{msg}```"


def make_time_string(seconds):
    """Turn the number of seconds into a formatted time string"""
    return str(datetime.timedelta(seconds=seconds))


def update_state_machine():
    """Update the state machine"""
    globvars.master_state.state_machine.run(globvars.master_state)


def find_role_in_all(role_name):
    """
    Find a role name amongst all the loaded game packs.
    Return the role class if it is found, else return None

    The game_packs variable is coded in the following way:

    {'botc': {'game_obj': <botc.Game.Game object at 0x1187bffd0>, 'gamemodes': {'trouble-brewing': 
    [Baron Class, Butler Class, Chef Class, Drunk Class, Empath Class, Fortune Teller Class, Imp Class, 
    Investigator Class, Librarian Class, Mayor Class, Monk Class, Poisoner Class, Ravenkeeper Class, 
    Recluse Class, Saint Class, Scarlet Woman Class, Slayer Class, Soldier Class, Undertaker Class, 
    Virgin Class, Washerwoman Class]}}}
    """
    match = None
    for game_pack_title in globvars.master_state.game_packs:
        pack_content = globvars.master_state.game_packs[game_pack_title]
        for gamemode_title in pack_content["gamemodes"]:
            gamemode_content = pack_content["gamemodes"][gamemode_title]
            for role in gamemode_content:
                instance = role()
                if role_name.lower() == instance.name.lower():
                    return instance
                elif role_name.lower() in instance.name.lower() and not match:
                    match = instance
    return match

def get_gamemode_from_str(string: str):
    """
    Get the gamemode enum from a given string
    If no gamemode is found, then None is returned
    """

    from botc.gamemodes.Gamemode import Gamemode

    matches = {
        Gamemode.trouble_brewing : [
            "tb",
            "troublebrewing",
            "trouble brewing",
            "t b"
        ],
        Gamemode.bad_moon_rising : [
            "bmr",
            "badmoonrising",
            "bad moon rising",
            "b m r"
        ],
        Gamemode.sects_and_violets : [
            "snv",
            "sv",
            "s&v",
            "sectsandviolets",
            "sectsnviolets",
            "sects&violets",
            "sects and violets",
            "sects n violets",
            "sects & violets",
            "s n v",
            "s v",
            "s & v"
        ]
    }

    string = string.strip()
    string = string.lower()

    match = None
    for gm in matches:
        for elem in matches[gm]:
            if string == elem:
                return gm
            elif string in elem:
                match = gm

    return match

def get_emoji(s):
    """Get the emoji from a string"""
    if s in emoji.UNICODE_EMOJI['en']:
        return s
    else:
        try:
            em = globvars.client.get_emoji(int(re.split(r'[<:>]', s)[-2]))
            if em:
                return str(em)
            else:
                return None
        except Exception:
            return None


def get_member_from_string(string):
    """Find a member object from user input string.
    Code inspired from belungawhale's discord werewolf project.
    """
    import globvars
    string = string.lower()
    usernames = []
    discriminators = []
    nicknames = []
    ids_contains = []
    usernames_contains = []
    nicknames_contains = []
    for member in globvars.client.get_guild(SERVER_ID).members:
        if string == str(member.id) or string.strip('<@!>') == str(member.id):
            return member
        if str(member).lower().startswith(string):
            usernames.append(member)
        if string.strip('#') == member.discriminator:
            discriminators.append(member)
        if member.display_name.lower().startswith(string):
            nicknames.append(member)
        if string in member.name.lower():
            usernames_contains.append(member)
        if string in member.display_name.lower():
            nicknames_contains.append(member)
        if string in str(member.id):
            ids_contains.append(member)
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
    all_matches = set([*usernames, *discriminators, *nicknames, *usernames_contains, *nicknames_contains, *ids_contains])
    if all_matches:
        raise AmbiguousUserError(f"Ambiguous user: {string}", all_matches)
    return None


async def restart_bot(ctx, notify=True, force=False):
    if globvars.master_state.game and not force:
        return await ctx.send(bot_text["cmd"]["frestart_confirm"].format(ctx.author.mention, botutils.BotEmoji.x_emoji))

    if notify:
        await ctx.send(bot_text["cmd"]["frestart"].format(ctx.author.mention, botutils.BotEmoji.success))

    try:
        os.unlink("botc.pid")
    except FileNotFoundError:
        pass
    os.execl(sys.executable, sys.executable, *sys.argv)
