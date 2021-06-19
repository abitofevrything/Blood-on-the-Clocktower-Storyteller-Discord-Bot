"""Blood on the Clocktower (BoTC) - Bad Moon Rising Edition Characters"""

import json
import sys

import globvars

try:
    with open("botc/gamemodes/badmoonrising/character_text.json") as character_texts_file:
        character_texts = json.load(character_texts_file)
except FileNotFoundError:
    globvars.logging.error("Unable to load Bad Moon Rising character text file. Does the file botc/gamemodes/badmoonrising/character_text.json exist?")
    sys.exit(1)

from .Assassin import Assassin
from .Chambermaid import Chambermaid
from .Courtier import Courtier
from .DevilsAdvocate import DevilsAdvocate
from .Exorcist import Exorcist
from .Fool import Fool
from .Gambler import Gambler
from .Godfather import Godfather
from .Goon import Goon
from .Gossip import Gossip
from .Grandmother import Grandmother
from .Innkeeper import Innkeeper
from .Lunatic import Lunatic
from .Mastermind import Mastermind
from .Minstrel import Minstrel
from .Moonchild import Moonchild
from .Pacifist import Pacifist
from .Po import Po
from .Professor import Professor
from .Pukka import Pukka
from .Sailor import Sailor
from .Shabaloth import Shabaloth
from .TeaLady import TeaLady
from .Tinker import Tinker
from .Zombuul import Zombuul
