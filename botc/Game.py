"""Contains the BOTC Game class"""

import asyncio
import datetime
import json
import random
import sqlite3

import discord
import pytz
import toml

import botutils
import globvars
from botc import StatusList, Team, game_text
from botc.Notes import Notes, NotesManager
from config import (DAWN_CARD_COLOR, DAY_CARD_COLOR, DEBUG, DEMON_CARD_COLOR,
                    DISABLE_DMS, NIGHT_CARD_COLOR, NO_INVALIDATE, SERVER_ID,
                    TIMEZONE, TOWNSFOLK_CARD_COLOR)
from library import fancy
from models import GameMeta

from .abilities import _GrowingList
from .BOTCUtils import BOTCUtils
from .Category import Category
from .chrono import GameChrono
from .Demon import Demon
from .errors import GameError, TooFewPlayers, TooManyPlayers
from .gameloops import (base_day_loop, debate_timer, master_game_loop,
                        nomination_loop)
from .gamemodes.badmoonrising._utils import BadMoonRising
from .gamemodes.Gamemode import Gamemode
from .gamemodes.sectsandviolets._utils import SectsAndViolets
from .gamemodes.troublebrewing._utils import TroubleBrewing
from .gamemodes.troublebrewing.Drunk import Drunk
from .gamemodes.troublebrewing.Saint import Saint
from .Minion import Minion
from .Outsider import Outsider
from .Phase import Phase
from .Player import Player
from .PlayerState import PlayerState
from .RoleGuide import RoleGuide
from .Townsfolk import Townsfolk

CONFLICTING_CMDS = [
   "cmd.gameplay"
]

random.seed(datetime.datetime.now())

nightfall = game_text["gameplay"]["nightfall"]
daybreak = game_text["gameplay"]["daybreak"]
dawn = game_text["gameplay"]["dawn"]
lobby_game_start = game_text["gameplay"]["lobby_game_start"]
lobby_game_closing = game_text["gameplay"]["lobby_game_closing"]
evilteammates = game_text["gameplay"]["evilteammates"]
copyrights_str = game_text["misc"]["copyrights"]
tb_lore = game_text["gameplay"]["tb_lore"]
bmr_lore = game_text["gameplay"]["bmr_lore"]
snv_lore = game_text["gameplay"]["snv_lore"]
nightfall_image = game_text["images"]["nightfall"]
dawn_image = game_text["images"]["dawn"]
daybreak_image = game_text["images"]["daybreak"]
dove = game_text["images"]["dove"]
demon = game_text["images"]["demon"]
no_one_wins = game_text["gameplay"]["no_one_wins"]
good_wins = game_text["gameplay"]["good_wins"]
evil_wins = game_text["gameplay"]["evil_wins"]
role_reveal = game_text["gameplay"]["role_reveal"]
role_reveal_herring = game_text["gameplay"]["role_reveal_herring"]
storyteller_death = game_text["lore"]["storyteller_death"]
ego_role_reveal = game_text["gameplay"]["ego_role_reveal"]
ego_role_reveal_herring = game_text["gameplay"]["ego_role_reveal_herring"]
changed_role_reveal = game_text["gameplay"]["changed_role_reveal"]


class Setup:
    """A class to facilitate role to player access"""

    DEMON_HEAD_EMOJI = botutils.BotEmoji.demonhead

    def __init__(self):

        self.demon = []
        self.minions = []
        self.townsfolks = []
        self.outsiders = []
        self.role_dict = {}  # {"recluse" : player_obj1, "undertaker" : player_obj2}
        self.gamemode = None
        self.game = None

    def create(self, player_ob_list, gamemode, game):

        self.gamemode = gamemode
        self.game = game

        for player in player_ob_list:
            self.role_dict.update({player.role.name: player})
            if player.role.category == Category.demon:
                self.demon.append(player)
            elif player.role.category == Category.minion:
                self.minions.append(player)
            elif player.role.category == Category.townsfolk:
                self.townsfolks.append(player)
            elif player.role.category == Category.outsider:
                self.outsiders.append(player)
        assert len(self.demon) == 1, "More than 1 demon found."

    def create_evil_team_string(self):
        """
        :demonhead: Your Evil team consists of:
        ```basic
        Oliver (460105234748801024) (demon)
        Johnny (159985870458322944) (minion)
        Michel (614109280508968980) (minion)
        ```
        """
        msg = Setup.DEMON_HEAD_EMOJI + " " + evilteammates + "```basic\n"
        for demon in self.demon:
            msg += f"{demon.user.display_name} ({demon.user.id}) (demon)"
            msg += "\n"
        for minion in self.minions:
            msg += f"{minion.user.display_name} ({minion.user.id}) (minion)"
            msg += "\n"
        msg += "```"
        return msg

    def create_fake_evil_team_string(self, fake_demon):
        """
        :demonhead: Your Evil team consists of:
        ```basic
        Oliver (460105234748801024) (demon)
        Johnny (159985870458322944) (minion)
        Michel (614109280508968980) (minion)
        ```
        """

        guide = RoleGuide(len(self.game._member_obj_list))
        players = list(self.game.player_obj_list)

        players.remove(fake_demon)

        random.shuffle(players)

        fake_demons = [fake_demon]
        for _ in range(0, guide.nb_demons - 1):
            fake_demons.append(players.pop())

        fake_minions = list()
        for _ in range(0, guide.nb_minions):
            fake_minions.append(players.pop())

        msg = Setup.DEMON_HEAD_EMOJI + " " + evilteammates + "```basic\n"
        for demon in fake_demons:
            msg += f"{demon.user.display_name} ({demon.user.id}) (demon)"
            msg += "\n"
        for minion in fake_minions:
            msg += f"{minion.user.display_name} ({minion.user.id}) (minion)"
            msg += "\n"
        msg += "```"
        return msg


    def clear(self):

        self.__init__()

    def __str__(self):
        return f"Game setup: townsfolk {self.townsfolks}, outsiders {self.outsiders}, minions {self.minions}, demons {self.demon}"


