"""Contains the Recurring Action class"""

import datetime

import discord
import toml

import botutils
from botc import BOTCUtils, game_text

from config import DISABLE_DMS

butterfly = botutils.BotEmoji.butterfly

copyrights_str = game_text["misc"]["copyrights"]


# ------- For Night -------

class RecurringAction:
    """A class to faciliate the characters who have recurring night actions"""

    @property
    def name(self):
        raise NotImplementedError

    @property
    def emoji(self):
        raise NotImplementedError

    @property
    def instruction(self):
        raise NotImplementedError

    @property
    def action(self):
        raise NotImplementedError

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""

        if DISABLE_DMS:
            return

        import globvars

        player = BOTCUtils.get_player_from_id(recipient.id)

        if player.is_alive():

            # Construct the message to send
            msg = f"***{recipient.name}#{recipient.discriminator}***, the **{self.name}**:"
            msg += "\n"
            msg += self.emoji + " " + self.instruction
            msg += "\n"

            embed = discord.Embed(description = msg)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text = copyrights_str)

            msg2 = self.action
            msg2 += globvars.master_state.game.create_sitting_order_stats_string()
            embed.add_field(name = butterfly + " **「 Your Action 」**", value = msg2, inline = False)

            try:
                await recipient.send(embed = embed)
            except discord.Forbidden:
                pass


class NonRecurringAction:
    """A class to faciliate the characters who don't have recurring night actions"""

    async def send_regular_night_start_dm(self, recipient):
        """Send the query for night action for each regular night (not the first one)"""
        pass
