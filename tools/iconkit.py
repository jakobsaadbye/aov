"""
Iconkit: paints icons from flat drawings. An icon is drawn with the calls of PIL's ImageDraw (polygon, ellipse, line,
rectangle, arc, pieslice, text, ...) on a Canvas, which keeps each shape as a layer of its own instead of painting it at
once. When the icon is finished, each shape is painted like a raised, lit object: rounded at its edges by a bevel lit
from the top left, lighter at its top, with a shine, a little brush texture, and a soft shadow under it. The background
gets light from behind the symbol, a glow round it and darker corners. So the icons of make_textures.py and
make_icons.py, which are drawings of flat shapes, come out painted, without being drawn again.

    image, draw = canvas((90, 120, 160), (30, 40, 60))     # the background, from the top color to the bottom one
    draw.ellipse([60, 60, 196, 196], fill=(220, 60, 40), outline=(20, 20, 20), width=6)
    paint(draw).save("icon.png")
"""

import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

S = 256             # The size icons are drawn at
OUT = 128           # and saved at
LIGHT = np.array([-0.55, -0.65, 0.55])      # From the top left, towards the viewer (x right, y down, z out)
LIGHT = LIGHT / np.linalg.norm(LIGHT)
_rng = np.random.default_rng(5)


class Layer:
    def __init__(self, mask, color, kind):
        self.mask = mask            # 0..1 at S x S
        self.color = np.asarray(color[:3], dtype=float) / 255.0
        self.kind = kind            # "fill", "outline" or "line"


def _color(c):
    if c is None:
        return None
    if isinstance(c, str):
        from PIL import ImageColor
        return ImageColor.getrgb(c)
    if isinstance(c, (int, np.integer)):
        return (c, c, c)
    return tuple(int(v) for v in c[:3])


class Canvas:
    """Takes the drawing calls of ImageDraw, and keeps each shape as a layer"""

    def __init__(self, top, bottom):
        self.top, self.bottom = np.asarray(top, float) / 255, np.asarray(bottom, float) / 255
        self.layers = []
        self.image = Image.new("RGB", (S, S))

    def _shape(self, method, args, kwargs, fill_key="fill"):
        fill = _color(kwargs.pop(fill_key, None))
        outline = _color(kwargs.pop("outline", None))
        width = kwargs.pop("width", 1)
        line_like = method in ("line", "arc", "point")
        if line_like:
            if fill is None:
                return
            m = Image.new("L", (S, S), 0)
            getattr(ImageDraw.Draw(m), method)(*args, fill=255, width=width, **kwargs)
            self.layers.append(Layer(np.asarray(m, float) / 255, fill, "line"))
            return
        if fill is not None:
            m = Image.new("L", (S, S), 0)
            getattr(ImageDraw.Draw(m), method)(*args, fill=255, **kwargs)
            fm = np.asarray(m, float) / 255
        else:
            fm = None
        if outline is not None and width > 0:
            m = Image.new("L", (S, S), 0)
            getattr(ImageDraw.Draw(m), method)(*args, fill=None, outline=255, width=width, **kwargs)
            om = np.asarray(m, float) / 255
            # The outline goes under the fill, as a rim round it, so the fill keeps its full shape
            if fm is not None:
                rim = np.maximum(om, fm)
                self.layers.append(Layer(rim, outline, "outline"))
                self.layers.append(Layer(fm, fill, "fill"))
            else:
                self.layers.append(Layer(om, outline, "line"))
        elif fm is not None:
            self.layers.append(Layer(fm, fill, "fill"))

    def polygon(self, *a, **k): self._shape("polygon", a, k)
    def ellipse(self, *a, **k): self._shape("ellipse", a, k)
    def rectangle(self, *a, **k): self._shape("rectangle", a, k)
    def rounded_rectangle(self, *a, **k): self._shape("rounded_rectangle", a, k)
    def pieslice(self, *a, **k): self._shape("pieslice", a, k)
    def chord(self, *a, **k): self._shape("chord", a, k)
    def line(self, *a, **k): self._shape("line", a, k)
    def arc(self, *a, **k): self._shape("arc", a, k)
    def point(self, *a, **k): self._shape("point", a, k)
    def regular_polygon(self, *a, **k): self._shape("regular_polygon", a, k)

    def text(self, xy, text, fill=None, **k):
        if fill is None:
            return
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).text(xy, text, fill=255, **k)
        self.layers.append(Layer(np.asarray(m, float) / 255, _color(fill), "fill"))


def canvas(top, bottom):
    c = Canvas(top, bottom)
    return c.image, c


