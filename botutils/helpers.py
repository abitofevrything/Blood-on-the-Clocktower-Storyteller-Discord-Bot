"""Contains other helper functions"""

import datetime
import os
import re
import sys

import emoji
import toml

import globvars

with open("config.toml") as fd:
    config = toml.load(fd)

    SERVER_ID = config["ids"]["server_id"]
    ALIVE_ROLE_ID = config["ids"]["alive_role_id"]
    DEAD_ROLE_ID = config["ids"]["dead_role_id"]


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
    return globvars.client.get_guild(int(SERVER_ID)).get_member(int(userid))


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
    [Baron Obj, Butler Obj, Chef Obj, Drunk Obj, Empath Obj, Fortune Teller Obj, Imp Obj,
    Investigator Obj, Librarian Obj, Mayor Obj, Monk Obj, Poisoner Obj, Ravenkeeper Obj,
    Recluse Obj, Saint Obj, Scarlet Woman Obj, Slayer Obj, Soldier Obj, Undertaker Obj,
    Virgin Obj, Washerwoman Obj]}}}
    """
    match = None
    for game_pack_title in globvars.master_state.game_packs:
        pack_content = globvars.master_state.game_packs[game_pack_title]
        for gamemode_title in pack_content["gamemodes"]:
            gamemode_content = pack_content["gamemodes"][gamemode_title]
            for role in gamemode_content:
                if role_name.lower() == role.name.lower():
                    return role
                elif role_name.lower() in role.name.lower() and not match:
                    match = role
    return match


def get_emoji(s):
    """Get the emoji from a string"""
    if s in emoji.UNICODE_EMOJI['en']:
        return s
    else:
        em = globvars.client.get_emoji(int(re.split(r'[<:>]', s)[-2]))
        if em:
            return em
        else:
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
    for member in globvars.client.get_guild(int(SERVER_ID)).members:
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


def restart_bot():
    os.unlink("botc.pid")
    os.execl(sys.executable, sys.executable, *sys.argv)
