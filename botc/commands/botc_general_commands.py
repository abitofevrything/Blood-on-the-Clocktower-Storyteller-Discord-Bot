"""Contains cog for general out of game / info related botc commands"""

import json

import discord
import toml
from discord.ext import commands

import botutils
from botc import game_text
from config import NORMAL_CARD_COLOR

copyrights_str = game_text["misc"]["copyrights"]
res_title = game_text["misc"]["res_title"]
res_desc = game_text["misc"]["res_desc"]
thumnail = game_text["misc"]["thumnail"]
wiki = game_text["misc"]["wiki"]
rulebooks = game_text["misc"]["rulebooks"]
scripts = game_text["misc"]["scripts"]
social_medias = game_text["misc"]["social_medias"].format(
    botutils.BotEmoji.facebook, botutils.BotEmoji.youtube, botutils.BotEmoji.twitter, botutils.BotEmoji.reddit
)


class BOTCGeneralCommands(commands.Cog, name="BoTC Commands"):
    """BoTC General commands cog"""

    def __init__(self, client):
        self.client = client

    @commands.group(pass_context = True, name = "botc")
    async def botc(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.resource(ctx)

    @botc.command(
        pass_context = True,
        name = "guide",
        aliases = ["chart", "playerchart", "playerguide"]
    )
    async def guide(self, ctx):
        await ctx.send("https://imgur.com/jD50A9Q")

    @botc.command(
        pass_context = True,
        name = "resource",
        aliases = ["resources", "res"]
    )
    async def resource(self, ctx):
        embed=discord.Embed(title = res_title, description = res_desc, color = NORMAL_CARD_COLOR)
        embed.set_thumbnail(url = thumnail)
        embed.add_field(name = "Wiki", value = wiki, inline = False)
        embed.add_field(name = "Rulebooks", value = rulebooks, inline = False)
        embed.add_field(name = "Scripts", value = scripts, inline = False)
        embed.add_field(name = "Social Medias", value = social_medias, inline = False)
        embed.set_footer(text = copyrights_str)
        await ctx.send(embed = embed)

    @botc.command(
        pass_context = True,
        name = "trouble-brewing",
        aliases = ["tb", "trouble_brewing", "troublebrewing"]
    )
    async def trouble_brewing(self, ctx):
        await ctx.send("https://imgur.com/QJeTKDR")

    @botc.command(
        pass_context = True,
        name = "bad-moon-rising",
        aliases = ["bmr", "bad_moon_rising", "badmoonrising"]
    )
    async def bad_moon_rising(self, ctx):
        await ctx.send("https://imgur.com/Jy3ifCZ")

    @botc.command(
        pass_context = True,
        name = "sects-and-violets",
        aliases = ["sv", "sects_and_violets", "sectsandviolets"]
    )
    async def sects_and_violets(self, ctx):
        await ctx.send("https://imgur.com/ZcryOcA")


def setup(client):
    client.add_cog(BOTCGeneralCommands(client))
