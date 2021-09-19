"""Contains the fstart command cog"""

import json

from discord.ext import commands

import botutils
from botutils import BotEmoji, bot_text, get_gamemode_from_str
from library import fancy

from ._admin import Admin

missing_gamemode = bot_text["errors"]["missing_gamemode"]
success = bot_text["cmd"]["fgame_success"]
gm_not_found = bot_text["cmd"]["gm_not_found"]

x_emoji = BotEmoji.x_emoji
check = BotEmoji.check

class FGame(Admin, name = bot_text["system"]["admin_cog"]):
    """Fgame command"""

    @commands.command(
        pass_context = True,
        name = "fgame",
        brief = bot_text["doc"]["fgame"]["brief"],
        help = bot_text["doc"]["fgame"]["help"],
        description = bot_text["doc"]["fgame"]["description"]
    )
    @commands.check(botutils.check_if_lobby_or_dm_or_admin)
    async def fgame(self, ctx, gm: str):
        """Force game command"""

        import globvars

        if gm:
            parsed_gamemode = get_gamemode_from_str(gm)
            if parsed_gamemode:
                globvars.master_state.game_chooser.disable_voting()
                globvars.master_state.game_chooser.select_gamemode(parsed_gamemode, ctx.author.id)
                await ctx.send(success.format(ctx.author.mention, check, fancy.bold(parsed_gamemode.value)))
            else:
                from botc.BOTCUtils import GamemodeNotFound
                raise GamemodeNotFound(gm_not_found.format(ctx.author.mention, x_emoji))
        else:
            from botc.BOTCUtils import GamemodeNotFound
            raise GamemodeNotFound(missing_gamemode.format(ctx.author.mention, x_emoji))

