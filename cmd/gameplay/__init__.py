from .join import Join
from .notify import Notify
from .quit import Quit
from .start import Start
from .stats import Stats
from .time import Time
from .votes import Votes


def setup(client):
    client.add_cog(Join(client))
    client.add_cog(Quit(client))
    client.add_cog(Time(client))
    client.add_cog(Stats(client))
    client.add_cog(Start(client))
    client.add_cog(Notify(client))
    client.add_cog(Votes(client))

