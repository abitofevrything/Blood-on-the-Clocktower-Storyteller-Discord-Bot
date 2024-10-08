from .coin import Coin
from .dog import Dog
from .gamestats import Gamestats
from .github import Github
from .ping import Ping
from .playerstats import Playerstats
from .role import Role
from .statements import Statements
from .streak import Streak
from .sync import Sync
from .top import Top
from .uptime import Uptime

class _MiscCommands(Github, Ping, Uptime, Dog, Coin, Role, Gamestats, Playerstats, Top, Sync, Streak, Statements):
    pass

def setup(client):
    client.add_cog(_MiscCommands(client))
