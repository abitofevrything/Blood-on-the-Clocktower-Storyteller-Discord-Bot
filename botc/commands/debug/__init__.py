from .fdawn import Fdawn
from .fday import Fday
from .fnight import Fnight
from .fnomination import Fnomination
from .frole import Frole
from .fstop import Fstop
from .modkill import Modkill
from .modrevive import Modrevive
from .revealrole import RevealRole

class _DebugCommands(Fstop, Modkill, Frole, Fnight, Fnomination, Fdawn, Fday, RevealRole, Modrevive):
    pass

def setup(client):
    client.add_cog(_DebugCommands(client))
