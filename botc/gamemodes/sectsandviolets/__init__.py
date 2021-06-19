"""Blood on the Clocktower (BoTC) - Sects & Violets Edition Characters"""

import json
import sys

import globvars

try:
    with open("botc/gamemodes/sectsandviolets/character_text.json") as character_texts_file:
        character_texts = json.load(character_texts_file)
except FileNotFoundError:
    globvars.logging.error("Unable to load Sects and Violets character text file. Does the file botc/gamemodes/sectsandviolets/character_text.json exist?")
    sys.exit(1)

from .Artist import Artist
from .Barber import Barber
from .Cerenovus import Cerenovus
from .Clockmaker import Clockmaker
from .Dreamer import Dreamer
from .EvilTwin import EvilTwin
from .FangGu import FangGu
from .Flowergirl import Flowergirl
from .Juggler import Juggler
from .Klutz import Klutz
from .Mathematician import Mathematician
from .Mutant import Mutant
from .NoDashii import NoDashii
from .Oracle import Oracle
from .Philosopher import Philosopher
from .PitHag import PitHag
from .Sage import Sage
from .Savant import Savant
from .Seamstress import Seamstress
from .SnakeCharmer import SnakeCharmer
from .Sweetheart import Sweetheart
from .TownCrier import TownCrier
from .Vigormortis import Vigormortis
from .Vortox import Vortox
from .Witch import Witch
