"""
Generates the animated pbip-doctor header lockup (icon + wordmark baked into
one image, transparent background): white EKG ring + trace, "pbip-doctor" in
Consolas Bold, muted-gold pulse dots breathing out of phase. Renders at 4x
supersample via Pillow (no cairosvg / libcairo dependency needed) then
downsamples for anti-aliasing, and keys a threshold-alpha mask into the GIF's
single transparent palette index.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "header-badge.gif"

SUPERSAMPLE = 4
FINAL_H = 160
ICON_MARGIN = 20
ICON_D_FINAL = FINAL_H - 2 * ICON_MARGIN          # 120
SCALE = (ICON_D_FINAL / 2 / 36) * SUPERSAMPLE      # viewBox units -> working px
GAP_FINAL = 26
TEXT = "pbip-doctor"
FONT_PATH = "C:/Windows/Fonts/consolab.ttf"
FONT_SIZE_FINAL = 56

WHITE = (245, 242, 235, 255)
GOLD = (201, 160, 61, 255)

TRACE_PTS = [
    (8, 50), (32, 50), (38, 37), (47, 63),
    (53, 50), (65, 50), (70, 43), (75, 50), (92, 50),
]

N_FRAMES = 24
DURATION_MS = 90
PHASE_B = 1.0 / 3.0


def ease(t):
    return 0.5 - 0.5 * math.cos(2 * math.pi * t)


font = ImageFont.truetype(FONT_PATH, FONT_SIZE_FINAL * SUPERSAMPLE)
tmp = Image.new("RGBA", (10, 10))
tmp_draw = ImageDraw.Draw(tmp)
text_bbox = tmp_draw.textbbox((0, 0), TEXT, font=font)
text_w_work = text_bbox[2] - text_bbox[0]
text_h_work = text_bbox[3] - text_bbox[1]

FINAL_W = ICON_MARGIN + ICON_D_FINAL + GAP_FINAL + int(text_w_work / SUPERSAMPLE) + ICON_MARGIN
CANVAS_W = FINAL_W * SUPERSAMPLE
CANVAS_H = FINAL_H * SUPERSAMPLE

icon_cx = (ICON_MARGIN + ICON_D_FINAL / 2) * SUPERSAMPLE
icon_cy = (FINAL_H / 2) * SUPERSAMPLE
icon_offset_x = icon_cx - 50 * SCALE
icon_offset_y = icon_cy - 50 * SCALE


def vp(x, y):
    return (icon_offset_x + x * SCALE, icon_offset_y + y * SCALE)


text_x = (ICON_MARGIN + ICON_D_FINAL + GAP_FINAL) * SUPERSAMPLE - text_bbox[0]
text_y = CANVAS_H / 2 - text_h_work / 2 - text_bbox[1]


def render_frame(t):
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r_ring = 36 * SCALE
    ring_w = max(2, round(2.6 * SCALE))
    draw.ellipse(
        [icon_cx - r_ring, icon_cy - r_ring, icon_cx + r_ring, icon_cy + r_ring],
        outline=WHITE, width=ring_w,
    )

    trace_w = max(2, round(2.2 * SCALE))
    pts = [vp(x, y) for x, y in TRACE_PTS]
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
        cx_d, cy_d = vp(vx, vy)
        draw.ellipse(
            [cx_d - radius, cy_d - radius, cx_d + radius, cy_d + radius],
            fill=GOLD,
        )

    draw.text((text_x, text_y), TEXT, font=font, fill=WHITE)

    return img.resize((FINAL_W, FINAL_H), Image.LANCZOS)


frames = [render_frame(i / N_FRAMES) for i in range(N_FRAMES)]

SENTINEL = (255, 0, 255)
ALPHA_THRESHOLD = 128
pal_frames = []
for f in frames:
    alpha = f.split()[3]
    flat = Image.new("RGB", f.size, SENTINEL)
    flat.paste(f.convert("RGB"), mask=None)
    # only paste where alpha >= threshold, so anti-aliased near-transparent
    # edge pixels fall back to the sentinel instead of a blended fringe
    mask = alpha.point(lambda a: 255 if a >= ALPHA_THRESHOLD else 0)
    composed = Image.new("RGB", f.size, SENTINEL)
    composed.paste(f.convert("RGB"), mask=mask)
    pal_frames.append(composed)

# shared palette across all frames so the transparent index is consistent
strip = Image.new("RGB", (pal_frames[0].width, pal_frames[0].height * len(pal_frames)))
for i, fr in enumerate(pal_frames):
    strip.paste(fr, (0, i * fr.height))
strip_q = strip.quantize(colors=255, method=Image.MEDIANCUT)
palette = strip_q.getpalette()

quantized = []
for i, fr in enumerate(pal_frames):
    box = (0, i * fr.height, fr.width, (i + 1) * fr.height)
    q = strip_q.crop(box)
    quantized.append(q)

# find (or force) the sentinel color's palette index
sentinel_img = Image.new("RGB", (1, 1), SENTINEL).quantize(
    palette=quantized[0], dither=Image.NONE
)
transparent_index = sentinel_img.getpixel((0, 0))

quantized[0].save(
    OUT,
    save_all=True,
    append_images=quantized[1:],
    duration=DURATION_MS,
    loop=0,
    transparency=transparent_index,
    disposal=2,
    optimize=False,
)
print(f"wrote {OUT} size={FINAL_W}x{FINAL_H} frames={len(quantized)}")
