"""Contains the on_ready event listener"""

import csv
import json
import os
import sqlite3

import toml
from discord.ext import commands

import botutils

with open("config.toml") as fd:
    config = toml.load(fd)

    SERVER_ID = config["ids"]["server_id"]
    LOBBY_CHANNEL_ID = config["ids"]["lobby_channel_id"]
    ALIVE_ROLE_ID = config["ids"]["alive_role_id"]
    DEAD_ROLE_ID = config["ids"]["dead_role_id"]

with open("botutils/bot_text.json") as json_file:
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
            c.execute("""
            CREATE TABLE IF NOT EXISTS player_map (
                primary_user_id INTEGER NOT NULL,
                secondary_user_id INTEGER PRIMARY KEY NOT NULL
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS ignore (
                user_id INTEGER PRIMARY KEY NOT NULL
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS notify (
                user_id INTEGER PRIMARY KEY NOT NULL
            )
            """)
            c.execute("PRAGMA user_version = 5")

            # Migrate old ignore data
            try:
                with open("ignore.csv") as ignore_file:
                    csv_reader = csv.reader(ignore_file, delimiter = ',')
                    for row in csv_reader:
                        for item in row:
                            c.execute("INSERT OR IGNORE INTO ignore (user_id) VALUES (:user_id)", {"user_id": int(item)})
                        break
            except FileNotFoundError:
                pass
            else:
                os.unlink("ignore.csv")

            # Migrate old notify data
            try:
                with open("notify.csv") as notify_file:
                    csv_reader = csv.reader(notify_file, delimiter = ',')
                    for row in csv_reader:
                        for item in row:
                            c.execute("INSERT OR IGNORE INTO notify (user_id) VALUES (:user_id)", {"user_id": int(item)})
                        break
            except FileNotFoundError:
                pass
            else:
                os.unlink("notify.csv")

        # Print the login message in console
        print(f"Logged in as {self.client.user.name}")
        print(f"Bot ID {self.client.user.id}")
        print("----------")

        # Start cycling playing message
        botutils.cycling_bot_status.start()

        # Send the message in log
        await botutils.log(botutils.Level.info, restart_msg)

        pings = []

        alive_role = globvars.client.get_guild(SERVER_ID).get_role(ALIVE_ROLE_ID)
        dead_role = globvars.client.get_guild(SERVER_ID).get_role(DEAD_ROLE_ID)

        num_alive = len(alive_role.members)
        num_dead = len(dead_role.members)

        if num_alive:
            pings.append(botutils.make_role_ping(ALIVE_ROLE_ID))
        if num_dead:
            pings.append(botutils.make_role_ping(DEAD_ROLE_ID))
        if pings:
            lobby_channel = globvars.client.get_channel(LOBBY_CHANNEL_ID)
            await lobby_channel.send(restarted_notify_msg.format(" ".join(pings)))

        for player in alive_role.members:
            await botutils.remove_alive_role(player)
        for player in dead_role.members:
            await botutils.remove_dead_role(player)

        await botutils.unlock_lobby()


def setup(client):
    client.add_cog(on_ready(client))
