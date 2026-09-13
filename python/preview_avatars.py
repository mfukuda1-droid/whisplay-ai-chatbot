"""Export native 64x64 transparent PNGs: python3 python/preview_avatars.py."""

import argparse
from pathlib import Path

from avatar_runtime import AvatarRenderer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=Path('data/avatar-preview'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # These are avatar states, not incoming statuses (status idle means sleep).
    for state in ('idle', 'sleep', 'listening', 'thinking', 'answer', 'error'):
        target = args.output_dir / f'{state}.png'
        AvatarRenderer._draw(state).save(target)
        print(f'{target} (64x64 RGBA)')


if __name__ == '__main__':
    main()
