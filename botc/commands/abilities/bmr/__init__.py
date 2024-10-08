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

class _BmrAbilitiesCommands(Assassinate, See, Poison, Protect, Exorcise, Guess, Execute, Gossip, Visit, Host, Examine, Choose, Kill, Pass, Curse):
	pass

def setup(client):
	client.add_cog(_BmrAbilitiesCommands(client))
