"""Notes-related classes"""

import asyncio
import math

from discord.ext import commands

import botutils
import globvars


class NotesEntry:
    """Represents a single Entry into some Notes.
    Contains info about claim, player info and additional notes.
    """

    def __init__(self, player) -> None:
        self._player = player

        self._claimed_role = None
        self._claimed_category = None
        self._info = []
        self._notes = []

    def claim(self, category, role):
        self._claimed_category = category
        self._claimed_role = role

    def info(self, info, n):
        while n >= len(self._info):
            self._info.append('')
        if info is None:
            info = ''
        self._info[n] = info

        while len(self._info) > 0 and self._info[-1] == '':
            self._info.pop()

    def note(self, note):
        self._notes.append(note)

    @property
    def info_list(self):
        return self._info

    @property
    def notes(self):
        return self._notes

    @property
    def claimed_category(self):
        return self._claimed_category

    @property
    def claimed_role(self):
        return self._claimed_role

    @property
    def player(self):
        return self._player


class Notes:
    """Represents a set of notes.
    Can be either the public set or a player's private notes.
    """

    def __init__(self, player_list, player = None) -> None:
        self._entries = {p: NotesEntry(p) for p in player_list}
        self._player = player

    def get_entry(self, player):
        return self._entries[player]

    @property
    def entries(self):
        return self._entries.values()

    @property
    def player(self):
        return self._player


