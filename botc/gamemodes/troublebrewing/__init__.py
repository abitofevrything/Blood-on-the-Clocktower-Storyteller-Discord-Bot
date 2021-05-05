"""Blood on the Clocktower (BoTC) - Trouble Brewing Edition Characters"""

import json
import sys
import globvars

try:
    with open("botc/gamemodes/troublebrewing/character_text.json") as character_texts_file:
        character_texts = json.load(character_texts_file)
except FileNotFoundError:
    globvars.logging.error("Unable to load trouble brewing character text file. Does the file botc/gamemodes/troublebrewing/character_text.json exist?")
    sys.exit(1)

from .Baron import Baron
from .Butler import Butler
from .Chef import Chef
from .Drunk import Drunk
from .Empath import Empath
from .FortuneTeller import FortuneTeller
from .Imp import Imp
from .Investigator import Investigator
from .Librarian import Librarian
from .Mayor import Mayor
from .Monk import Monk
from .Poisoner import Poisoner
from .Ravenkeeper import Ravenkeeper
from .Recluse import Recluse
from .Saint import Saint
from .ScarletWoman import ScarletWoman
from .Slayer import Slayer
from .Soldier import Soldier
from .Spy import Spy
from .Undertaker import Undertaker
from .Virgin import Virgin
from .Washerwoman import Washerwoman

