from .fnight import Fnight
from .fnomination import Fnomination
from .fdawn import Fdawn
from .fday import Fday
from .frole import Frole
from .fstop import Fstop
from .modkill import Modkill
from .revealrole import RevealRole

def setup(client):
    client.add_cog(Fstop(client))
    client.add_cog(Modkill(client))
    client.add_cog(Frole(client))
    client.add_cog(Fnight(client))
    client.add_cog(Fnomination(client))
    client.add_cog(Fdawn(client))
    client.add_cog(Fday(client))
    client.add_cog(RevealRole(client))
