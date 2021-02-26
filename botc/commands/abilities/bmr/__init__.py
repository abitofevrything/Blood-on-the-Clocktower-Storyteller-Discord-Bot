from .assassinate import Assassinate

def setup(client):
	client.add_cog(Assassinate(client))