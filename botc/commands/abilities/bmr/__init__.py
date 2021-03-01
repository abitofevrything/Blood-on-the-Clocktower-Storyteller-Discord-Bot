from .assassinate import Assassinate
from .see import See
from .poison import Poison
from.protect import Protect

def setup(client):
	client.add_cog(Assassinate(client))
	client.add_cog(See(client))
	client.add_cog(Poison(client))
	client.add_cog(Protect(client))