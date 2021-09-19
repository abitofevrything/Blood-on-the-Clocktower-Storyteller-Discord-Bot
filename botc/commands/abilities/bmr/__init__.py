from .assassinate import Assassinate
from .poison import Poison
from .see import See

from.protect import Protect
from .choose import Choose
from .curse import Curse
from .examine import Examine
from .execute import Execute
from .exorcise import Exorcise
from .gossip import Gossip
from .guess import Guess
from .host import Host
from .kill import Kill
from .pass_ability import Pass
from .visit import Visit


def setup(client):
	client.add_cog(Assassinate(client))
	client.add_cog(See(client))
	client.add_cog(Poison(client))
	client.add_cog(Protect(client))
	client.add_cog(Exorcise(client))
	client.add_cog(Guess(client))
	client.add_cog(Execute(client))
	client.add_cog(Gossip(client))
	client.add_cog(Visit(client))
	client.add_cog(Host(client))
	client.add_cog(Examine(client))
	client.add_cog(Choose(client))
	client.add_cog(Kill(client))
	client.add_cog(Pass(client))
	client.add_cog(Curse(client))
