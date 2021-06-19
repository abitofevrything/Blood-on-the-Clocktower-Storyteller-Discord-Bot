from .getrole import GetRole
from .nominate import Nominate
from .stats import Stats
from .time import Time
from .townsquare import Townsquare
from .votestop import Votestop
from .whisper import Whisper


def setup(client):
    client.add_cog(Nominate(client))
    client.add_cog(Stats(client))
    client.add_cog(Townsquare(client))
    client.add_cog(Whisper(client))
    client.add_cog(Time(client))
    client.add_cog(Votestop(client))
    client.add_cog(GetRole(client))