class GameLog:
    """Game log class"""

    def __init__(self, game_obj):
        self.setup = game_obj.setup
        self.sitting_order = game_obj.sitting_order
        self.gamemode = game_obj.gamemode.value

    def create_game_obj_log_str(self, roles_only=False):
        """Create the game log string. The string looks like this:

        Game Start:
        ```asciidoc
        BoTC game started at 2020-06-19T19:50:04.657050-04:00, with 10 players, using the Trouble-Brewing edition.
        --------------------
        DEMON :: [Tester 1 (614109280508968980) is Imp]
        MINION :: [Tester 5 (235088799074484224) is Baron, Tester 3 (159985870458322944) is Spy]
        TOWNSFOLK :: [Tester 6 (172002275412279296) is Chef, Tester 4 (184405311681986560) is Monk, Xinverse
        (346426113285753875) is Slayer, Tester 7 (460105234748801024) is Librarian, Tester 2 (270904126974590976)
        is Investigator]
        OUTSIDER :: [Penguin (606332710911156778) is Saint, Temporary Bot (609674334247771236) is Butler]
        ```
        """

        d = datetime.datetime.now()
        timezone = pytz.timezone(TIMEZONE)
        d_aware = timezone.localize(d)

        msg = ""

        if not roles_only:
            msg += "Game Start:```asciidoc\n"
            msg += f"BoTC game started at {d_aware.isoformat()}, with {len(self.sitting_order)} players, using the {self.gamemode} edition.\n"
            msg += "--------------------\n"

        msg += f"DEMON :: {str(self.setup.demon)}\n"
        msg += f"MINION :: {str(self.setup.minions)}\n"
        msg += f"TOWNSFOLK :: {str(self.setup.townsfolks)}\n"
        msg += f"OUTSIDER :: {str(self.setup.outsiders)}\n"

        if not roles_only:
            msg += "```"

        return msg

    async def send_game_obj_log_str(self):
        """Log the game object"""
        msg = self.create_game_obj_log_str()
        await botutils.log(botutils.Level.info, msg)


