"""
Deterministic pixel-art avatar generator.
Same username → same avatar every time.
Produces a symmetric 5×5 identicon-style SVG in the game's cyberpunk palette.
"""

import hashlib

# Cyberpunk palette — one primary + one accent per avatar
_PALETTES = [
    ("#05D9E8", "#a371f7"),   # cyan   / purple
    ("#a371f7", "#FF2A6D"),   # purple / pink
    ("#FF2A6D", "#FFC200"),   # pink   / gold
    ("#FFC200", "#05D9E8"),   # gold   / cyan
    ("#3fb950", "#05D9E8"),   # green  / cyan
    ("#05D9E8", "#FF2A6D"),   # cyan   / pink
    ("#a371f7", "#FFC200"),   # purple / gold
    ("#FF2A6D", "#3fb950"),   # pink   / green
]

_BG = "#050514"


def _digest(username: str) -> bytes:
    return hashlib.sha256(username.lower().encode()).digest()


def generate_avatar_svg(username: str, size: int = 40) -> str:
    d = _digest(username)

    # Pick colour palette
    primary, accent = _PALETTES[d[0] % len(_PALETTES)]

    # Build 5×5 symmetric grid (only decide 3 cols, mirror cols 0-1 onto 4-3)
    cell = size / 5
    rects: list[str] = []

    for row in range(5):
        for col in range(3):
            byte_idx = row * 3 + col
            val = d[byte_idx % len(d)]
            if val % 2 == 0:
                continue
            color = accent if val % 7 == 0 else primary
            # Draw cell
            x = col * cell
            y = row * cell
            rects.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" '
                f'width="{cell:.1f}" height="{cell:.1f}" fill="{color}"/>'
            )
            # Mirror (skip center column)
            if col < 2:
                mx = (4 - col) * cell
                rects.append(
                    f'<rect x="{mx:.1f}" y="{y:.1f}" '
                    f'width="{cell:.1f}" height="{cell:.1f}" fill="{color}"/>'
                )

    cells_svg = "\n  ".join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<rect width="{size}" height="{size}" fill="{_BG}"/>'
        f'{cells_svg}'
        f'</svg>'
    )
