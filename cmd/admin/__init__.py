from .deop import Deop
from .fgame import FGame
from .fjoin import Fjoin
from .fleave import Fleave
from .frestart import Frestart
from .fstart import Fstart
from .ignore import Ignore
from .op import Op
from .playtest import Playtest
from .update import Update

class _AdminCommands(Ignore, Op, Deop, Fstart, Fjoin, Fleave, Playtest, Frestart, Update, FGame):
    pass

def setup(client):
    client.add_cog(_AdminCommands(client))