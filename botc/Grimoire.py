"""Contains the Grimoire class"""

from config import GRIMOIRE_SHOW_TIME
import math
import random

from PIL import Image, ImageDraw, ImageFont

from botc.gamemodes import Gamemode


class Grimoire:
    """Grimoire object to show the grimoire representation to the Spy Character"""

    GRIMOIRE_PATH = "botc/assets/grimoire/grimoire.png"
    TB_ICON = "botc/assets/editions/TB_Logo.png"
    BMR_ICON = "botc/assets/editions/BMR_Logo.png"
    SV_ICON = "botc/assets/editions/SV_Logo.png"
    SHROUD = "botc/assets/grimoire/shroud.png"
    FONT = "botc/assets/grimoire/Bitstream_Cyberbit.ttf"

    def create(game_obj):
        # Load image
        backgroud_path = Grimoire.random_background()
        image = Image.open(backgroud_path)
        image.convert('RGBA')

        # Get some dimensions
        image_width = image.size[0]
        image_height = image.size[1]
        smallest_dimension = min(image_width, image_height)

        sitting_circle_radius = math.ceil(smallest_dimension * 0.75 * 0.5)
        token_diameter = math.ceil(smallest_dimension / 5.5)
        font_size = math.ceil(smallest_dimension * 0.04)

        # Load font
        font = ImageFont.truetype(Grimoire.FONT, font_size)

        # Add the gamemode icon in the center
        Grimoire.paste_gamemode_icon(game_obj, image, smallest_dimension, image_width / 2, image_height / 2)

        # Iterate in reverse to make the sitting order clockwise
        for i, n in enumerate(range(game_obj.nb_players - 1, -1, -1)):
            current_player = game_obj.sitting_order[i]
            current_angle = (2 * math.pi / game_obj.nb_players) * n

            Grimoire.process_player(image, font, current_player, sitting_circle_radius, token_diameter, current_angle)

        # Save grimoire to output
        image.save(Grimoire.GRIMOIRE_PATH)

    def random_background():
        """Select a random background"""
        backgrounds = [
            "botc/assets/grimoire/grimoire_background1.png",
            "botc/assets/grimoire/grimoire_background2.png"
        ]
        return random.choice(backgrounds)

    def paste_gamemode_icon(game_obj, image, image_smallest_size, x, y):
        if game_obj.gamemode == Gamemode.trouble_brewing:
            icon = Image.open(Grimoire.TB_ICON)
        elif game_obj.gamemode == Gamemode.bad_moon_rising:
            icon = Image.open(Grimoire.BMR_ICON)
        elif game_obj.gamemode == Gamemode.sects_and_violets:
            icon = Image.open(Grimoire.SV_ICON)
        else:
            assert 0, "Invalid gamemode for grimoire creation"

        icon_width = icon.size[0]
        icon_height = icon.size[1]

        icon_smallest_size = min(icon_width, icon_height)

        reduction_ration = icon_smallest_size / (image_smallest_size / 4)
        reduction_ration = 1 / reduction_ration

        icon.thumbnail((icon_width * reduction_ration, icon_height * reduction_ration), Image.ANTIALIAS)

        adjusted_x = int(x - (icon_width * reduction_ration) / 2)
        adjusted_y = int(y - (icon_height * reduction_ration) / 2)

        try:
            image.paste(icon, (adjusted_x, adjusted_y), icon.convert('RGBA'))
        except Exception:
            pass

    def process_player(image, font: ImageFont, player_obj, sitting_circle_radius, token_width, player_angle):
        draw = ImageDraw.Draw(image, 'RGBA')

        reminder_token_size = math.ceil(token_width / 2)

        image_width, image_height = image.size

        token_x = math.sin(player_angle) * sitting_circle_radius + (image_width / 2)
        token_y = math.cos(player_angle) * sitting_circle_radius + (image_height / 2)

        adjusted_token_x = int(token_x - (token_width / 2))
        adjusted_token_y = int(token_y - (token_width / 2))

        # Paste the token
        role_obj = player_obj.role
        if player_obj.old_role is not None:
            # Use old_role, role change tokens should be handled by the relevant character classes
            role_obj = player_obj.old_role
        try:
            token_image = Image.open(TokenPathGrabber().getpath(role_obj.ego_self)) # True self is added as a reminder token
            token_image.thumbnail((token_width, token_width), Image.ANTIALIAS)
            image.paste(token_image, (adjusted_token_x, adjusted_token_y), token_image.convert('RGBA'))
        except Exception:
            # If we are unable to paste the image, paste the role name instead
            role_text = player_obj.role.ego_self.name
            w, h = font.getsize(role_text)
            adjusted_text_x = int(token_x - (w / 2))
            adjusted_text_y = int(token_y - (h / 2))

            draw.rectangle((
                            adjusted_text_x,
                            adjusted_text_y,
                            adjusted_text_x + w,
                            adjusted_text_y + h
                        ), fill = (37, 30, 23, 140))
            draw.text((adjusted_text_x, adjusted_text_y), role_text, (255, 255, 255), font=font)

        reminder_tokens = []
        if role_obj.true_self.name != role_obj.ego_self.name:
            reminder_tokens.append(TokenPathGrabber().getpath(role_obj.true_self))

        # Dead shroud
        if player_obj.is_apparently_dead():
            shroud = Image.open(Grimoire.SHROUD)
            shroud_size_x = shroud.size[0]
            shroud_size_y = shroud.size[1]

            ratio = shroud_size_y / (token_width / 2)
            ratio = 1 / ratio
            thumbnail_x = int(shroud_size_x * ratio)
            thumbnail_y = int(shroud_size_y * ratio)
            shroud.thumbnail((thumbnail_x, thumbnail_y), Image.ANTIALIAS)

            shroud_x = int(token_x - thumbnail_x / 2)
            shroud_y = int(token_y - token_width / 2)
            image.paste(shroud, (shroud_x, shroud_y), shroud.convert("RGBA"))

        reminder_tokens += player_obj.reminder_tokens

        token_spacing = math.floor(min(token_width + 2, # Normal spacing
        (sitting_circle_radius - (reminder_token_size + token_width) / 2) / (len(reminder_tokens) + 1))) # Possible overlap, too many tokens
        curr_radius = sitting_circle_radius - (token_width / 2) - (reminder_token_size / 2)
        
        for reminder_token in reminder_tokens:
            reminder_token_image = Image.open(reminder_token)
            reminder_token_image.thumbnail((reminder_token_size, reminder_token_size), Image.ANTIALIAS)
            
            reminder_token_x = math.sin(player_angle) * curr_radius + (image_width / 2)
            reminder_token_y = math.cos(player_angle) * curr_radius + (image_height / 2)

            adjusted_reminder_token_x = int(reminder_token_x - (reminder_token_size / 2))
            adjusted_reminder_token_y = int(reminder_token_y - (reminder_token_size / 2))

            image.paste(reminder_token_image, (adjusted_reminder_token_x, adjusted_reminder_token_y), reminder_token_image.convert('RGBA'))

            curr_radius -= token_spacing

        # Player name
        name_text = player_obj.user.display_name
        w, h = font.getsize(name_text)
        adjusted_text_x = int(token_x - (w / 2))
        adjusted_text_y = int(adjusted_token_y - h)

        draw.rectangle((
                        adjusted_text_x,
                        adjusted_text_y,
                        adjusted_text_x + w,
                        adjusted_text_y + h
                    ), fill = (37, 30, 23, 140))
        draw.text((adjusted_text_x, adjusted_text_y), name_text, (255, 255, 255), font=font)


class TokenPathGrabber:
    """A utility object to grab the path of a token png file"""

    def getpath(self, character_obj):
        # Trouble brewing gamemode
        if character_obj.gm_of_appearance == Gamemode.trouble_brewing:
            character_name = character_obj.name.title()
            words = character_name.split(" ")
            words.append("Token.png")
            file_name = "_".join(words)
            return "botc/assets/tb_tokens_rgba/" + file_name
        # Bad moon rising gamemode
        elif character_obj.gm_of_appearance == Gamemode.bad_moon_rising:
            pass
        # Sects and violets gamemode
        elif character_obj.gm_of_appearance == Gamemode.sects_and_violets:
            pass
