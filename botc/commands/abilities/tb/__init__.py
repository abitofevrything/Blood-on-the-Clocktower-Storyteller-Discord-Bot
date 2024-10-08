from .kill import Kill
from .learn import Learn
from .poison import Poison
from .protect import Protect
from .read import Read
from .serve import Serve
from .slay import Slay

class _TbGameplayCommands(Kill, Learn, Poison, Protect, Read, Serve, Slay):
    pass

def setup(client):
    client.add_cog(_TbGameplayCommands(client))
