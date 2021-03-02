from .assassinate import Assassinate
from .see import See
from .poison import Poison
from.protect import Protect
from .exorcise import Exorcise
from .guess import Guess

def setup(client):
	client.add_cog(Assassinate(client))
	client.add_cog(See(client))
	client.add_cog(Poison(client))
	client.add_cog(Protect(client))
	client.add_cog(Exorcise(client))
	client.add_cog(Guess(client))