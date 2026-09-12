"""WhisPlay 40x40 status avatar renderer.

This module keeps the avatar implementation self-contained and reversible.
It installs a temporary class-construction hook so the existing RenderThread
header renderer can be wrapped without duplicating chatbot-ui.py.
"""

import builtins
import sys
from PIL import Image, ImageDraw


PALETTE = {
    "outline": (2, 15, 45, 255),
    "hair_dark": (8, 31, 79, 255),
    "hair": (18, 50, 116, 255),
    "hair_light": (61, 100, 177, 255),
    "skin": (255, 214, 180, 255),
    "skin_shadow": (242, 165, 124, 255),
    "white": (255, 244, 212, 255),
    "amber": (255, 181, 0, 255),
    "amber_dark": (144, 63, 8, 255),
    "orange": (255, 119, 0, 255),
    "orange_light": (255, 174, 0, 255),
    "brown": (82, 34, 33, 255),
    "navy": (13, 37, 91, 255),
    "blue": (44, 84, 153, 255),
    "cyan": (61, 211, 232, 255),
    "red": (235, 58, 32, 255),
    "blush": (255, 168, 151, 255),
    "transparent": (0, 0, 0, 0),
    "black": (0, 0, 0, 255),
}


class AvatarRenderer:
    SIZE = 40
    _cache = {}

    @classmethod
    def for_status(cls, status):
        key = cls._status_key(status)
        if key is None:
            return None
        if key not in cls._cache:
            cls._cache[key] = cls._draw(key)
        return cls._cache[key]

    @staticmethod
    def _status_key(status):
        value = (status or "").lower()
        if value in {"starting", "hello"}:
            return "idle"
        if value == "idle":
            return "sleep"
        if value in {"detecting", "listening"}:
            return "listening"
        if value in {"recognizing", "thinking"}:
            return "thinking"
        if value.startswith("answer"):
            return "answer"
        if value == "error":
            return "error"
        return None

    @classmethod
    def _draw(cls, state):
        p = PALETTE
        img = Image.new("RGBA", (cls.SIZE, cls.SIZE), p["transparent"])
        d = ImageDraw.Draw(img)

        # Hair silhouette / bob.
        d.polygon([(5,11),(8,6),(14,3),(26,3),(32,6),(35,11),(37,22),(34,30),(29,34),(11,34),(6,30),(3,23)], fill=p["outline"])
        d.polygon([(7,12),(10,7),(15,5),(25,5),(30,7),(33,12),(35,23),(31,30),(27,32),(13,32),(8,29),(5,22)], fill=p["hair_dark"])
        d.polygon([(9,11),(13,7),(18,5),(25,6),(30,9),(32,18),(31,25),(28,29),(12,29),(8,25),(7,18)], fill=p["hair"])
        d.rectangle((10,9,12,17), fill=p["hair_light"])
        d.rectangle((14,6,18,8), fill=p["hair_light"])
        d.rectangle((28,10,30,17), fill=p["blue"])

        # Face.
        d.rounded_rectangle((9,11,31,31), radius=8, fill=p["skin"], outline=p["outline"], width=1)
        d.rectangle((11,12,28,16), fill=p["skin"])

        # Bangs.
        d.polygon([(9,10),(13,6),(16,6),(16,15),(18,12),(19,5),(23,5),(23,15),(25,12),(27,7),(31,11),(29,16),(11,16)], fill=p["hair"])
        d.rectangle((18,5,20,14), fill=p["hair_dark"])

        # Orange diamond hair clip.
        d.polygon([(28,7),(31,9),(29,12),(26,10)], fill=p["orange"], outline=p["outline"])
        d.polygon([(28,8),(30,9),(29,11),(27,10)], fill=p["orange_light"])

        # Ears / side accents.
        d.rectangle((7,20,9,25), fill=p["skin_shadow"])
        d.rectangle((31,20,33,25), fill=p["skin_shadow"])
        d.rectangle((6,27,8,30), fill=p["orange"])
        d.rectangle((32,27,34,30), fill=p["orange"])

        # Eyes and expression.
        if state == "sleep":
            d.line((12,22,15,24,18,22), fill=p["brown"], width=2)
            d.line((22,22,25,24,28,22), fill=p["brown"], width=2)
            d.arc((17,25,23,29), 10, 170, fill=p["brown"], width=1)
            d.rectangle((31,14,33,16), fill=p["cyan"])
            d.rectangle((33,12,35,14), fill=p["cyan"])
        elif state == "error":
            d.line((11,20,17,25), fill=p["brown"], width=2)
            d.line((17,20,11,25), fill=p["brown"], width=2)
            d.line((23,20,29,25), fill=p["brown"], width=2)
            d.line((29,20,23,25), fill=p["brown"], width=2)
            d.line((16,29,19,27,22,29,25,27), fill=p["brown"], width=1)
            d.rectangle((34,6,36,12), fill=p["red"])
            d.rectangle((34,14,36,16), fill=p["red"])
        else:
            cls._eye(d, 15, 22, wide=state == "listening", look_right=state == "thinking")
            cls._eye(d, 25, 22, wide=state == "listening", look_right=state == "thinking")
            if state == "listening":
                d.ellipse((19,27,21,30), fill=p["brown"])
                # Strong cyan audio waves so listening differs clearly from idle.
                d.arc((1,15,8,29), 285, 75, fill=p["cyan"], width=2)
                d.arc((32,15,39,29), 105, 255, fill=p["cyan"], width=2)
            elif state == "thinking":
                d.ellipse((19,28,21,29), fill=p["brown"])
                d.rectangle((33,7,35,12), fill=p["orange_light"])
                d.rectangle((35,5,37,7), fill=p["orange_light"])
                d.rectangle((34,14,36,16), fill=p["orange_light"])
            elif state == "answer":
                d.rectangle((17,27,23,31), fill=p["brown"])
                d.rectangle((18,28,22,29), fill=p["blush"])
                d.rectangle((32,25,35,27), fill=p["orange_light"])
                d.rectangle((34,28,37,30), fill=p["orange_light"])
            else:
                d.arc((17,26,23,30), 5, 175, fill=p["brown"], width=1)

        # Blush.
        if state not in {"sleep", "error"}:
            d.rectangle((10,26,12,27), fill=p["blush"])
            d.rectangle((28,26,30,27), fill=p["blush"])

        # Collar and navy outfit.
        d.polygon([(10,32),(15,30),(20,34),(25,30),(30,32),(32,39),(8,39)], fill=p["navy"], outline=p["outline"])
        d.polygon([(11,31),(16,30),(20,34),(15,36)], fill=p["white"])
        d.polygon([(29,31),(24,30),(20,34),(25,36)], fill=p["white"])
        d.rectangle((18,36,22,39), fill=p["orange"])

        return img

    @staticmethod
    def _eye(draw, x, y, wide=False, look_right=False):
        p = PALETTE
        rx = 4 if wide else 3
        ry = 5 if wide else 4
        draw.ellipse((x-rx, y-ry, x+rx, y+ry), fill=p["white"], outline=p["outline"])
        pupil_x = x + (1 if look_right else 0)
        draw.ellipse((pupil_x-2, y-2, pupil_x+2, y+3), fill=p["amber_dark"])
        draw.rectangle((pupil_x-1, y, pupil_x+1, y+2), fill=p["amber"])
        draw.rectangle((pupil_x-1, y-2, pupil_x, y-1), fill=p["white"])


