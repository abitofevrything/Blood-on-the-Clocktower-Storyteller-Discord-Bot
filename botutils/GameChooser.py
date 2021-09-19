"""Contains the GameChooser class"""

import json

from discord.ext import commands

from botc.gamemodes.Gamemode import Gamemode
from botutils import BotEmoji, bot_text

gamemode_not_found = bot_text["cmd"]["gm_not_found"]
voting_diabled = bot_text["cmd"]["voting_diabled"]

x_emoji = BotEmoji.x_emoji

class VotingDisabled(commands.BadArgument):
    """Error to indicate votes are disabled"""
    pass


class GameChooser:
    """A class to faciliate gamemode choosing and voting"""

    selected_gamemode = Gamemode.trouble_brewing # Default gamemode is TB

    def __init__(self):
        from botc.Game import Game

        self._games = {
            Gamemode.trouble_brewing : Game(Gamemode.trouble_brewing),
            Gamemode.bad_moon_rising : Game(Gamemode.bad_moon_rising),
            # Uncomment once sv is implemented to allow people to play sv
            # Gamemode.sects_and_violets : Game(Gamemode.sects_and_violets),
            None: Game() # Default game
        }

        self._votes = {
            gm : [] for gm in self._games if gm is not None
        }

        self.enabled = True

    def register_vote(self, user_id, vote = Gamemode.trouble_brewing):
        """Register a user's vote"""

        if not self.enabled:
            from botutils import make_ping
            raise VotingDisabled(voting_diabled.format(make_ping(user_id), x_emoji))

        if vote not in self._votes:
            # This exception will trigger when a gamemode that has been recognized by the
            # gamemode parser is not availible to play. 
            from botc.BOTCUtils import GamemodeNotFound
            raise GamemodeNotFound(gamemode_not_found.format(x_emoji, f"<@{user_id}>", vote.value))

        for gm in self._votes:
            if user_id in self._votes[gm]:
                self._votes[gm].remove(user_id)

        self._votes[vote].append(user_id)

        # Update the selected gamemode
        highest = (None, -1)

        for gm in self._votes:
            if len(self._votes[gm]) > highest[1]:
                highest = (gm, len(self._votes[gm]))

        self.selected_gamemode = highest[0]

    def clear_votes(self):
        """Clear all votes"""
        for gm in self._votes:
            self._votes[gm].clear()
        self.selected_gamemode = Gamemode.trouble_brewing

    @property
    def default_game(self):
        return self._games[None]

    def select_gamemode(self, gamemode, user_id):
        """Select a gamemode (force)"""
        if not gamemode in self._games:
            from botc.BOTCUtils import GamemodeNotFound
            raise GamemodeNotFound(gamemode_not_found.format(x_emoji, f"<@{user_id}>", gamemode.value))
        self.selected_gamemode = gamemode

    def remove_vote(self, user_id):
        """Remove a user's vote"""
        for gm in self._votes:
            if user_id in self._votes[gm]:
                self._votes[gm].remove(user_id)

        highest = (None, -1)

        for gm in self._votes:
            if len(self._votes[gm]) > highest[1]:
                highest = (gm, len(self._votes[gm]))

        self.selected_gamemode = highest[0]

    def get_vote(self, user_id):
        """Get a user's vote"""
        for gm in self._votes:
            if user_id in self._votes[gm]:
                return gm
        return None
        
    @property
    def votes(self):
        return {gm: len(self._votes[gm]) for gm in self._votes if gm is not None}

    def get_selected_game(self):
        return self._games[self.selected_gamemode]

    def disable_voting(self):
        self.clear_votes()
        self.enabled = False

    def enable_voting(self):
        self.enabled = True

    def is_enabled(self):
        return self.enabled