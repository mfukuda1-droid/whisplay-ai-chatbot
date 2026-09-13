"""Hardware-free avatar and real header-layout regression checks."""

import ast
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from avatar_runtime import AvatarRenderer, install_avatar_hook


class AvatarTests(unittest.TestCase):
    def test_states_and_pixels(self):
        mapping = {'starting': 'idle', 'hello': 'idle', 'idle': 'sleep',
                   'detecting': 'listening', 'listening': 'listening',
                   'recognizing': 'thinking', 'thinking': 'thinking',
                   'answer': 'answer', 'answering': 'answer', 'error': 'error'}
        for status, state in mapping.items():
            self.assertEqual(AvatarRenderer._status_key(status), state)
            avatar = AvatarRenderer.for_status(status)
            self.assertEqual(avatar.size, (64, 64))
            self.assertEqual(avatar.mode, 'RGBA')
            self.assertEqual(set(avatar.getchannel('A').getdata()), {0, 255})
            self.assertIs(avatar, AvatarRenderer.for_status(status))
        for status in ('camera', 'camera_mode', 'music', 'unknown', '', None):
            self.assertIsNone(AvatarRenderer.for_status(status))
        self.assertEqual(len({AvatarRenderer._draw(s).tobytes()
                              for s in set(mapping.values())}), 6)

    def test_hook_and_header_layout(self):
        # Execute the production method alone, avoiding GPIO/server startup.
        source = Path(__file__).resolve().parents[1] / 'chatbot-ui.py'
        tree = ast.parse(source.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == 'RenderThread')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                      and n.name == 'render_header')
        calls = []
        board = SimpleNamespace(LCD_WIDTH=240, CornerHeight=10)
        env = dict(status_font_size=20, emoji_font_size=40, battery_font_size=13,
                   current_status='thinking', current_emoji='?',
                   current_terminal_text='', TERMINAL_MARGIN_X=8,
                   current_network_connected=False, current_wifi_signal_level=0,
                   current_vpn_connected=False, current_rag_icon_visible=False,
                   current_image_icon_visible=False, whisplay=board,
                   TextUtils=SimpleNamespace(draw_mixed_text=lambda *args: calls.append(args[2])))
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), env)
        install_avatar_hook()

        class RenderThread:
            render_header = env['render_header']

        renderer = RenderThread()
        renderer.whisplay = board
        renderer.status_font = renderer.emoji_font = renderer.battery_font = ImageFont.load_default()
        renderer.build_status_icons = lambda context: []
        renderer.render_status_icons = lambda *args: None
        terminal_calls = []
        renderer.draw_terminal_output = lambda *args: terminal_calls.append(args)
        for width in (240, 280):
            board.LCD_WIDTH = width
            for font_size in (20, 28):
                env['status_font_size'] = font_size
                for terminal in ('', 'running command'):
                    env['current_terminal_text'] = terminal
                    for status in ('thinking', 'camera', 'music', 'unknown'):
                        calls.clear()
                        terminal_calls.clear()
                        height = max(98, font_size + 8 + 64 + 6)
                        image = Image.new('RGBA', (width, height), 'black')
                        renderer.render_header(image, ImageDraw.Draw(image), status, '?', 90, 'green')
                        self.assertIsNone(renderer._status_avatar)
                        if status == 'thinking':
                            self.assertEqual(calls, ['thinking'])
                            x = board.CornerHeight if terminal else (width - 64) // 2
                            y = font_size + 8
                            self.assertLessEqual(y + 64, height - 6)
                            expected = Image.new('RGBA', (64, 64), 'black')
                            avatar = AvatarRenderer.for_status(status)
                            expected.paste(avatar, (0, 0), avatar)
                            self.assertEqual(image.crop((x, y, x + 64, y + 64)).tobytes(), expected.tobytes())
                            if terminal:
                                self.assertEqual(terminal_calls[0][2], x + 64 + 8)
                                self.assertEqual(terminal_calls[0][4], width - (x + 64 + 8) - 8)
                        else:
                            self.assertEqual(calls, ['thinking', '?'])
                            if terminal:
                                bbox = renderer.emoji_font.getbbox('?')
                                self.assertEqual(terminal_calls[0][2], board.CornerHeight + bbox[2] - bbox[0] + 8)


if __name__ == '__main__':
    unittest.main()
