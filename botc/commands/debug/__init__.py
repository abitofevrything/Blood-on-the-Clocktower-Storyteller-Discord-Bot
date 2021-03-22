from .fnight import Fnight
from .fnomination import Fnomination
from .frole import Frole
from .fstop import Fstop
from .modkill import Modkill


def setup(client):
    client.add_cog(Fstop(client))
    client.add_cog(Modkill(client))
    client.add_cog(Frole(client))
    client.add_cog(Fnight(client))
    client.add_cog(Fnomination(client))
