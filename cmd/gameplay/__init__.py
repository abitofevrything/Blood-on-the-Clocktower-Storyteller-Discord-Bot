from .join import Join
from .notify import Notify
from .quit import Quit
from .start import Start
from .stats import Stats
from .time import Time
from .votes import Votes

class _GameplayCommands(Join, Quit, Time, Stats, Start, Notify, Votes):
    pass

def setup(client):
    client.add_cog(_GameplayCommands(client))

