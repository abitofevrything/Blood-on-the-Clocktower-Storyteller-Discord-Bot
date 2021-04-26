from .nominate import Nominate
from .stats import Stats
from .time import Time
from .townsquare import Townsquare
from .whisper import Whisper
from .votestop import Votestop


def setup(client):
    client.add_cog(Nominate(client))
    client.add_cog(Stats(client))
    client.add_cog(Townsquare(client))
    client.add_cog(Whisper(client))
    client.add_cog(Time(client))
    client.add_cog(Votestop(client))
