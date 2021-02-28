from .assassinate import Assassinate
from .see import See
from .poison import Poison

def setup(client):
	client.add_cog(Assassinate(client))
	client.add_cog(See(client))
	client.add_cog(Poison(client))