class NotesManager:
    """Manages global note operations, such as madness, and provides easy access to player's notes
    """

    def __init__(self, public_notes, private_notes) -> None:
        self._private_notes = private_notes
        self._public_notes = public_notes

        self._self_madness = {e.player: (None, None) for e in self._public_notes.entries}
        self._inferred_madness = {e.player: (None, None) for e in self._public_notes.entries}

    def public_notes(self):
        return self._public_notes

    def private_notes(self, player):
        return next(n for n in self._private_notes if n.player == player)

    def claim(self, player, category, role, target_notes = None):
        """Inserts a claim into a player's notes.
        If `target_notes` is None, will be claimed publically.
        Runs the claim trigger on the relevant player if needed.
        """
        if category is None:
            if role is None:
                return
            category = role.category

        if target_notes is None:
            self._public_notes.get_entry(player).claim(category, role)
            if self._self_madness[player] != (category, role):
                asyncio.create_task(player.role.true_self.on_claim(player, category, role, True))
                self._self_madness[player] = (category, role)
        else:
            self.private_notes(target_notes).get_entry(player).claim(category, role)
            # Check for madness
            # Madness is declared if >= floor(nb_players / 2) think a player is a category or role

            if self.check_madness(player, category, role):
                if self._inferred_madness[player] != (category, role) and self._self_madness[player] != (category, role):
                    self._inferred_madness[player] = (category, role)
                    asyncio.create_task(player.role.true_self.on_claim(player, category, role, False))
            elif self.check_madness(player, category):
                if self._inferred_madness[player][0] != category and self._self_madness[player][0] != category:
                    self._inferred_madness[player] = (category, None)
                    asyncio.create_task(player.role.true_self.on_claim(player, category, role, False))

    def rm_claim(self, player, target_notes = None):
        if target_notes is None:
            self._public_notes.get_entry(player).claim(None, None)
            if self._self_madness[player] != (None, None):
                asyncio.create_task(player.role.true_self.on_claim(player, None, None, True))
                self._self_madness[player] = (None, None)
        else:
            self.private_notes(target_notes).get_entry(player).claim(None, None)
            # Check if madness is still valid
            madness = self.check_madness(player, self._inferred_madness[player][0], self._inferred_madness[player][1])
            if not madness:
                self._inferred_madness[player] = (None, None)
                asyncio.create_task(player.role.true_self.on_claim(player, None, None, False))

    def info(self, player, info, target_notes = None, n = None):
        if n is None:
            n = globvars.master_state.game._chrono.cycle

        if n <= 0:
            raise commands.BadArgument()

        if target_notes is None:
            self._public_notes.get_entry(player).info(info, n - 1) # Remove one to get 0-based index
        else:
            self.private_notes(target_notes).get_entry(player).info(info, n - 1) # Remove one to get 0-based index

    def rm_info(self, player, info_idx = None, target_notes = None):
        if info_idx is None:
            info_idx = globvars.master_state.game._chrono.cycle

        if info_idx <= 0:
            raise commands.BadArgument()

        if target_notes is None:
            self._public_notes.get_entry(player).info(None, info_idx - 1) # Remove one to get 0-based index
        else:
            self.private_notes(target_notes).get_entry(player).info(None, info_idx - 1) # Remove one to get 0-based index

    def note(self, player, note, target_notes):
        if target_notes is None:
            return # Cannot add extra notes to public notes
        self.private_notes(target_notes).get_entry(player).note(note)

    def rm_note(self, player, note_idx, target_notes):
        if target_notes is None:
            return # Cannot add extra notes to public notes
        if note_idx <= 0 or note_idx > len(self.private_notes(target_notes).get_entry(player).notes):
            raise commands.BadArgument()
        self.private_notes(target_notes).get_entry(player).notes.pop(note_idx - 1) # Remove one to get 0-based index

    def check_madness(self, player, category, role = None):
        """Checks if a given player is mad
        """

        # "Inferred" madness
        if role is None:
            num_matching = len(list(filter(lambda n: n.get_entry(player).claimed_category == category, self._private_notes)))
            return num_matching >= math.floor(globvars.master_state.game.nb_players / 2)
        else:
            num_matching = len(list(filter(lambda n: n.get_entry(player).claimed_role == role, self._private_notes)))
            return num_matching >= math.floor(globvars.master_state.game.nb_players / 2)

    def is_cc(self, player, target_notes=None, check_private=False):
        if target_notes is None:
            player_entry = self._public_notes.get_entry(player)
            if player_entry.claimed_role is None:
                return False

            for entry in self._public_notes.entries:
                if entry.player == player:
                    continue
                elif (entry.claimed_role.name if entry.claimed_role else '') == player_entry.claimed_role.name:
                    return True
            return False
        else:
            if check_private:
                player_entry = self.private_notes(target_notes).get_entry(player)
                if player_entry.claimed_role is None:
                    return False

                for entry in self._public_notes.entries:
                    if entry.player == player:
                        continue
                    elif (entry.claimed_role.name if entry.claimed_role else '') == player_entry.claimed_role.name:
                        return True

                for entry in self.private_notes(target_notes).entries:
                    if entry.player == player:
                        continue
                    elif (entry.claimed_role.name if entry.claimed_role else '') == player_entry.claimed_role.name:
                        return True
                return False
            else:
                player_entry = self._public_notes.get_entry(player)
                if player_entry.claimed_role is None:
                    return False

                for entry in self._public_notes.entries:
                    if entry.player == player:
                        continue
                    elif (entry.claimed_role.name if entry.claimed_role else '') == player_entry.claimed_role.name:
                        return True

                for entry in self.private_notes(target_notes).entries:
                    if entry.player == player:
                        continue
                    elif (entry.claimed_role.name if entry.claimed_role else '') == player_entry.claimed_role.name:
                        return True
                return False

    def format_notes(self, target_notes = None):
        msg = ""
        game = globvars.master_state.game

        # Get some values for spacing
        max_player_name_len = len(max(game.sitting_order, key=lambda player: len(player.user.display_name)).user.display_name)

        if target_notes is None:
            for entry in self._public_notes.entries:
                player = entry.player

                death_indicator = '[ALIVE]' if player.is_apparently_alive() else '[DEAD] '
                player_name = player.user.display_name.ljust(max_player_name_len, ' ')
                claim = (entry.claimed_role.name if entry.claimed_role else
                         (entry.claimed_category.value if entry.claimed_category else ''))

                if self.is_cc(player):
                    claim += ' [CC]'

                info_str = ''
                for info in entry.info_list:
                    if info:
                        info_str += ' [' + (str(info) if info else '?') + ']'

                msg += f"{death_indicator} {player_name} - {claim}{info_str}\n"
        else:
            for entry, public_entry in zip(self.private_notes(target_notes).entries, self._public_notes.entries):
                player = entry.player

                death_indicator = '[ALIVE]' if player.is_apparently_alive() else '[DEAD] '
                player_name = player.user.display_name.ljust(max_player_name_len, ' ')
                public_claim = (public_entry.claimed_role.name if public_entry.claimed_role else
                                (public_entry.claimed_category.value if public_entry.claimed_category else ''))

                if self.is_cc(player):
                    public_claim += ' [CC]'
                elif self.is_cc(player, target_notes, False):
                    public_claim += ' ([CC])'

                public_info_str = ''
                for info in public_entry.info_list:
                    public_info_str += ' [' + (str(info) if info else '?') + ']'

                private_claim = (entry.claimed_role.name if entry.claimed_role else
                                 (entry.claimed_category.value if entry.claimed_category else ''))

                if self.is_cc(player, target_notes, True):
                    private_claim += ' [CC]'

                private_info_str = ''
                for info in entry.info_list:
                    private_info_str += ' [' + (str(info) if info else '?') + ']'

                msg += f"{death_indicator} {player_name} - "

                if private_claim:
                    msg += f"({private_claim}"
                    if not private_info_str:
                        msg += ') '

                if private_info_str:
                    if not private_claim:
                        msg += "("
                    msg += private_info_str + ") "

                msg += f"{public_claim}{public_info_str}\n"

                for note in entry.notes:
                    msg += f"        - {note}\n"

        return botutils.make_code_block('ini\n' + msg)
