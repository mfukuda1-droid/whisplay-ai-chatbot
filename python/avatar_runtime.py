"""WhisPlay 64x64 face-focused status avatar renderer."""

import builtins
from PIL import Image, ImageDraw

PALETTE = {
    "outline": (2, 15, 45, 255), "hair_dark": (8, 31, 79, 255),
    "hair": (28, 55, 119, 255), "hair_light": (61, 100, 177, 255),
    "skin": (255, 229, 195, 255), "skin_shadow": (242, 165, 124, 255),
    "white": (255, 244, 212, 255), "amber": (255, 181, 0, 255),
    "amber_dark": (144, 63, 8, 255), "orange": (255, 119, 0, 255),
    "orange_light": (255, 174, 0, 255), "brown": (82, 34, 33, 255),
    "navy": (13, 37, 91, 255), "blue": (44, 84, 153, 255),
    "cyan": (61, 211, 232, 255), "red": (235, 58, 32, 255),
    "blush": (255, 168, 151, 255), "transparent": (0, 0, 0, 0),
    "black": (0, 0, 0, 255),
}

class AvatarRenderer:
    SIZE = 64
    _cache = {}

    @classmethod
    def for_status(cls, status):
        key = cls._status_key(status)
        if key is None: return None
        if key not in cls._cache: cls._cache[key] = cls._draw(key)
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
        # All coordinates are authored on the final 64px grid. No resampling,
        # curves, or antialiasing: the stepped silhouette is part of the art.
        p = PALETTE
        img = Image.new("RGBA", (cls.SIZE, cls.SIZE), p["transparent"])
        d = ImageDraw.Draw(img)

        def polygon(points, color):
            d.polygon(points, fill=p[color])

        def rect(box, color):
            d.rectangle(box, fill=p[color])

        # Face-only bob, broad cheeks and long overlapping bangs, based on
        # the reference. Each contour is authored directly on the 64px grid.
        polygon([(27, 2), (36, 2), (36, 4), (43, 4), (43, 6),
                 (48, 6), (48, 9), (52, 9), (52, 13), (55, 13),
                 (55, 19), (58, 19), (58, 29), (60, 29), (60, 40),
                 (62, 40), (62, 49), (59, 49), (59, 54), (54, 57),
                 (49, 57), (49, 60), (42, 61), (21, 61), (15, 59),
                 (12, 56), (7, 56), (4, 52), (2, 49), (2, 40),
                 (4, 40), (4, 30), (6, 30), (6, 21), (8, 21),
                 (8, 15), (12, 15), (12, 11), (16, 11), (16, 8),
                 (21, 8), (21, 5), (27, 5)], "outline")
        polygon([(27, 5), (36, 5), (42, 7), (47, 10), (51, 14),
                 (54, 21), (56, 31), (58, 40), (60, 42), (60, 48),
                 (56, 53), (51, 54), (46, 59), (19, 58), (13, 54),
                 (8, 53), (5, 48), (6, 39), (8, 30), (10, 21),
                 (14, 15), (18, 11), (23, 8)], "hair")
        polygon([(12, 30), (21, 20), (42, 20), (52, 31), (53, 45),
                 (48, 53), (43, 56), (38, 59), (26, 59), (20, 56),
                 (15, 53), (10, 45)], "skin_shadow")
        polygon([(17, 29), (24, 21), (40, 21), (47, 29), (50, 43),
                 (47, 51), (42, 55), (37, 58), (27, 58), (21, 55),
                 (16, 51), (13, 43)], "skin")
        # Ears remain visible between the outer bob and cheek-side locks.
        rect((8, 40, 11, 45), "skin_shadow")
        rect((10, 44, 12, 47), "skin_shadow")
        rect((52, 40, 55, 45), "skin_shadow")
        rect((51, 44, 53, 47), "skin_shadow")
        polygon([(27, 7), (34, 6), (40, 9), (45, 14), (48, 23),
                 (50, 30), (53, 34), (53, 43), (50, 49), (46, 51),
                 (44, 50), (47, 47), (48, 38), (44, 33), (41, 30),
                 (39, 23), (38, 21), (38, 30), (36, 34), (35, 38),
                 (32, 37), (30, 34), (29, 37), (28, 31), (26, 34),
                 (24, 27), (23, 25), (22, 31), (19, 29), (17, 32),
                 (14, 37), (14, 46), (17, 50), (19, 51), (15, 52),
                 (11, 48), (10, 39), (12, 28), (16, 19), (22, 12)], "outline")
        polygon([(28, 8), (34, 8), (38, 11), (41, 17), (42, 26),
                 (46, 33), (49, 37), (49, 45), (47, 49), (50, 46),
                 (51, 35), (47, 28), (45, 21), (43, 15), (39, 10)], "hair_dark")
        polygon([(27, 9), (33, 9), (37, 12), (39, 21), (37, 21),
                 (37, 29), (34, 35), (33, 34), (32, 31), (30, 34),
                 (29, 28), (27, 30), (26, 24), (24, 23), (23, 28),
                 (21, 27), (19, 29), (15, 34), (12, 41), (12, 32),
                 (16, 22), (20, 17), (23, 12)], "hair")
        d.line([(12, 25), (16, 18), (21, 12), (26, 8)], fill=p["blue"], width=1)
        d.line([(37, 7), (43, 10), (48, 17)], fill=p["blue"], width=1)
        polygon([(6, 43), (8, 49), (11, 52), (10, 54), (7, 51)], "hair_dark")
        polygon([(57, 43), (56, 50), (53, 54), (56, 53), (59, 48)], "hair_dark")
        rect((6, 49, 7, 51), "orange")
        rect((8, 51, 9, 53), "orange")
        rect((55, 50, 57, 51), "orange")
        rect((54, 52, 55, 53), "orange")
        polygon([(47, 19), (54, 26), (47, 33), (40, 26)], "outline")
        polygon([(47, 21), (52, 26), (47, 31), (42, 26)], "orange")
        polygon([(47, 22), (50, 26), (47, 29), (44, 26)], "orange_light")
        polygon([(47, 24), (49, 26), (47, 28), (45, 26)], "outline")
        rect((46, 22, 47, 23), "amber")
        rect((51, 33, 53, 34), "cyan")
        rect((52, 35, 53, 36), "blue")

        if state == "sleep":
            d.line([(16, 40), (19, 43), (24, 43), (27, 40)], fill=p["brown"], width=2)
            d.line([(36, 40), (39, 43), (44, 43), (47, 40)], fill=p["brown"], width=2)
            rect((29, 53, 34, 53), "brown")
            cls._mark(d, 53, 3, ["11111", "00010", "00100", "01000", "11111"], "cyan", 2)
            cls._mark(d, 56, 16, ["1111", "0010", "0100", "1111"], "blue")
        elif state == "error":
            for x in (17, 37):
                d.line((x, 38, x + 8, 46), fill=p["brown"], width=2)
                d.line((x + 8, 38, x, 46), fill=p["brown"], width=2)
            d.line([(27, 55), (30, 52), (33, 52), (36, 55)], fill=p["brown"], width=2)
            cls._mark(d, 57, 3, ["11", "11", "11", "11", "00", "11"], "red", 2)
            polygon([(50, 37), (54, 43), (54, 47), (52, 49),
                     (49, 48), (48, 45)], "cyan")
            rect((50, 43, 50, 46), "white")
        else:
            cls._eye(d, 16, state)
            cls._eye(d, 36, state)
            if state == "listening":
                polygon([(30, 47), (33, 47), (35, 49), (35, 52),
                         (33, 54), (30, 54), (28, 52), (28, 49)], "brown")
                rect((31, 49, 32, 51), "skin_shadow")
                for x, direction in ((0, 1), (63, -1)):
                    d.line([(x + 2 * direction, 27), (x, 31),
                            (x, 40), (x + 2 * direction, 44)], fill=p["cyan"], width=1)
                    rect((min(x + 3 * direction, x + 4 * direction), 32,
                          max(x + 3 * direction, x + 4 * direction), 39), "cyan")
            elif state == "thinking":
                rect((30, 53, 35, 54), "brown")
                cls._mark(d, 53, 2, ["01110", "11011", "00011", "00110", "00100", "00000", "00100"], "orange_light", 2)
            elif state == "answer":
                polygon([(26, 51), (37, 51), (37, 54), (34, 57),
                         (29, 57), (26, 54)], "brown")
                rect((28, 51, 35, 52), "white")
                rect((30, 55, 34, 56), "blush")
                cls._mark(d, 56, 25, ["00100", "00100", "11111", "00100", "00100"], "orange_light")
                d.line((55, 18, 60, 14), fill=p["orange_light"], width=2)
                d.line((56, 35, 61, 37), fill=p["orange"], width=2)
            else:
                d.line([(29, 52), (30, 54), (33, 54), (34, 52)], fill=p["brown"], width=1)
        rect((16, 49, 21, 50), "blush")
        rect((42, 49, 47, 50), "blush")
        return img

    @staticmethod
    def _eye(draw, x, state):
        p = PALETTE
        top = 34 if state == "listening" else 36
        # Wide amber irises, dark upper lashes and a gold lower crescent.
        draw.polygon([(x, top + 3), (x + 2, top + 1), (x + 3, top),
                      (x + 8, top), (x + 10, top + 2), (x + 11, top + 3),
                      (x + 11, 46), (x + 9, 48), (x + 3, 48),
                      (x, 45)], fill=p["outline"])
        draw.rectangle((x, top + 5, x + 11, 45), fill=p["white"])
        draw.rectangle((x + 2, top + 3, x + 9, 45), fill=p["amber_dark"])
        draw.rectangle((x + 3, 44, x + 8, 47), fill=p["orange"])
        draw.rectangle((x + 4, 44, x + 7, 47), fill=p["amber"])
        y = top + 2 if state == "thinking" else top + 4
        draw.rectangle((x + 4, y, x + 7, y + 4), fill=p["brown"])
        draw.rectangle((x + 7, y, x + 8, y + 1), fill=p["white"])
        draw.point((x + 2, top + 4), fill=p["white"])
        draw.line((x + 2, top - 3, x + 5, top - 3), fill=p["brown"])

    @staticmethod
    def _mark(draw, x, y, rows, color, scale=1):
        """Small hand-pixelled symbols; independent of system fonts."""
        for row, bits in enumerate(rows):
            for col, bit in enumerate(bits):
                if bit == "1":
                    left, top = x + col * scale, y + row * scale
                    draw.rectangle((left, top, left + scale - 1,
                                    top + scale - 1), fill=PALETTE[color])


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
        if original_render_header is not None:
            def render_header_with_avatar(self, image, draw, status, emoji,
                                          battery_level, battery_color):
                self._status_avatar = AvatarRenderer.for_status(status)
                try:
                    return original_render_header(
                        self, image, draw, status, emoji, battery_level,
                        battery_color)
                finally:
                    self._status_avatar = None
            cls.render_header = render_header_with_avatar
        builtins.__build_class__ = original_build_class
        return cls

    builtins.__build_class__ = build_class
