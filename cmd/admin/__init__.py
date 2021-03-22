from .deop import Deop
from .fjoin import Fjoin
from .fleave import Fleave
from .frestart import Frestart
from .fstart import Fstart
from .ignore import Ignore
from .op import Op
from .playtest import Playtest
from .update import Update


def setup(client):
    client.add_cog(Ignore(client))
    client.add_cog(Op(client))
    client.add_cog(Deop(client))
    client.add_cog(Fstart(client))
    client.add_cog(Fjoin(client))
    client.add_cog(Fleave(client))
    client.add_cog(Playtest(client))
    client.add_cog(Frestart(client))
    client.add_cog(Update(client))
