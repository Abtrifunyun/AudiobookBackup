from PIL import Image, ImageDraw, ImageFilter

OUTPUT_PATH = "assets/book.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]
SUPERSAMPLE = 4


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_book(size: int) -> Image.Image:
    s = size * SUPERSAMPLE
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    m = s * 0.15
    radius = s * 0.10
    left, top, right, bottom = m, m, s - m, s - m
    width, height = right - left, bottom - top

    # soft drop shadow, offset down-right
    shadow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    off = s * 0.025
    ImageDraw.Draw(shadow).rounded_rectangle(
        [left + off, top + off * 1.6, right + off, bottom + off * 1.6],
        radius=radius, fill=(0, 0, 0, 130),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(s * 0.025)))

    # cover: vertical gradient (lighter teal top -> deep navy-teal bottom)
    face = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    fd = ImageDraw.Draw(face)
    top_color, bottom_color = (54, 138, 162), (16, 54, 76)
    steps = 96
    for i in range(steps):
        t = i / steps
        y0 = top + height * t
        y1 = top + height * (i + 1) / steps + 1
        fd.rectangle([left, y0, right, y1], fill=lerp_color(top_color, bottom_color, t) + (255,))

    # spine: translucent dark band, alpha-blended over the gradient (not a flat replace)
    spine_overlay = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    spine_w = width * 0.20
    ImageDraw.Draw(spine_overlay).rectangle(
        [left, top, left + spine_w, bottom], fill=(0, 0, 0, 95)
    )
    face = Image.alpha_composite(face, spine_overlay)

    # a thin light highlight along the spine's right edge, for a bit of depth
    highlight = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    hl_x = left + spine_w
    ImageDraw.Draw(highlight).line(
        [(hl_x, top), (hl_x, bottom)], fill=(255, 255, 255, 60), width=max(1, int(s * 0.006))
    )
    face = Image.alpha_composite(face, highlight)

    # page edge: a few thin cream lines near the right, fully opaque
    pd = ImageDraw.Draw(face)
    page_color = (247, 240, 220, 255)
    for frac in (0.10, 0.075, 0.05):
        x = right - width * frac
        pd.line(
            [(x, top + height * 0.07), (x, bottom - height * 0.07)],
            fill=page_color, width=max(1, int(s * 0.008)),
        )

    # mask the whole face to the rounded-rect book silhouette in one pass
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([left, top, right, bottom], radius=radius, fill=255)
    canvas.paste(face, (0, 0), mask)

    return canvas.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    largest = draw_book(256)
    largest.save(OUTPUT_PATH, sizes=[(s, s) for s in SIZES])
    print(f"Wrote {OUTPUT_PATH}")