def _noise(scale, seed):
    """Smooth noise over the icon, about 0..1"""
    r = np.random.default_rng(seed)
    g = r.random((scale + 1, scale + 1))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), float) / 255


def _background(c):
    y, x = np.mgrid[0:S, 0:S] / (S - 1)
    t = y[..., None]
    base = c.top * (1 - t) + c.bottom * t
    # Light from behind the middle, a little up and left, and darker corners
    d = np.sqrt((x - 0.45) ** 2 + (y - 0.4) ** 2)
    glow = np.clip(1 - d / 0.7, 0, 1) ** 1.5
    vignette = np.clip((np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) - 0.35) / 0.4, 0, 1) ** 1.5
    strokes = _noise(6, 1) * 0.6 + _noise(18, 2) * 0.4
    out = base * (0.8 + 0.55 * glow[..., None] - 0.45 * vignette[..., None] + (strokes[..., None] - 0.5) * 0.12)
    # A little warmer where it is lit
    out += glow[..., None] * np.array([0.05, 0.03, 0.0])
    return np.clip(out, 0, 1)


def _shade(layer, seed):
    """The colors of a shape, lit like it is raised from the icon, and its alpha"""
    m = layer.mask
    inside = m > 0.5
    if not inside.any():
        return None, m
    ys, xs = np.nonzero(inside)
    size = max(ys.max() - ys.min(), xs.max() - xs.min(), 1)
    dist = ndimage.distance_transform_edt(inside)
    bevel = np.clip(size * 0.12, 3, 14) if layer.kind == "fill" else np.clip(dist.max(), 1.5, 8)
    h = np.clip(dist / bevel, 0, 1)
    h = np.sin(h * math.pi / 2)
    h = ndimage.gaussian_filter(h, 1.2)
    gy, gx = np.gradient(h * bevel * 0.9)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    lambert = np.clip(n @ LIGHT, 0, 1)
    half = LIGHT + np.array([0, 0, 1.0])
    half /= np.linalg.norm(half)
    spec = np.clip(n @ half, 0, 1) ** 40
    # Lighter at its top and darker at its bottom, over the whole shape
    y = np.arange(S)[:, None] * np.ones((1, S))
    top, bottom = ys.min(), ys.max()
    vert = np.clip((y - top) / max(bottom - top, 1), 0, 1)
    c = layer.color
    if layer.kind == "outline":
        k = 0.85 + 0.3 * lambert - 0.1 * vert
        col = c[None, None, :] * k[..., None]
        return np.clip(col, 0, 1), m
    k = 0.62 + 0.62 * lambert + 0.14 * (1 - vert) - 0.12 * vert
    texture = 1 + (_noise(10, seed) - 0.5) * 0.1 + (_noise(40, seed + 1) - 0.5) * 0.06
    col = c[None, None, :] * (k * texture)[..., None]
    # Warm light, cool shade
    col += (lambert[..., None] - 0.5) * np.array([0.04, 0.02, -0.03])
    col += spec[..., None] * 0.45 * (0.6 + 0.4 * c.mean())
    # A thin bright rim on the lit edge
    rim = (dist > 0.5) & (dist < 2.2) & (lambert > 0.6)
    col[rim] = col[rim] * 0.7 + 0.3
    return np.clip(col, 0, 1), m


def paint(c, frame=True):
    """The finished icon, at OUT x OUT"""
    out = _background(c)
    union = np.zeros((S, S))
    for layer in c.layers:
        union = np.maximum(union, layer.mask)
    # A glow round the symbol, lighter than the background behind it
    halo = ndimage.gaussian_filter(union, 14)
    halo = np.clip(halo * 1.3, 0, 1) * (1 - union)
    out = out + halo[..., None] * (out * 0.45 + 0.08)
    for i, layer in enumerate(c.layers):
        col, a = _shade(layer, 100 + i * 7)
        if col is None:
            continue
        # The soft shadow it casts, down and to the right
        sh = ndimage.shift(ndimage.gaussian_filter(a, 3.5), (5, 4), order=1)
        out = out * (1 - 0.42 * sh[..., None])
        out = out * (1 - a[..., None]) + col * a[..., None]
    img = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    image = Image.fromarray(img, "RGB")
    if frame:
        d = ImageDraw.Draw(image)
        d.rectangle([0, 0, S - 1, S - 1], outline=(18, 14, 10), width=8)
        d.rectangle([8, 8, S - 9, S - 9], outline=(190, 160, 95), width=3)
        d.rectangle([11, 11, S - 12, S - 12], outline=(70, 52, 28), width=2)
    return image.resize((OUT, OUT), Image.LANCZOS)
