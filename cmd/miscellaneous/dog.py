"""Contains the dog command cog"""

import json
import random

from discord.ext import commands

import botutils

from ._miscellaneous import Miscellaneous

from botutils import bot_text


class Dog(Miscellaneous, name = bot_text["system"]["miscellaneous_cog"]):
    """Dog command"""

    @commands.command(
        pass_context = True,
        name = "dog",
        brief = bot_text["doc"]["dog"]["brief"],
        help = bot_text["doc"]["dog"]["help"],
        description = bot_text["doc"]["dog"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def dog(self, ctx):
        """Flip a dog."""

        dog_replies = bot_text["doc"]["dog"]["outputs"]
        dog_weights = bot_text["doc"]["dog"]["weights"]
        dog_reply = random.choices(
            dog_replies,
            weights=dog_weights
        )
        dog_reply = dog_reply[0]
        dog_reply = dog_reply.format(botutils.BotEmoji.puppy)

        await ctx.send(dog_reply)
