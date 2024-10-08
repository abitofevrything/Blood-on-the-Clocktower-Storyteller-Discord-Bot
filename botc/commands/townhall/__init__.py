from .getrole import GetRole
from .nominate import Nominate
from .stats import Stats
from .time import Time
from .townsquare import Townsquare
from .votestop import Votestop
from .whisper import Whisper


class _TownhallCommands(Nominate, Stats, Townsquare, Whisper, Time, Votestop, GetRole):
    pass

def setup(client):
    client.add_cog(_TownhallCommands(client))
