"""Contains some checking functions for botc commands"""

import configparser
from botc import BOTCUtils, NotAPlayer, RoleCannotUseCommand, AliveOnlyCommand, \
    DeadOnlyCommand, NotDay, NotDawn, NotNight, NotDMChannel, NotLobbyChannel

Config = configparser.ConfigParser()
Config.read("config.INI")

LOBBY_CHANNEL_ID = Config["user"]["LOBBY_CHANNEL_ID"]


def check_if_is_player(ctx):
    """Return true if user is a player, and not in fleaved state"""
    player = BOTCUtils.get_player_from_id(ctx.author.id)
    if player:
        if player.is_fleaved():
            raise NotAPlayer("Command not allowed: user has quit the game (BoTC).")
        else:
            return True
    else:
        raise NotAPlayer("Command not allowed: user is not a player (BoTC).")


def can_use_serve(user_id):
    """Return true if the user can use the command "serve"
    Characters that can serve: 
    - Butler
    """
    from botc.gamemodes.troublebrewing._utils import TBRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [TBRole.butler.value]:
        return True
    return False


def check_if_can_serve(ctx):
    """Return true if the command user can use the command "serve"
    Command check function
    """
    if can_use_serve(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use serve command (BoTC)")


def can_use_poison(user_id):
    """Return true if the user can use the command "poison"
    Characters that can poison:
    - Poisoner
    - Courtier
    """
    from botc.gamemodes.troublebrewing._utils import TBRole
    from botc.gamemodes.badmoonrising._utils import BMRRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [TBRole.poisoner.value, BMRRole.courtier.value]:
        return True
    return False


def check_if_can_poison(ctx):
    """Return true if the command user can use the command "poison"
    Command check function
    """
    if can_use_poison(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use poison command (BoTC)")


def can_use_learn(user_id):
    """Return true if the user can use the command "learn"
    Characters that can learn:
    - Ravenkeeper
    """
    from botc.gamemodes.troublebrewing._utils import TBRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [TBRole.ravenkeeper.value]:
        return True
    return False


def check_if_can_learn(ctx):
    """Return true if the command user can use the command "learn"
    Command check function
    """
    if can_use_learn(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use learn command (BoTC)")


def can_use_read(user_id):
    """Return true if the user can use the command "read"
    Characters that can read:
    - Fortune teller
    """
    from botc.gamemodes.troublebrewing._utils import TBRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [TBRole.fortuneteller.value]:
        return True
    return False


def check_if_can_read(ctx):
    """Return true if the command user can use the command "read"
    Command check function
    """
    if can_use_read(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use read command (BoTC)")


def can_use_kill(user_id):
    """Return true if the user can use the command "kill"
    Characters that can kill:
    - Imp
    """
    from botc.gamemodes.troublebrewing._utils import TBRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [TBRole.imp.value]:
        return True
    return False


def check_if_can_kill(ctx):
    """Return true if the command user can use the command "kill"
    Command check function
    """
    if can_use_kill(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use kill command (BoTC)")


def can_use_slay(user_id):
    """Return true if the user can use the command "slay"
    Characters that can slay:
    - All characters (to allow for fake claiming)
    """
    return True


def check_if_can_slay(ctx):
    """Return true if the command user can use the command "slay"
    Command check function
    """
    if can_use_slay(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use slay command (BoTC)")


def can_use_protect(user_id):
    """Return true if the user can use the command "protect"
    Characters that can protect:
    - Monk
    """
    from botc.gamemodes.troublebrewing._utils import TBRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [TBRole.monk.value]:
        return True
    return False


def check_if_can_protect(ctx):
    """Return true if the command user can use the command "protect"
    Command check function
    """
    if can_use_protect(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use protect command (BoTC)")

def can_use_assassinate(user_id):
    """Return true if the user can use the command "assassinate"
    Characters that can assassinate:
    - Assassin
    """
    from botc.gamemodes.badmoonrising._utils import BMRRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [BMRRole.assassin.value]:
       return True
    return False

def check_if_can_assassinate(ctx):
    """Return True if the user can use the command "assassinate"
    Command check function
    """
    if can_use_assassinate(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use assassinate command (BoTC)")

def can_use_see(user_id):
    """Return true if the user can use the command "see"
    Characters that can see:
    - Chambermaid
    """
    from botc.gamemodes.badmoonrising._utils import BMRRole
    player = BOTCUtils.get_player_from_id(user_id)
    if player.role.ego_self.name in [BMRRole.chambermaid.value]:
        return True
    return False

def check_if_can_see(ctx):
    """Return true if the user can use the command "see"
    Characters that can see:
    - Chambermaid
    """
    if can_use_see(ctx.author.id):
        return True
    else:
        raise RoleCannotUseCommand("Cannot use see command (BoTC)")


def check_if_is_night(ctx):
    """Check if the game is in night phase"""
    import globvars
    if globvars.master_state.game.is_night():
        return True
    else:
        raise NotNight("Command is allowed during night phase only (BoTC)")


def check_if_is_dawn(ctx):
    """Check if the game is in dawn phase"""
    import globvars
    if globvars.master_state.game.is_dawn():
        return True
    else:
        raise NotDawn("Command is allowed during dawn phase only (BoTC")


def check_if_is_day(ctx):
    """Check if the game is in day phase"""
    import globvars
    if globvars.master_state.game.is_day():
        return True
    else:
        raise NotDay("Command is allowed during day phase only (BoTC)")


def check_if_dm(ctx):
    """Check if the command is invoked in a dm channel."""
    if ctx.guild is None:
        return True
    else:
        raise NotDMChannel("Only DM allowed (BoTC)")


def check_if_lobby(ctx):
    """Check if the command is invoked in the lobby."""
    if ctx.channel.id == int(LOBBY_CHANNEL_ID):
        return True
    else:
        raise NotLobbyChannel("Only lobby allowed (BoTC)")


def check_if_player_apparently_alive(ctx):
    """Check if the player is alive using apprent state"""
    player = BOTCUtils.get_player_from_id(ctx.author.id)
    if player.is_apparently_alive():
        return True
    else:
        raise AliveOnlyCommand("Command reserved for Alive Players (BoTC)")


def check_if_player_apparently_dead(ctx):
    """Check if the player is dead using apparent state"""
    player = BOTCUtils.get_player_from_id(ctx.author.id)
    if player.is_apparently_dead():
        return True
    else:
        raise DeadOnlyCommand("Command reserved for Dead Players (BoTC)")


def check_if_player_really_alive(ctx):
    """Check if the player is alive using real state"""
    player = BOTCUtils.get_player_from_id(ctx.author.id)
    if player.is_alive():
        return True
    else:
        raise AliveOnlyCommand("Command reserved for Alive Players (BoTC)")


def check_if_player_really_dead(ctx):
    """Check if the player is dead using real state"""
    player = BOTCUtils.get_player_from_id(ctx.author.id)
    if player.is_dead():
        return True
    else:
        raise DeadOnlyCommand("Command reserved for Dead Players (BoTC)")
