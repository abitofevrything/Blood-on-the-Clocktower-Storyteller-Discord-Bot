"""Contains the on_ready event listener"""

import configparser
import csv
import json
import sqlite3

from discord.ext import commands

import botutils

Config = configparser.ConfigParser()
Config.read("config.INI")

SERVER_ID = Config["user"]["SERVER_ID"]
LOBBY_CHANNEL_ID = Config["user"]["LOBBY_CHANNEL_ID"]
ALIVE_ROLE_ID = Config["user"]["ALIVE_ROLE_ID"]
DEAD_ROLE_ID = Config["user"]["DEAD_ROLE_ID"]
LOCK_CHANNELS_SPECIAL_ID = json.loads(Config["user"].get("LOCK_CHANNELS_SPECIAL_ID", "[]"))

with open('botutils/bot_text.json') as json_file:
    language = json.load(json_file)

restart_msg = language["system"]["restart"]
restarted_notify_msg = language["system"]["restarted_notify"]


class on_ready(commands.Cog):
    """Event listener on_ready"""

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """On_ready event"""

        import globvars

        # Import the ignore data from csv file
        globvars.ignore_list.clear()

        with open('ignore.csv', mode = 'r') as ignore_file:
            csv_reader = csv.reader(ignore_file, delimiter = ',')
            for row in csv_reader:
                globvars.ignore_list = [int(item) for item in row]
                break

        # Import the notify data from csv file
        globvars.notify_list.clear()

        with open('notify.csv', mode = 'r') as notify_file:
            csv_reader = csv.reader(notify_file, delimiter = ',')
            for row in csv_reader:
                globvars.notify_list = [int(item) for item in row]
                break

        with sqlite3.connect("data.sqlite3") as conn:
            c = conn.cursor()

            c.execute("""
            CREATE TABLE IF NOT EXISTS game (
                game_id INTEGER PRIMARY KEY NOT NULL,
                ended_at DATETIME NOT NULL,
                gamemode TEXT NOT NULL,
                winner TEXT NOT NULL
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS game_player (
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                alignment TEXT NOT NULL,
                role TEXT NOT NULL,
                PRIMARY KEY (game_id, user_id),
                FOREIGN KEY (game_id) REFERENCES game (game_id)
            )
            """)
            c.execute("PRAGMA user_version = 3")

        # Start the backup loop
        botutils.backup_loop.start()

        # Print the login message in console
        print(f"Logged in as {self.client.user.name}")
        print(f"Bot ID {self.client.user.id}")
        print("----------")

        # Start cycling playing message
        botutils.cycling_bot_status.start()

        # Send the message in log
        await botutils.log(botutils.Level.info, restart_msg)

        pings = []

        alive_role = globvars.client.get_guild(int(SERVER_ID)).get_role(int(ALIVE_ROLE_ID))
        dead_role = globvars.client.get_guild(int(SERVER_ID)).get_role(int(DEAD_ROLE_ID))

        num_alive = len(alive_role.members)
        num_dead = len(dead_role.members)

        if num_alive:
            pings.append(botutils.make_role_ping(ALIVE_ROLE_ID))
        if num_dead:
            pings.append(botutils.make_role_ping(DEAD_ROLE_ID))
        if pings:
            lobby_channel = globvars.client.get_channel(int(LOBBY_CHANNEL_ID))
            await lobby_channel.send(restarted_notify_msg.format(" ".join(pings)))

        for player in alive_role.members:
            await botutils.remove_alive_role(player)
        for player in dead_role.members:
            await botutils.remove_dead_role(player)

        await botutils.unlock_lobby()


def setup(client):
    client.add_cog(on_ready(client))