class Game(GameMeta):
    """BoTC Game class"""

    def __init__(self, gamemode = Gamemode.trouble_brewing):

        self.MIN_PLAYERS = 5 if gamemode == Gamemode.trouble_brewing else 7
        self.MAX_PLAYERS = 15

        self._gamemode = gamemode  # default gamemode will always be trouble brewing

        self._member_obj_list = []  # list object - list of discord member objects
        self._player_obj_list = []  # list object - list of player objects
        self._sitting_order = tuple()  # tuple object (for immutability)
        self._chrono = GameChrono()
        self._setup = Setup()
        self.gameloop = master_game_loop
        self.winners = None  # botc.Team object
        self.invalidated = False  # Don't count in win rates due to modkill/frole/player leaving guild
        self._whispers = _GrowingList()

        self.replay = "```asciidoc\n"

        if any(x for x in DEBUG.values()) and not NO_INVALIDATE:
            # Also don't count game in win rates if debug options are used
            # (DISABLE_PINGS, DISABLE_DMS, FORCE_VOTES), unless forced by
            # setting no_invalidate to true.
            self.invalidated = True

        # Temporary day data
        self.chopping_block = None  # ChoppingBlock object
        self.today_executed_player = None  # Player object
        self.day_start_time = None  # datetime()
        self.nomination_iteration_date = tuple()  # tuple(datetime() for start time, duration in secs)

        # Temporary night data
        self.night_deaths = []  # List of player objects
        self.night_revives = [] # List of player objects
        self.night_start_time = None  # datetime()

        # Temporary dawn data
        self.dawn_start_time = None  # datetime()

        # Is the game doing something without the gameloop being active?
        self.working = False

    @property
    def nb_players(self):
        return len(self._player_obj_list)

    @property
    def gamemode(self):
        return self._gamemode

    @property
    def member_obj_list(self):
        return self._member_obj_list

    @property
    def player_obj_list(self):
        return self._player_obj_list

    @property
    def sitting_order(self):
        return self._sitting_order

    @property
    def current_phase(self):
        return self._chrono.phase

    @property
    def current_cycle(self):
        return self._chrono.cycle

    @property
    def setup(self):
        return self._setup

    @property
    def whispers(self):
        return self._whispers

    def is_idle(self):
        return self.current_phase == Phase.idle

    def is_day(self):
        return self.current_phase == Phase.day

    def is_dawn(self):
        return self.current_phase == Phase.dawn

    def is_night(self):
        return self.current_phase == Phase.night

    def init_temporary_day_data(self):
        """Initialize temporary day data. To be called at the start of the day"""
        # Temporary day data
        self.chopping_block = None  # ChoppingBlock object
        self.today_executed_player = None  # Player object
        self.day_start_time = None  # datetime()
        self.nomination_iteration_date = tuple()  # tuple(datetime() for start time, duration in secs)

    def init_temporary_night_data(self):
        """Initialize temporary night data. To be called at the start of the night"""
        # Temporary night data
        self.night_deaths = []  # List of player objects
        self.night_revives = [] # List of player objects
        self.night_start_time = None  # datetime()

    def init_temporary_dawn_data(self):
        """Initialize temporary dawn data. To be called at the start of the dawn"""
        # Temporary dawn data
        self.dawn_start_time = None  # datetime()

    def create_sitting_order_stats_string(self):
        """Create a stats board:

        Sitting Order:
        ```css
        Chris (232456937349834784) [DEAD]
        John (233426113285745785) [ALIVE]
        Anna (266015398221479937) [ALIVE]
        Fred (3447492102843678721) [ALIVE]
        ```
        """

        msg = "\n\n**Players**: ```css\n"
        for player in self.sitting_order:
            if player.is_display_alive():
                line = f"{player.user.display_name} ({player.user.id}) [alive]\n"
            elif player.is_display_dead():
                if player.has_vote():
                    line = f"{player.user.display_name} ({player.user.id}) [dead] {botutils.BotEmoji.skull} {botutils.BotEmoji.vote}\n"
                else:
                    line = f"{player.user.display_name} ({player.user.id}) [dead] {botutils.BotEmoji.skull}\n"
            else:
                line = f"{player.user.display_name} ({player.user.id}) [quit] {botutils.BotEmoji.fquit}\n"
            msg += line
        msg += "```"
        return msg

    def register_players(self, id_list):
        """Register the players.
        Must be implemented.
        """

        for user_id in id_list:
            member_obj = botutils.get_member_obj(user_id)
            if member_obj:
                self._member_obj_list.append(member_obj)
            else:
                raise GameError("Member not found, invalid user ID")

    async def send_lobby_welcome_message(self):
        """Send the welcome message in lobby"""

        # Trouble Brewing Edition
        if self.gamemode == Gamemode.trouble_brewing:
            embed = discord.Embed(
               description = tb_lore
            )
            # Using the Saint() object to access some URL's
            embed.set_thumbnail(url = TroubleBrewing()._gm_art_link)
            embed.set_author(name = "𝕿𝖗𝖔𝖚𝖇𝖑𝖊 𝕭𝖗𝖊𝖜𝖎𝖓𝖌 - 𝕭𝖑𝖔𝖔𝖉 𝖔𝖓 𝖙𝖍𝖊 𝕮𝖑𝖔𝖈𝖐𝖙𝖔𝖜𝖊𝖗 (𝕭𝖔𝕿𝕮)",
                             icon_url = Saint()._botc_logo_link)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text = copyrights_str)

            pings = " ".join([player.user.mention for player in self.sitting_order])
            msg = lobby_game_start.format(pings, "𝕿𝖗𝖔𝖚𝖇𝖑𝖊 𝕭𝖗𝖊𝖜𝖎𝖓𝖌", self.nb_players)

            await botutils.send_lobby(msg, embed=embed)

        # Bad Moon Rising edition
        elif self.gamemode == Gamemode.bad_moon_rising:
            embed = discord.Embed(
               description = bmr_lore
            )
            # Using the Saint() object to access some URL's
            embed.set_thumbnail(url = BadMoonRising()._gm_art_link)
            embed.set_author(name = "𝕭𝖆𝖉 𝕸𝖔𝖔𝖓 𝕽𝖎𝖘𝖎𝖓𝖌 - 𝕭𝖑𝖔𝖔𝖉 𝖔𝖓 𝖙𝖍𝖊 𝕮𝖑𝖔𝖈𝖐𝖙𝖔𝖜𝖊𝖗 (𝕭𝖔𝕿𝕮)",
                             icon_url = Saint()._botc_logo_link)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text = copyrights_str)

            pings = " ".join([player.user.mention for player in self.sitting_order])
            msg = lobby_game_start.format(pings, "𝕭𝖆𝖉 𝕸𝖔𝖔𝖓 𝕽𝖎𝖘𝖎𝖓𝖌", self.nb_players)

            await botutils.send_lobby(msg, embed=embed)

        # Sects And Violets edition
        elif self.gamemode == Gamemode.sects_and_violets:
            embed = discord.Embed(
               description = snv_lore
            )
            # Using the Saint() object to access some URL's
            embed.set_thumbnail(url = SectsAndViolets()._gm_art_link)
            embed.set_author(name = "𝕾𝖊𝖈𝖙𝖘 𝖆𝖓𝖉 𝖁𝖎𝖔𝖑𝖊𝖙𝖘 - 𝕭𝖑𝖔𝖔𝖉 𝖔𝖓 𝖙𝖍𝖊 𝕮𝖑𝖔𝖈𝖐𝖙𝖔𝖜𝖊𝖗 (𝕭𝖔𝕿𝕮)",
                             icon_url = Saint()._botc_logo_link)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text = copyrights_str)

            pings = " ".join([player.user.mention for player in self.sitting_order])
            msg = lobby_game_start.format(pings, "𝕾𝖊𝖈𝖙𝖘 𝖆𝖓𝖉 𝖁𝖎𝖔𝖑𝖊𝖙𝖘", self.nb_players)

            await botutils.send_lobby(msg, embed=embed)

    async def send_lobby_closing_message(self, win_con_reason = ""):
        """Send the closing message in lobby"""

        from botc import Team

        gamemode = fancy.bold(self.gamemode.value)

        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            # ----- The good team wins -----
            if self.winners == Team.good:

                if not self.invalidated:
                    c.execute("""
                    INSERT INTO game
                        (ended_at, gamemode, winner)
                    VALUES
                        (DATETIME(), :gamemode, 'good')
                    """, {
                        "gamemode": self.gamemode.value,
                        "players": len(self.sitting_order),
                    })

                    game_id = c.lastrowid

                # Revealing the role list
                role_list_str = ""

                for player in self.sitting_order:
                    # The player is a drunk, we use the special reveal short string
                    if player.role.true_self.name == Drunk().name:
                        if player.has_status_effect(StatusList.red_herring):
                            message = ego_role_reveal_herring
                        else:
                            message = ego_role_reveal

                        short = message.format(
                           botutils.BotEmoji.trophy_animated if player.role.true_self.is_good() else "---",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name,
                           player.role.ego_self.name
                        )

                    # The player is a minion who became imp
                    elif player.old_role is not None:
                        short = changed_role_reveal.format(
                           botutils.BotEmoji.trophy_animated if player.role.true_self.is_good() else "---",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name,
                           player.old_role.true_self.emoji,
                           player.old_role.true_self.name,
                        )

                    # The player is not a drunk, we use the default reveal short string
                    else:
                        if player.has_status_effect(StatusList.red_herring):
                            message = role_reveal_herring
                        else:
                            message = role_reveal

                        short = message.format(
                           botutils.BotEmoji.trophy_animated if player.role.true_self.is_good() else "---",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name
                        )

                    role_list_str += short
                    role_list_str += "\n"

                    if not self.invalidated:
                        role = player.old_role or player.role

                        c.execute("""
                        INSERT INTO game_player
                            (game_id, user_id, alignment, role)
                        VALUES
                            (:game_id, :user_id, :alignment, :role)
                        """, {
                            "game_id": game_id,
                            "user_id": player.user.id,
                            "alignment": "good" if role.true_self.is_good() else "evil",
                            "role": role.true_self.name,
                        })

                conn.commit()

                # The embed
                embed = discord.Embed(
                   title = good_wins,
                   description = role_list_str,
                   color = TOWNSFOLK_CARD_COLOR
                )
                embed.set_author(
                   name = "{} - 𝕭𝖑𝖔𝖔𝖉 𝖔𝖓 𝖙𝖍𝖊 𝕮𝖑𝖔𝖈𝖐𝖙𝖔𝖜𝖊𝖗 (𝕭𝖔𝕿𝕮)".format(gamemode),
                   icon_url = Saint()._botc_logo_link
                )
                embed.set_thumbnail(url = dove)

            # ----- The evil team wins -----
            elif self.winners == Team.evil:
                if not self.invalidated:
                    c.execute("""
                    INSERT INTO game
                        (ended_at, gamemode, winner)
                    VALUES
                        (DATETIME(), :gamemode, 'evil')
                    """, {
                        "gamemode": self.gamemode.value,
                        "players": len(self.sitting_order),
                    })

                    game_id = c.lastrowid

                # Revealing the role list
                role_list_str = ""

                for player in self.sitting_order:
                    # The player is a drunk, we use the special reveal short string
                    if player.role.true_self.name == Drunk().name:
                        if player.has_status_effect(StatusList.red_herring):
                            message = ego_role_reveal_herring
                        else:
                            message = ego_role_reveal

                        short = message.format(
                           botutils.BotEmoji.trophy_animated if player.role.true_self.is_evil() else "---",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name,
                           player.role.ego_self.name
                        )

                    # The player is a minion who became imp
                    elif player.old_role is not None:
                        short = changed_role_reveal.format(
                           botutils.BotEmoji.trophy_animated if player.role.true_self.is_evil() else "---",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name,
                           player.old_role.true_self.emoji,
                           player.old_role.true_self.name,
                        )

                    # The player is not a drunk, we use the default reveal short string
                    else:
                        if player.has_status_effect(StatusList.red_herring):
                            message = role_reveal_herring
                        else:
                            message = role_reveal

                        short = message.format(
                           botutils.BotEmoji.trophy_animated if player.role.true_self.is_evil() else "---",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name
                        )

                    role_list_str += short
                    role_list_str += "\n"

                    if not self.invalidated:
                        role = player.old_role or player.role

                        c.execute("""
                        INSERT INTO game_player
                            (game_id, user_id, alignment, role)
                        VALUES
                            (:game_id, :user_id, :alignment, :role)
                        """, {
                            "game_id": game_id,
                            "user_id": player.user.id,
                            "alignment": "good" if role.true_self.is_good() else "evil",
                            "role": role.true_self.name,
                        })

                conn.commit()

                # The embed
                embed = discord.Embed(
                   title = evil_wins,
                   description = role_list_str,
                   color = DEMON_CARD_COLOR
                )
                embed.set_author(
                   name = "{} - 𝕭𝖑𝖔𝖔𝖉 𝖔𝖓 𝖙𝖍𝖊 𝕮𝖑𝖔𝖈𝖐𝖙𝖔𝖜𝖊𝖗 (𝕭𝖔𝕿𝕮)".format(gamemode),
                   icon_url = Saint()._botc_logo_link
                )
                embed.set_thumbnail(url = demon)

            # ----- No one wins -----
            else:
                # Revealing the role list
                role_list_str = ""
                for player in self.sitting_order:

                    # The player is a drunk, we use the special reveal short string
                    if player.role.true_self.name == Drunk().name:
                        if player.has_status_effect(StatusList.red_herring):
                            message = ego_role_reveal_herring
                        else:
                            message = ego_role_reveal

                        short = message.format(
                           "",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name,
                           player.role.ego_self.name
                        )

                    # The player is a minion who became imp
                    elif player.old_role is not None:
                        short = changed_role_reveal.format(
                           "",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name,
                           player.old_role.true_self.emoji,
                           player.old_role.true_self.name,
                        )

                    # The player is not a drunk, we use the default reveal short string
                    else:
                        if player.has_status_effect(StatusList.red_herring):
                            message = role_reveal_herring
                        else:
                            message = role_reveal

                        short = message.format(
                           "",
                           player.user.mention,
                           player.role.true_self.emoji,
                           player.role.true_self.name
                        )

                    role_list_str += short
                    role_list_str += "\n"

                # The embed
                embed = discord.Embed(
                   title = no_one_wins,
                   description = role_list_str
                )
                embed.set_author(
                   name = "{} - 𝕭𝖑𝖔𝖔𝖉 𝖔𝖓 𝖙𝖍𝖊 𝕮𝖑𝖔𝖈𝖐𝖙𝖔𝖜𝖊𝖗 (𝕭𝖔𝕿𝕮)".format(gamemode),
                   icon_url = Saint()._botc_logo_link
                )

            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text = copyrights_str)

            pings = " ".join([player.user.mention for player in self.sitting_order])
            msg = lobby_game_closing.format(pings, gamemode, self.nb_players)

            await botutils.send_lobby(msg, embed=embed)

    async def start_game(self):
        """Start the game.
        Must be implemented.
        """
        self.working = True
        botutils.tasks.update_status = True
        # If game is still starting after 60s, something went wrong
        asyncio.create_task(self.clear_working(60))
        # Ensure all players have alive role
        await botutils.add_all_alive_role()
        # Cancel the timer
        if botutils.start_votes_timer.is_running():
            botutils.start_votes_timer.cancel()
        # Register the players in game
        self.register_players(globvars.master_state.pregame)
        # Generate the setup (role list)
        setup = self.generate_role_set()
        # Give each player a role
        self.distribute_roles(setup, self.member_obj_list)
        # Freeze the sitting
        self.generate_frozen_sitting()
        # Initialize the setup object
        self.setup.clear()
        self.setup.create(self.player_obj_list, self.gamemode, self)
        # Send the lobby welcome message
        await self.send_lobby_welcome_message()
        # Lock the lobby channel
        await botutils.lock_lobby()
        # Initialize each role to set flags as needed, etc.
        for player in self._player_obj_list:
            player.role.exec_init_role(self.setup)
        # Send the opening dm to all players
        for player in self._player_obj_list:
            await player.role.ego_self.send_opening_dm_embed(player.user)
        # Include the starting information for the replay
        d = datetime.datetime.now()
        timezone = pytz.timezone(TIMEZONE)
        d_formatted = timezone.localize(d).strftime("%b %d, %Y | %I:%M:%S %p %Z")
        self.replay += f"Start: {d_formatted}\n"\
                        f"[BoTC: {self.gamemode.value}, {len(self.sitting_order)} players]\n"
        self.replay += GameLog(self).create_game_obj_log_str(roles_only=True)
        # Create the public notes
        self._notes = Notes(self.sitting_order)
        self._note_manager = NotesManager(self._notes, [p.notes for p in self.sitting_order])
        # Log the game data
        await GameLog(self).send_game_obj_log_str()
        # Unload conflicting commands
        for extension in CONFLICTING_CMDS:
            globvars.client.unload_extension(extension)
        # Load game related commands
        if self.gamemode == Gamemode.trouble_brewing:
            globvars.client.load_extension("botc.commands.abilities.tb")
        elif self.gamemode == Gamemode.bad_moon_rising:
            globvars.client.load_extension("botc.commands.abilities.bmr")
        elif self.gamemode == Gamemode.sects_and_violets:
            globvars.client.load_extension("botc.commands.abilities.snv")

        globvars.client.load_extension("botc.commands.townhall")
        globvars.client.load_extension("botc.commands.debug")
        globvars.client.load_extension("botc.commands.info")
        # Start the game loop
        self.gameloop.start(self)

        import botc.gamemodes.badmoonrising._utils as _utils

        _utils.player_gossips = {}
        
        self.working = False

    async def compute_dawn_ability_interactions(self):
        """Order of Action
        1. Ravenkeeper
        """

        await self.remove_left_guild_players()

        if self.gamemode == Gamemode.trouble_brewing:

            from botc.gamemodes.troublebrewing._utils import TBRole

            order = [

               TBRole.ravenkeeper

            ]

        elif self.gamemode == Gamemode.bad_moon_rising:
            
            from botc.gamemodes.badmoonrising._utils import BMRRole

            order = [

                BMRRole.goon,
                BMRRole.moonchild,
                BMRRole.tinker

            ]

        elif self.gamemode == Gamemode.sects_and_violets:

            from botc.gamemodes.sectsandviolets._utils import SnVRole

            order = [

            ]

        else: 
            raise GameError("Gamemode is not one of available BoTC editions.")


        for character_enum in order:
            list_of_characters = BOTCUtils.get_players_from_role_name(character_enum)
            for character in list_of_characters:
                
                if character.has_status_effect(StatusList.no_ability):
                    continue

                from botc import Character

                action = character.action_grid.retrieve_an_action(self._chrono.phase_id)
                if action:
                    for target in action.target_player:
                        if isinstance(target, Player):
                            await target.role.true_self.on_being_targeted(target, action)
                        elif isinstance(target, Character):
                            target_players = BOTCUtils.get_players_from_role_name(target._role_enum)
                            for player in target_players:
                                await player.role.true_self.on_being_targeted(player, action)
                        elif isinstance(target, tuple):
                            # Gambler
                            await target[0].role.true_self.on_being_targeted(target[0], action)

                await character.role.ego_self.process_dawn_ability(character)

    async def compute_night_ability_interactions(self):
        """
        Prompt all players to complete their night actions, according to night order for the selected gamemode
        """

        await self.remove_left_guild_players()

        if self.gamemode == Gamemode.trouble_brewing:
            """Order of Action (First Night)
            1. poisoner
            2. washerwoman
            3. librarian
            4. investigator
            5. chef
            6. empath
            7. fortune teller
            8. butler
            9. spy

            Order of Action (All Other Nights)
            1. poisoner
            2. monk
            3. scarlet woman
            4. imp
            5. ravenkeeper
            6. empath
            7. fortune teller
            8. butler
            9. undertaker
            10. spy
            """

            from botc.gamemodes.troublebrewing._utils import TBRole

            night_1_order = [

               TBRole.poisoner,
               TBRole.washerwoman,
               TBRole.librarian,
               TBRole.investigator,
               TBRole.chef,
               TBRole.empath,
               TBRole.fortuneteller,
               TBRole.butler,
               TBRole.spy

            ]

            night_regular_order = [

               TBRole.poisoner,      # Poison
               TBRole.monk,          # Protect
               TBRole.scarletwoman,  # Let her know of any demon promotion
               TBRole.soldier,       # Add the safe from demon status effect if not droisoned
               TBRole.imp,           # Save the kill target
               TBRole.empath,
               TBRole.fortuneteller,
               TBRole.butler,
               TBRole.undertaker,    # Send the executed player's role
               TBRole.spy

            ]

        elif self.gamemode == Gamemode.bad_moon_rising:
            """Order of Action (First Night)
            1. lunatic
            2. sailor
            3. courtier
            4. godfather
            5. devil's advocate
            6. pukka
            7. grandmother
            8. chambermaid

            Order of Action (All Other Nights)
            1. sailor
            2. courtier
            3. innkeeper
            4. gambler
            5. devil's advocate
            6. lunatic
            7. exorcist
            8. zombuul
            9. pukka
            10. shabaloth
            11. po
            12. assassin
            13. godfather
            14. gossip
            15. professor
            16. tinker
            17. moonchild
            18. grandmother
            19. chambermaid
            """

            from botc.gamemodes.badmoonrising._utils import BMRRole

            night_1_order = [
                BMRRole.lunatic,
                BMRRole.sailor,
                BMRRole.courtier,
                BMRRole.godfather,
                BMRRole.devilsadvocate,
                BMRRole.pukka,
                BMRRole.grandmother,
                BMRRole.chambermaid
            ]

            night_regular_order = [
                BMRRole.minstrel,
                BMRRole.sailor,
                BMRRole.courtier,
                BMRRole.innkeeper,
                BMRRole.gambler,
                BMRRole.devilsadvocate,
                BMRRole.lunatic,
                BMRRole.exorcist,
                BMRRole.zombuul,
                BMRRole.pukka,
                BMRRole.shabaloth,
                BMRRole.po,
                BMRRole.assassin,
                BMRRole.godfather,
                BMRRole.gossip,
                BMRRole.professor,
                BMRRole.tinker,
                BMRRole.moonchild,
                BMRRole.grandmother,
                BMRRole.chambermaid
            ]

        elif self.gamemode == Gamemode.sects_and_violets:
            """Order of Action (First Night)
            1. philosopher
            2. snake charmer
            3. evil twin
            4. witch
            5. cerenovus
            6. clockmaker
            7. dreamer
            8. seamstress
            9. mathematician

            Order of Action (All Other Nights)
            1. philosopher
            2. snake charmer
            3. witch
            4. cerenovus
            5. pit-hag
            6. fang gu
            7. no dashii
            8. vortox
            9. vigormortis
            10. barber
            11. sweetheart
            12. sage
            13. dreamer
            14. flowergirl
            15. town crier
            16. oracle
            17. seamstress
            18. juggler
            19. mathematician
            """

            from botc.gamemodes.sectsandviolets._utils import SnVRole

            night_1_order = [
                SnVRole.philosopher,
                SnVRole.snakecharmer,
                SnVRole.eviltwin,
                SnVRole.witch,
                SnVRole.cerenovus,
                SnVRole.clockmaker,
                SnVRole.dreamer,
                SnVRole.seamstress,
                SnVRole.mathematician
            ]

            night_regular_order = [
                SnVRole.philosopher,
                SnVRole.snakecharmer,
                SnVRole.witch,
                SnVRole.cerenovus,
                SnVRole.pithag,
                SnVRole.fanggu,
                SnVRole.nodashii,
                SnVRole.vortox,
                SnVRole.vigormortis,
                SnVRole.barber,
                SnVRole.sweetheart,
                SnVRole.sage,
                SnVRole.dreamer,
                SnVRole.flowergirl,
                SnVRole.towncrier,
                SnVRole.oracle,
                SnVRole.seamstress,
                SnVRole.juggler,
                SnVRole.mathematician
            ]

        else:
            raise GameError("Gamemode is not one of available BoTC editions.")

        from .Character import Character

        # Night 1 order
        if self._chrono.is_night_1():
            for character_enum in night_1_order:
                list_of_characters = BOTCUtils.get_players_from_role_name(character_enum)
                for character in list_of_characters:

                    if character.has_status_effect(StatusList.no_ability):
                        continue

                    action = character.action_grid.retrieve_an_action(self._chrono.phase_id)
                    if action:
                        for target in action.target_player:
                            if isinstance(target, Player):
                                await target.role.true_self.on_being_targeted(target, action)
                            elif isinstance(target, Character):
                                target_players = BOTCUtils.get_players_from_role_name(target._role_enum)
                                for player in target_players:
                                    await player.role.true_self.on_being_targeted(player, action)
                            elif isinstance(target, tuple):
                                # Gambler
                                await target[0].role.true_self.on_being_targeted(target[0], action)


                    await character.role.ego_self.process_night_ability(character)

        # Regular night order
        else:
            for character_enum in night_regular_order:
                list_of_characters = BOTCUtils.get_players_from_role_name(character_enum)
                for character in list_of_characters:

                    if character.has_status_effect(StatusList.no_ability):
                        continue

                    action = character.action_grid.retrieve_an_action(self._chrono.phase_id)
                    if action:
                        for target in action.target_player:
                            if isinstance(target, Player):
                                await target.role.true_self.on_being_targeted(target, action)
                            elif isinstance(target, Character):
                                target_players = BOTCUtils.get_players_from_role_name(target._role_enum)
                                for player in target_players:
                                    await player.role.true_self.on_being_targeted(player, action)
                            elif isinstance(target, tuple):
                                # Gambler
                                await target[0].role.true_self.on_being_targeted(target[0], action)

                    await character.role.ego_self.process_night_ability(character)

    def has_received_all_expected_dawn_actions(self):
        """Check if all players with expected dawn actions have submitted them"""
        for player in self.sitting_order:
            if not player.role.ego_self.has_finished_dawn_action(player):
                return False
        return True

    def has_received_all_expected_night_actions(self):
        """Check if all players with expected night actions have submitted them"""
        for player in self.sitting_order:
            if not player.role.ego_self.has_finished_night_action(player):
                return False
        return True

    @property
    def nb_alive_players(self):
        """Return the number of alive players (apparently alive state)"""
        count = 0
        for player in self.sitting_order:
            if player.is_apparently_alive():
                count += 1
        return count

    @property
    def nb_truly_alive_players(self):
        """Return the number of alive players"""
        count = 0
        for player in self.sitting_order:
            if player.isalive():
                count += 1
        return count

    @property
    def list_alive_players(self):
        """Return the list of alive players (truly alive state)"""
        return [player for player in self.sitting_order if player.is_alive()]

    @property
    def notes(self):
        return self._notes

    @property
    def note_manager(self):
        return self._note_manager

    async def check_winning_conditions(self):
        """Check if the game has reached the winning conditons. Promote new demons or
        end the game is necessary.
        """

        responses = list()
        for player in self._player_obj_list:
            responses.append(player.role.true_self.check_winning_conditions(player))

        if False in responses:
            return

        # Less than or equal to 2 alive players. Winning condition is definitely triggered.
        if self.nb_truly_alive_players <= 2:

            # There are still alive demons. The game is over with Evil win.
            if BOTCUtils.has_alive_demons():
                self.winners = Team.evil
                self.gameloop.cancel()

            # There is no alive demon. The game is over with Good win.
            else:
                self.winners = Team.good
                self.gameloop.cancel()

        # More than 2 players still alive.
        else:

            # There are still alive demons.
            if BOTCUtils.has_alive_demons():
                # There is at least one alive good player. The game continues.
                alives = self.list_alive_players
                for player in alives:
                    if player.role.true_self.is_good():
                        return
                # The remaining players are all evil. The demon can't be nominated, and evil wins.
                else:
                    self.winners = Team.evil
                    self.gameloop.cancel()

            # There is no alive demon. The game is over with Good win.
            else:
                self.winners = Team.good
                self.gameloop.cancel()

    async def end_game(self):
        """End the game, compute winners etc.
        Must be implemented.
        """
        self.working = True
        # If game is still ending after 60s, something went wrong
        asyncio.create_task(self.clear_working(60))
        # Include the ending information for the replay and send it
        winning_team = "No one"
        if self.winners == Team.good:
            winning_team = "Good"
        elif self.winners == Team.evil:
            winning_team = "Evil"
        d = datetime.datetime.now()
        timezone = pytz.timezone(TIMEZONE)
        d_formatted = timezone.localize(d).strftime("%b %d, %Y | %I:%M:%S %p %Z")
        self.replay += f"[{winning_team} wins]\nEnd: {d_formatted}\n```"
        await botutils.send_replay(self.replay)
        # Send the lobby game conclusion message
        await self.send_lobby_closing_message()
        # Unload extensions
        if self.gamemode == Gamemode.trouble_brewing:
            globvars.client.unload_extension("botc.commands.abilities.tb")
        elif self.gamemode == Gamemode.bad_moon_rising:
            globvars.client.unload_extension("botc.commands.abilities.bmr")
        elif self.gamemode == Gamemode.sects_and_violets:
            globvars.client.unload_extension("botc.commands.abilities.snv")

        globvars.client.unload_extension("botc.commands.townhall")
        globvars.client.unload_extension("botc.commands.debug")
        globvars.client.unload_extension("botc.commands.info")
        # Load conflicting commands
        for extension in CONFLICTING_CMDS:
            globvars.client.load_extension(extension)
        # Log the game
        await botutils.log(botutils.Level.info, "Game finished")
        # Stop various loops from running
        from botc.gameloops import base_day_loop, nomination_loop

        # Stop the nomination loop if it is running
        if nomination_loop.is_running():
            nomination_loop.cancel()
        # Stop the base day loop if it is running
        if base_day_loop.is_running():
            base_day_loop.cancel()
        # Stop the debate timer loop if it is running
        if debate_timer.is_running():
            debate_timer.cancel()
        # Unlock the lobby channel
        await botutils.unlock_lobby()
        # Remove roles
        await botutils.remove_all_alive_dead_roles_after_game()
        # Clear the game object
        self.__init__(self._gamemode)
        globvars.master_state.game = None
        # Update the global state
        botutils.update_state_machine()
        botutils.tasks.update_status = True

        self.working = False

    async def make_nightfall(self):
        """Transition the game into night phase"""

        # Initialize the temporary night data set
        self.init_temporary_night_data()

        # Store the starting time
        self.night_start_time = datetime.datetime.now()

        # Initialize the master switches at the start of a phase
        import botc.switches
        botc.switches.init_switches()

        # Stop all tasks of the day phase
        if nomination_loop.is_running():
            nomination_loop.cancel()
        if base_day_loop.is_running():
            base_day_loop.cancel()
        if debate_timer.is_running():
            debate_timer.cancel()

        # Move the chrono forward by one phase
        self._chrono.next()

        # Prepare the phase announcement message
        embed = discord.Embed(
           description = botutils.BotEmoji.moon + " " + nightfall,
           color = NIGHT_CARD_COLOR
        )
        embed.set_footer(text = copyrights_str)
        embed.set_image(url = nightfall_image)
        embed.timestamp = datetime.datetime.utcnow()
        await botutils.send_lobby(message = "", embed = embed)

        # Reset the nomination data for the previous day phase
        for player in self.sitting_order:
            player.reset_nomination()

    async def make_dawn(self):
        """Transition the game into dawn/interlude phase"""

        # Initalize the temporary dawn data
        self.init_temporary_dawn_data()

        # Store the starting time
        self.dawn_start_time = datetime.datetime.now()

        # Move the chrono forward by one phase
        self._chrono.next()

        # Prepare the phase announcement message
        embed = discord.Embed(
           description = botutils.BotEmoji.sunrise + " " + dawn,
           color = DAWN_CARD_COLOR
        )
        embed.set_footer(text = copyrights_str)
        embed.set_image(url = dawn_image)
        embed.timestamp = datetime.datetime.utcnow()
        await botutils.send_lobby(message = "", embed = embed)

        # Initialize the master switches at the start of a phase
        import botc.switches
        if botc.switches.master_proceed_to_day:
            return
        botc.switches.init_switches()

    async def make_daybreak(self):
        """Transition the game into day phase"""

        # Initialize the temporary day data set
        self.init_temporary_day_data()

        for player in self.sitting_order:
            player.clear_reminder_tokens()

        # Store the starting time
        self.day_start_time = datetime.datetime.now()

        # Initialize the master switches at the start of a phase
        import botc.switches
        botc.switches.init_switches()

        # Move the chrono forward by one phase
        self._chrono.next()

        # Prepare the phase announcement message
        # Night 1 end is Storyteller death
        if self._chrono.cycle == 1 and self._chrono.phase == Phase.day:
            final_death_message = storyteller_death

        # Not night 1 end, we look at the death list
        else:

            night_deaths = list(set(self.night_deaths))
            night_deaths = filter(lambda player: player.is_apparently_dead(), night_deaths)
            night_deaths_names = [p.game_nametag for p in night_deaths]
            if len(night_deaths_names) == 1:
                night_deaths_string = night_deaths_names[0]
            elif len(night_deaths_names) != 0:
                night_deaths_string = ", ".join(night_deaths_names[:-1]) + ", and " + night_deaths_names[-1]

            night_revives = list(set(self.night_revives))
            night_revives = filter(lambda player: player.is_apparently_alive(), night_revives)
            night_revives_names = [p.game_nametag for p in night_revives]
            if len(night_revives_names) == 1:
                night_revives_string = night_revives_names[0]
            elif len(night_revives_names) != 0:
                night_revives_string = ", ".join(night_revives_names[:-1]) + ", and " + night_revives_names[-1]

            # Deaths Revives Message
            # 0      0       zero
            # 1      0       singular
            # 2+     0       plural
            # 0      1       no_death_single_revive
            # 1      1       one_death_single_revive
            # 2+     1       multiple_death_single_revive
            # 0      2+      no_death_multiple_revive
            # 1      2+      one_death_multiple_revive
            # 2+     2+      multiple_death_multiple_revive

            for player in self.night_deaths:
                await botutils.add_dead_role(player.user)
                await botutils.remove_alive_role(player.user)

            for player in self.night_revives:
                await botutils.add_alive_role(player.user)
                await botutils.remove_dead_role(player.user)

            night_deaths_names = [player.game_nametag for player in self.night_deaths]
            night_deaths_names = list(set(night_deaths_names))

            if len(night_deaths_names) == 0 and len(night_revives_names) == 0:
                death_messages = game_text["lore"]["night_death"]["zero"]["outputs"]
                death_weights = game_text["lore"]["night_death"]["zero"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
            elif len(night_deaths_names) == 1 and len(night_revives_names) == 0:
                death_messages = game_text["lore"]["night_death"]["singular"]["outputs"]
                death_weights = game_text["lore"]["night_death"]["singular"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.murder,
                    night_deaths_string
                )
            elif len(night_revives_names) == 0:
                death_messages = game_text["lore"]["night_death"]["plural"]["outputs"]
                death_weights = game_text["lore"]["night_death"]["plural"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.murder,
                    night_deaths_string
                )
            elif len(night_deaths_names) == 0 and len(night_revives_names) == 1:
                death_messages = game_text["lore"]["night_death"]["no_death_single_revive"]["outputs"]
                death_weights = game_text["lore"]["night_death"]["no_death_single_revive"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.revive,
                    night_revives_string
                )
            elif len(night_deaths_names) == 1 and len(night_revives_names) == 1:
                death_messages = game_text["lore"]["night_death"]["one_death_single_revive"]["outputs"]
                death_weights = game_text["lore"]["night_death"]["one_death_single_revive"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.murder,
                    night_deaths_names[0],
                    botutils.BotEmoji.revive,
                    night_revives_string
                )
            elif len(night_revives_names) == 1:
                death_messages = game_text["lore"]["night_death"]["multiple_death_single_revive"]["outputs"]
                death_weights = game_text["lore"]["night_death"]["multiple_death_single_revive"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.murder,
                    night_deaths_string,
                    botutils.BotEmoji.revive,
                    night_revives_string
                )
            elif len(night_deaths_names) == 0:
                death_messages = game_text["lore"]["no_death_multiple_revive"]["plural"]["outputs"]
                death_weights = game_text["lore"]["no_death_multiple_revive"]["plural"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.revive,
                    night_revives_string
                )
            elif len(night_deaths_names) == 1:
                death_messages = game_text["lore"]["one_death_multiple_revive"]["plural"]["outputs"]
                death_weights = game_text["lore"]["one_death_multiple_revive"]["plural"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.murder,
                    night_deaths_names[0],
                    botutils.BotEmoji.revive,
                    night_revives_string
                )
            else:
                death_messages = game_text["lore"]["multiple_death_multiple_revive"]["plural"]["outputs"]
                death_weights = game_text["lore"]["multiple_death_multiple_revive"]["plural"]["weights"]
                death_msg = random.choices(
                      death_messages,
                      weights = death_weights
                )
                final_death_message = death_msg[0]
                final_death_message = final_death_message.format(
                    botutils.BotEmoji.murder,
                    night_deaths_string,
                    botutils.BotEmoji.revive,
                    night_revives_string
                )

            # Clear night and day deaths so that stats string is correct
            self.night_deaths.clear()
            self.night_revives.clear()

        embed = discord.Embed(
           description = botutils.BotEmoji.sun + " " + daybreak + " " + final_death_message,
           color = DAY_CARD_COLOR
        )
        embed.set_footer(text = copyrights_str)
        embed.set_image(url = daybreak_image)
        embed.timestamp = datetime.datetime.utcnow()

        await botutils.send_lobby(message = "", embed = embed)

    def generate_role_set(self):
        """Generate a list of roles according to the number of players"""

        num_player = len(self._member_obj_list)

        # Incorrect number of players
        if num_player > self.MAX_PLAYERS:
            raise TooManyPlayers("Must be 15 players or less.")

        elif num_player < self.MIN_PLAYERS:
            raise TooFewPlayers("Must be 5 players or more.")

        # Correct number of players
        else:
            role_guide = RoleGuide(num_player)
            nb_townsfolk = role_guide.nb_townsfolks
            nb_outsider = role_guide.nb_outsiders
            nb_minion = role_guide.nb_minions
            nb_demon = role_guide.nb_demons

            # Trouble brewing mode
            if self.gamemode == Gamemode.trouble_brewing:
                selected_gamemode = TroubleBrewing

            # Bad moon rising mode
            elif self.gamemode == Gamemode.bad_moon_rising:
                selected_gamemode = BadMoonRising

            # Sects and violets mode
            elif self.gamemode == Gamemode.sects_and_violets:
                selected_gamemode = SectsAndViolets

            else:
                raise GameError("Gamemode is not one of available BoTC editions.")

            townsfolk_all = BOTCUtils.get_role_list(selected_gamemode, Townsfolk)
            outsider_all = BOTCUtils.get_role_list(selected_gamemode, Outsider)
            minion_all = BOTCUtils.get_role_list(selected_gamemode, Minion)
            demon_all = BOTCUtils.get_role_list(selected_gamemode, Demon)

            ret_townsfolk = random.sample(townsfolk_all, nb_townsfolk)
            ret_outsider = random.sample(outsider_all, nb_outsider)
            ret_minion = random.sample(minion_all, nb_minion)
            ret_demon = random.sample(demon_all, nb_demon)

            final_townsfolk = ret_townsfolk.copy()
            final_outsider = ret_outsider.copy()
            final_minion = ret_minion.copy()
            final_demon = ret_demon.copy()

            prelim = ret_townsfolk + ret_outsider + ret_minion + ret_demon
            for role in prelim:
                setup_next = role.exec_init_setup(final_townsfolk, final_outsider, final_minion, final_demon)
                final_townsfolk = setup_next[0]
                final_outsider = setup_next[1]
                final_minion = setup_next[2]
                final_demon = setup_next[3]

            setup = final_townsfolk + final_outsider + final_minion + final_demon
            random.shuffle(setup)

            return setup

    def distribute_roles(self, role_obj_list, member_obj_list):
        """Distribute the roles to the players"""

        if len(role_obj_list) != len(member_obj_list):
            raise GameError("Number of players not matching number of roles generated")

        else:
            ret = []
            for member in member_obj_list:
                role_obj = role_obj_list.pop()
                player_obj = Player(member, role_obj)
                ret.append(player_obj)

        self._player_obj_list = ret

    def generate_frozen_sitting(self):
        """Freeze the sittings of the table around the game table"""

        random.shuffle(self.player_obj_list)
        self._sitting_order = tuple(self._player_obj_list)
        globvars.logging.info(f"Sitting Order {str(self._sitting_order)}")

    def __repr__(self):
        return f"Blood on the Clocktower played using the {fancy.bold(self.gamemode.value)} edition"

    async def remove_left_guild_players(self):
        for member in self.member_obj_list:
            fetched_member = globvars.client.get_guild(SERVER_ID).get_member(int(member.id))
            if fetched_member == None: #player left guild
                self.invalidated = True
                for player in self._player_obj_list:
                    if player.user == member: #discord.py implements equality check between users and members

                        #We can't call player.exec_real_death() because we would then try to give a role to a nonexistent player
                        player.ghost_vote = 0
                        player._state_obj = PlayerState.dead
                        player._apparent_state_obj = PlayerState.dead

                        break
        await self.check_winning_conditions()

    def register_whisper(self, whisper):
        self._whispers.append(whisper)
        
    async def clear_working(self, seconds):
        await asyncio.sleep(seconds)
        self.working = False
