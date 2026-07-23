"""
Generates the animated header logo for the pbip-doctor README: a dark
charcoal square tile, white EKG ring + trace, muted-gold pulse dots
breathing out of phase. Renders at 4x supersample via Pillow (no cairosvg /
libcairo dependency needed) then downsamples for anti-aliasing.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "header-badge.gif"

FINAL_SIZE = 160
SUPERSAMPLE = 4
CANVAS = FINAL_SIZE * SUPERSAMPLE

SCALE = 1.5 * SUPERSAMPLE  # px (final) per viewBox unit
OFFSET = CANVAS / 2 - 50 * SCALE  # center viewBox (50,50) on canvas center


def p(x, y):
    return (OFFSET + x * SCALE, OFFSET + y * SCALE)


BG = (24, 22, 19)           # dark charcoal tile, matches README palette
WHITE = (245, 242, 235)
GOLD = (201, 160, 61)

TRACE_PTS = [
    (8, 50), (32, 50), (38, 37), (47, 63),
    (53, 50), (65, 50), (70, 43), (75, 50), (92, 50),
]

N_FRAMES = 24
DURATION_MS = 90  # ~2.16s full loop
PHASE_B = 1.0 / 3.0


def ease(t):
    return 0.5 - 0.5 * math.cos(2 * math.pi * t)


def render_frame(t):
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)

    r_ring = 36 * SCALE
    cx, cy = CANVAS / 2, CANVAS / 2
    ring_w = max(2, round(2.6 * SCALE))
    draw.ellipse(
        [cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring],
        outline=WHITE,
        width=ring_w,
    )

    trace_w = max(2, round(2.2 * SCALE))
    pts = [p(x, y) for x, y in TRACE_PTS]
    draw.line(pts, fill=WHITE, width=trace_w, joint="curve")
    cap_r = trace_w / 2
    for pt in (pts[0], pts[-1]):
        draw.ellipse(
            [pt[0] - cap_r, pt[1] - cap_r, pt[0] + cap_r, pt[1] + cap_r],
            fill=WHITE,
        )

    ea = ease(t)
    eb = ease((t + PHASE_B) % 1.0)
    for (vx, vy), e in (((8, 50), ea), ((92, 50), eb)):
        radius = (2.2 + 0.8 * e) * SCALE
        cx_d, cy_d = p(vx, vy)
        draw.ellipse(
            [cx_d - radius, cy_d - radius, cx_d + radius, cy_d + radius],
            fill=GOLD,
        )

    return img.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)


frames = [render_frame(i / N_FRAMES) for i in range(N_FRAMES)]

frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=DURATION_MS,
    loop=0,
    optimize=True,
)
print(f"wrote {OUT} ({len(frames)} frames)")
