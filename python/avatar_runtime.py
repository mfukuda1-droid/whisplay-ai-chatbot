"""WhisPlay 40x40 face-focused status avatar renderer."""

import builtins
import sys
from PIL import Image, ImageDraw

PALETTE = {
    "outline": (2, 15, 45, 255), "hair_dark": (8, 31, 79, 255),
    "hair": (18, 50, 116, 255), "hair_light": (61, 100, 177, 255),
    "skin": (255, 214, 180, 255), "skin_shadow": (242, 165, 124, 255),
    "white": (255, 244, 212, 255), "amber": (255, 181, 0, 255),
    "amber_dark": (144, 63, 8, 255), "orange": (255, 119, 0, 255),
    "orange_light": (255, 174, 0, 255), "brown": (82, 34, 33, 255),
    "navy": (13, 37, 91, 255), "blue": (44, 84, 153, 255),
    "cyan": (61, 211, 232, 255), "red": (235, 58, 32, 255),
    "blush": (255, 168, 151, 255), "transparent": (0, 0, 0, 0),
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
        value = (status or "").lower().strip()
        if value in {"starting", "hello"}: return "idle"
        if value == "idle": return "sleep"
        if value in {"detecting", "listening"}: return "listening"
        if value in {"recognizing", "thinking"}: return "thinking"
        if value.startswith("answer"): return "answer"
        if value == "error": return "error"
        return None

    @classmethod
    def _draw(cls, state):
        p = PALETTE
        img = Image.new("RGBA", (40, 40), p["transparent"])
        d = ImageDraw.Draw(img)

        # Face-first composition: the head fills almost the entire 40x40 tile.
        d.ellipse((1, 1, 38, 39), fill=p["outline"])
        d.ellipse((3, 3, 36, 38), fill=p["hair_dark"])
        d.ellipse((5, 4, 34, 36), fill=p["hair"])
        d.rectangle((7, 8, 10, 20), fill=p["hair_light"])
        d.rectangle((12, 5, 18, 7), fill=p["hair_light"])
        d.rectangle((30, 9, 32, 18), fill=p["blue"])

        # Large face area; torso intentionally removed for readability.
        d.rounded_rectangle((7, 10, 33, 36), radius=10, fill=p["skin"], outline=p["outline"], width=1)
        d.rectangle((9, 11, 31, 16), fill=p["skin"])

        # Large fixed bangs.
        d.polygon([(6,11),(10,6),(15,4),(17,15),(19,11),(20,3),(24,4),(24,15),(27,10),(30,7),(34,12),(31,17),(9,17)], fill=p["hair"])
        d.rectangle((19,4,21,14), fill=p["hair_dark"])

        # Larger orange hair clip.
        d.polygon([(29,5),(34,8),(31,13),(26,10)], fill=p["orange"], outline=p["outline"])
        d.polygon([(29,7),(32,8),(31,11),(28,10)], fill=p["orange_light"])

        if state == "sleep":
            d.line((10,23,14,26,18,23), fill=p["brown"], width=2)
            d.line((22,23,26,26,30,23), fill=p["brown"], width=2)
            d.arc((16,29,24,34), 10, 170, fill=p["brown"], width=1)
            d.rectangle((32,15,34,17), fill=p["cyan"])
            d.rectangle((34,12,37,14), fill=p["cyan"])
            d.rectangle((36,8,39,10), fill=p["cyan"])
        elif state == "error":
            d.line((9,21,17,27), fill=p["brown"], width=3)
            d.line((17,21,9,27), fill=p["brown"], width=3)
            d.line((23,21,31,27), fill=p["brown"], width=3)
            d.line((31,21,23,27), fill=p["brown"], width=3)
            d.line((15,33,19,30,23,33,27,30), fill=p["brown"], width=2)
            d.rectangle((35,4,38,12), fill=p["red"])
            d.rectangle((35,14,38,17), fill=p["red"])
        else:
            cls._eye(d, 14, 24, wide=state == "listening", look_right=state == "thinking")
            cls._eye(d, 26, 24, wide=state == "listening", look_right=state == "thinking")
            if state == "listening":
                d.ellipse((18,30,22,35), fill=p["brown"])
                # Approved listening cue: big eyes + O mouth + strong cyan waves.
                d.arc((0,15,8,32), 275, 85, fill=p["cyan"], width=3)
                d.arc((32,15,40,32), 95, 265, fill=p["cyan"], width=3)
            elif state == "thinking":
                d.ellipse((18,31,22,33), fill=p["brown"])
                d.arc((32,4,39,12), 200, 500, fill=p["orange_light"], width=3)
                d.rectangle((35,14,38,17), fill=p["orange_light"])
            elif state == "answer":
                d.rectangle((15,29,25,35), fill=p["brown"])
                d.rectangle((17,31,23,33), fill=p["blush"])
                d.polygon([(33,24),(39,21),(37,27)], fill=p["orange_light"])
                d.polygon([(34,30),(39,31),(35,34)], fill=p["orange_light"])
            else:
                d.arc((15,29,25,35), 5, 175, fill=p["brown"], width=2)

        if state not in {"sleep", "error"}:
            d.rectangle((8,29,11,30), fill=p["blush"])
            d.rectangle((29,29,32,30), fill=p["blush"])
        return img

    @staticmethod
    def _eye(draw, x, y, wide=False, look_right=False):
        p = PALETTE
        rx, ry = (5, 6) if wide else (4, 5)
        draw.ellipse((x-rx, y-ry, x+rx, y+ry), fill=p["white"], outline=p["outline"], width=1)
        pupil_x = x + (2 if look_right else 0)
        draw.ellipse((pupil_x-3, y-3, pupil_x+3, y+4), fill=p["amber_dark"])
        draw.rectangle((pupil_x-2, y, pupil_x+2, y+3), fill=p["amber"])
        draw.rectangle((pupil_x-2, y-3, pupil_x, y-1), fill=p["white"])


def install_avatar_hook():
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
            draw.rectangle((x - 2, y - 2, x + 42, y + 42), fill=(0, 0, 0, 255))
            image.paste(avatar, (x, y), avatar)
            return result

        cls.render_header = render_header_with_avatar
        builtins.__build_class__ = original_build_class
        return cls

    builtins.__build_class__ = build_class