def install_avatar_hook():
    """Wrap chatbot-ui.py RenderThread.render_header when the class is created."""
    if getattr(builtins, "_whisplay_avatar_hook_installed", False):
        return

    original_build_class = builtins.__build_class__
    builtins._whisplay_avatar_hook_installed = True

    def build_class(func, name, *bases, **kwargs):
        cls = original_build_class(func, name, *bases, **kwargs)
        if name != "RenderThread":
            return cls

        original_render_header = getattr(cls, "render_header", None)
        if original_render_header is None:
            builtins.__build_class__ = original_build_class
            return cls

        def render_header_with_avatar(self, image, draw, status, emoji, battery_level, battery_color):
            result = original_render_header(self, image, draw, status, emoji, battery_level, battery_color)
            avatar = AvatarRenderer.for_status(status)
            if avatar is None:
                return result

            main = sys.modules.get("__main__")
            status_font_size = getattr(main, "status_font_size", 20)
            terminal_text = getattr(main, "current_terminal_text", "")
            x = (self.whisplay.LCD_WIDTH - AvatarRenderer.SIZE) // 2
            if terminal_text:
                x = self.whisplay.CornerHeight
            y = status_font_size + 8

            # Clear the original emoji area, then draw the avatar. Existing
            # header/status-icon logic remains untouched and acts as fallback.
            draw.rectangle((x - 2, y - 2, x + AvatarRenderer.SIZE + 2, y + AvatarRenderer.SIZE + 2), fill=(0, 0, 0, 255))
            image.paste(avatar, (x, y), avatar)
            return result

        cls.render_header = render_header_with_avatar
        builtins.__build_class__ = original_build_class
        return cls

    builtins.__build_class__ = build_class
