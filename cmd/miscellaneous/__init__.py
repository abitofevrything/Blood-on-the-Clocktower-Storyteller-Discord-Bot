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


def setup(client):
    client.add_cog(Github(client))
    client.add_cog(Ping(client))
    client.add_cog(Uptime(client))
    client.add_cog(Dog(client))
    client.add_cog(Coin(client))
    client.add_cog(Role(client))
    client.add_cog(Gamestats(client))
    client.add_cog(Playerstats(client))
    client.add_cog(Top(client))
    client.add_cog(Sync(client))
    client.add_cog(Streak(client))
    client.add_cog(Statements(client))
