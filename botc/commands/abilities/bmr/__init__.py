from .assassinate import Assassinate
from .see import See

def setup(client):
	client.add_cog(Assassinate(client))
	client.add_cog(See(client))