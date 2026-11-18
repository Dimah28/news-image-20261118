#!/usr/bin/env python3
"""news-image-20261118 — "The world in one picture: Wednesday 18 November 2026".

A newspaper front page drawn entirely procedurally with the Python 3.13
standard library only: a hand-rolled 5x7 bitmap font, a small vector
drawing layer, and a hand-encoded PNG (zlib). No network, no files read,
no randomness, no clock — two runs write byte-identical files.

Layout (1024x1024), 28 stories, 6 continents:
  masthead -> one hero story (the three summits) -> six illustrated
  stories in a 3x2 grid -> dotted world map with numbered pins beside
  "ALSO ON" list of 21 more stories -> sources footer.
Every story below happened, or was first reported, on Wednesday
18 November 2026; disputed claims are labelled as claims.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (28, 26, 22)
TEAL = (14, 58, 58)        # masthead band
TEAL_DK = (9, 40, 40)
GOLD = (200, 134, 26)
GOLD_LT = (232, 196, 110)
BRICK = (166, 58, 42)      # kickers, number badges
BRICK_DK = (130, 44, 30)
CREAM = (250, 246, 236)
CARD = (255, 253, 247)
LINE = (28, 26, 22)
MUTED = (96, 90, 78)
SEA = (46, 92, 110)
SKY = (126, 170, 196)
SAND = (214, 186, 140)
SAGE = (122, 140, 110)
RUST = (178, 92, 52)
SLATE = (84, 98, 110)
MAPDOT = (90, 104, 96)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ---------------------------------------------------------------- PNG out
def encode_png(w, h, px):
    """px: bytes of RGB rows, top to bottom. Returns whole PNG bytes."""
    raw = b"".join(b"\x00" + px[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def _i(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._i(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._i(x0, yy)
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c):
        self.fill(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill(x, y, 1, h, c)

    def rect(self, x, y, w, h, c, lw=1):
        self.fill(x, y, w, lw, c)
        self.fill(x, y + h - lw, w, lw, c)
        self.fill(x, y, lw, h, c)
        self.fill(x + w - lw, y, lw, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, filled=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d <= r * r:
                        self.set(xx, yy, c)
                elif r * r - 2 * r <= d <= r * r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[j]), int(xs[j + 1])
                self.fill(xa, y, xb - xa + 1, 1, c)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = ink. Written for this entry.
FONT = {
'A': ("01110","10001","10001","11111","10001","10001","10001"),
'B': ("11110","10001","10001","11110","10001","10001","11110"),
'C': ("01110","10001","10000","10000","10000","10001","01110"),
'D': ("11110","10001","10001","10001","10001","10001","11110"),
'E': ("11111","10000","10000","11110","10000","10000","11111"),
'F': ("11111","10000","10000","11110","10000","10000","10000"),
'G': ("01110","10001","10000","10111","10001","10001","01111"),
'H': ("10001","10001","10001","11111","10001","10001","10001"),
'I': ("01110","00100","00100","00100","00100","00100","01110"),
'J': ("00111","00010","00010","00010","00010","10010","01100"),
'K': ("10001","10010","10100","11000","10100","10010","10001"),
'L': ("10000","10000","10000","10000","10000","10000","11111"),
'M': ("10001","11011","10101","10101","10001","10001","10001"),
'N': ("10001","11001","10101","10011","10001","10001","10001"),
'O': ("01110","10001","10001","10001","10001","10001","01110"),
'P': ("11110","10001","10001","11110","10000","10000","10000"),
'Q': ("01110","10001","10001","10001","10101","10010","01101"),
'R': ("11110","10001","10001","11110","10100","10010","10001"),
'S': ("01111","10000","10000","01110","00001","00001","11110"),
'T': ("11111","00100","00100","00100","00100","00100","00100"),
'U': ("10001","10001","10001","10001","10001","10001","01110"),
'V': ("10001","10001","10001","10001","10001","01010","00100"),
'W': ("10001","10001","10001","10101","10101","11011","10001"),
'X': ("10001","10001","01010","00100","01010","10001","10001"),
'Y': ("10001","10001","01010","00100","00100","00100","00100"),
'Z': ("11111","00001","00010","00100","01000","10000","11111"),
'0': ("01110","10001","10011","10101","11001","10001","01110"),
'1': ("00100","01100","00100","00100","00100","00100","01110"),
'2': ("01110","10001","00001","00110","01000","10000","11111"),
'3': ("11111","00010","00100","00010","00001","10001","01110"),
'4': ("00010","00110","01010","10010","11111","00010","00010"),
'5': ("11111","10000","11110","00001","00001","10001","01110"),
'6': ("00110","01000","10000","11110","10001","10001","01110"),
'7': ("11111","00001","00010","00100","01000","01000","01000"),
'8': ("01110","10001","10001","01110","10001","10001","01110"),
'9': ("01110","10001","10001","01111","00001","00010","01100"),
'a': ("00000","00000","01110","00001","01111","10001","01111"),
'b': ("10000","10000","11110","10001","10001","10001","11110"),
'c': ("00000","00000","01110","10001","10000","10001","01110"),
'd': ("00001","00001","01111","10001","10001","10001","01111"),
'e': ("00000","00000","01110","10001","11111","10000","01110"),
'f': ("00110","01001","01000","11110","01000","01000","01000"),
'g': ("00000","00000","01111","10001","10001","01111","01110"),
'h': ("10000","10000","11110","10001","10001","10001","10001"),
'i': ("00100","00000","01100","00100","00100","00100","01110"),
'j': ("00010","00000","00110","00010","00010","10010","01100"),
'k': ("10000","10000","10010","10100","11000","10100","10010"),
'l': ("01100","00100","00100","00100","00100","00100","01110"),
'm': ("00000","00000","11010","10101","10101","10101","10101"),
'n': ("00000","00000","11110","10001","10001","10001","10001"),
'o': ("00000","00000","01110","10001","10001","10001","01110"),
'p': ("00000","00000","11110","10001","10001","11110","10000"),
'q': ("00000","00000","01111","10001","10001","01111","00001"),
'r': ("00000","00000","10110","11001","10000","10000","10000"),
's': ("00000","00000","01111","10000","01110","00001","11110"),
't': ("01000","01000","11110","01000","01000","01000","00110"),
'u': ("00000","00000","10001","10001","10001","10001","01111"),
'v': ("00000","00000","10001","10001","10001","01010","00100"),
'w': ("00000","00000","10001","10101","10101","10101","01010"),
'x': ("00000","00000","10001","01010","00100","01010","10001"),
'y': ("00000","00000","10001","10001","10001","01111","01110"),
'z': ("00000","00000","11111","00010","00100","01000","11111"),
' ': ("00000","00000","00000","00000","00000","00000","00000"),
'.': ("00000","00000","00000","00000","00000","01100","01100"),
',': ("00000","00000","00000","00000","01100","00100","01000"),
':': ("00000","01100","01100","00000","01100","01100","00000"),
';': ("00000","01100","01100","00000","01100","00100","01000"),
'!': ("00100","00100","00100","00100","00100","00000","00100"),
'?': ("01110","10001","00001","00110","00100","00000","00100"),
'-': ("00000","00000","00000","01110","00000","00000","00000"),
'\u2013': ("00000","00000","00000","01110","00000","00000","00000"),
'\u2014': ("00000","00000","00000","11111","00000","00000","00000"),
"'": ("00100","00100","01000","00000","00000","00000","00000"),
'\u2019': ("00100","00100","01000","00000","00000","00000","00000"),
'"': ("01010","01010","01010","00000","00000","00000","00000"),
'(': ("00010","00100","01000","01000","01000","00100","00010"),
')': ("01000","00100","00010","00010","00010","00100","01000"),
'/': ("00001","00010","00010","00100","01000","01000","10000"),
'%': ("11001","11010","00010","00100","01000","01011","10011"),
'$': ("00100","01111","10100","01110","00101","11110","00100"),
'&': ("01100","10010","10100","01000","10101","10010","01101"),
'\u00b7': ("00000","00000","00000","01100","01100","00000","00000"),
'\u2022': ("00000","01110","11111","11111","01110","00000","00000"),
'+': ("00000","00100","00100","11111","00100","00100","00000"),
'\u00d7': ("00000","10001","01010","00100","01010","10001","00000"),
'=': ("00000","00000","11111","00000","11111","00000","00000"),
'*': ("00000","00100","10101","01110","10101","00100","00000"),
'>': ("10000","01000","00100","00010","00100","01000","10000"),
'<': ("00001","00010","00100","01000","00100","00010","00001"),
'#': ("01010","01010","11111","01010","11111","01010","01010"),
}

def text_w(s, scale, spacing=1):
    return len(s) * (5 * scale + spacing) - spacing

def draw_text(cv, x, y, s, scale, color, bold=False, spacing=1):
    """Draw string s with top-left at (x, y). Returns width used."""
    cx = x
    adv = 5 * scale + spacing
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '1':
                    cv.fill(cx + c * scale, y + r * scale, scale, scale, color)
                    if bold:
                        cv.fill(cx + c * scale + 1, y + r * scale, scale, scale, color)
        cx += adv
    return cx - x - spacing if s else 0

def wrap(s, width, scale, spacing=1, bold=False):
    """Greedy word wrap; returns list of lines fitting width px."""
    adv = 5 * scale + spacing
    max_chars = max(1, (width + spacing) // adv)
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            cur = word
    if cur:
        lines.append(cur)
    return lines

def draw_para(cv, x, y, lines, scale, color, lh=None, bold=False, spacing=1):
    lh = lh if lh is not None else 8 * scale + 2
    for ln in lines:
        draw_text(cv, x, y, ln, scale, color, bold=bold, spacing=spacing)
        y += lh
    return y

# ---------------------------------------------------------------- world map
# Land as ellipses on a 46x29 grid (lon -180..180, lat 75..-60).
LAND = [
    (11, 7, 9, 4.5), (5, 5, 3, 2), (15, 13, 2.5, 2),      # N America
    (20, 3, 2, 1.8),                                        # Greenland
    (17, 20, 3, 5.5), (18, 25, 1.8, 2.5),                   # S America
    (32, 17, 5.5, 6.5), (32, 11, 3, 2.5),                   # Africa
    (32, 7, 4.5, 2.5), (29, 5.5, 1, 1.2), (33, 4, 2, 1.5),  # Europe
    (45, 7, 11, 4.5), (48, 4, 9, 2.5),                      # Asia
    (41, 13, 2, 3), (48, 14, 2.5, 2), (36, 11, 2.5, 2),     # India, SE Asia, Mideast
    (50, 17, 4, 1), (54, 17, 2, 1),                         # Indonesia
    (52, 23, 3.5, 2.5),                                     # Australia
    (56, 10, 1, 2), (58, 26, 1, 1.5),                       # Japan, NZ
]

def _land(c, r):
    for cx, cy, rx, ry in LAND:
        if ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2 <= 1:
            return True
    return False

def draw_map(cv, x, y, cols=46, rows=29, step=10):
    for r in range(rows):
        for c in range(cols):
            if _land(c, r):
                cv.fill(x + c * step + 3, y + r * step + 3, 3, 3, MAPDOT)

def pin_xy(x, y, lon, lat, cols=46, rows=29, step=10):
    c = (lon + 180.0) / 360.0 * cols
    r = (75.0 - lat) / 135.0 * rows
    return int(x + c * step + 4), int(y + r * step + 4)

def draw_pin(cv, px, py, n):
    cv.circle(px, py, 8, BRICK)
    cv.circle(px, py, 8, BRICK_DK, filled=False)
    s = str(n)
    tw = text_w(s, 1)
    draw_text(cv, px - tw // 2, py - 3, s, 1, WHITE, bold=True)

# ---------------------------------------------------------------- illustrations
def draw_skyline(cv, x, y, w, h):
    """Dusk skyline over water, three summit flags — the hero art."""
    cv.fill(x, y, w, h, (56, 102, 118))
    cv.fill(x, y + h // 2, w, h - h // 2, (34, 68, 86))
    cv.circle(x + w - 52, y + 26, 15, (232, 196, 110))
    base = y + h - 26
    sil = [(0, 46), (18, 46), (18, 30), (34, 30), (34, 52), (52, 52), (52, 18),
           (66, 18), (66, 52), (86, 52), (86, 34), (100, 34), (100, 52),
           (120, 52), (120, 24), (132, 24), (132, 8), (140, 8), (140, 52),
           (160, 52), (160, 38), (176, 38), (176, 52), (196, 52), (196, 28),
           (212, 28), (212, 52), (232, 52), (232, 40), (246, 40), (246, 52),
           (264, 52), (264, 30), (280, 30), (280, 52), (300, 52), (300, 46)]
    pts = [(x + px, base - ph) for px, ph in sil]
    pts += [(x + w, base), (x, base)]
    cv.poly(pts, (8, 22, 28))
    for wx, wy in ((58, 34), (90, 44), (126, 40), (146, 20), (202, 42),
                   (238, 48), (270, 42), (72, 28), (166, 46)):
        cv.fill(x + wx, base - wy, 3, 3, GOLD_LT)
    for fx, fc in ((w - 100, (178, 58, 52)), (w - 66, (232, 196, 110)),
                   (w - 32, (46, 92, 140))):
        cv.vline(x + fx, y + 8, 34, (240, 236, 224))
        cv.fill(x + fx + 1, y + 8, 20, 13, fc)
    for wy in range(3):
        yy = base + 6 + wy * 7
        cv.hline(x + 12, yy, w - 24, (52, 96, 108))
        cv.hline(x + 12, yy + 3, w - 40, (38, 76, 90))

def draw_bridge(cv, x, y, w, h):
    cv.fill(x, y, w, h, SKY)
    cv.fill(x, y + h * 2 // 3, w, h // 3, SEA)
    cv.circle(x + w - 22, y + 14, 9, GOLD_LT)
    mid = x + w // 2
    cv.line(x + 6, y + h // 2, mid - 26, y + h // 2, WHITE)
    cv.line(mid + 26, y + h // 2, x + w - 6, y + h // 2, WHITE)
    cv.line(mid - 26, y + h // 2, mid - 8, y + h // 2 + 12, WHITE)
    cv.line(mid + 26, y + h // 2, mid + 8, y + h // 2 + 12, WHITE)
    for i in range(4):
        cv.line(x + 14 + i * 16, y + h // 2, x + 14 + i * 16, y + h // 2 - 12, WHITE)
        cv.line(x + w - 14 - i * 16, y + h // 2, x + w - 14 - i * 16, y + h // 2 - 12, WHITE)
    cv.poly([(mid - 30, y + h // 2), (mid, y + h // 2 - 22), (mid + 30, y + h // 2)], (70, 84, 96))
    cv.fill(mid - 3, y + h // 2 - 26, 6, 8, (70, 84, 96))
    cv.circle(mid - 10, y + h // 2 - 24, 4, (120, 120, 118))
    cv.circle(mid + 6, y + h // 2 - 30, 5, (140, 140, 136))

def draw_jet(cv, x, y, w, h):
    cv.fill(x, y, w, h, (16, 28, 44))
    for sx, sy in ((12, 8), (40, 20), (70, 6), (96, 16), (30, 34), (84, 30)):
        cv.fill(x + sx, y + sy, 2, 2, WHITE)
    cv.poly([(x + 14, y + 30), (x + 52, y + 22), (x + 58, y + 26),
             (x + 44, y + 30), (x + 30, y + 36), (x + 16, y + 34)], (200, 200, 196))
    cv.fill(x + 56, y + 24, 6, 2, GOLD_LT)
    cv.circle(x + w - 26, y + h - 18, 10, (90, 110, 126), filled=False)
    cv.line(x + w - 26, y + h - 18, x + w - 12, y + h - 30, (160, 170, 180))
    cv.fill(x + w - 46, y + 12, 3, 3, BRICK)
    cv.fill(x + w - 60, y + 20, 3, 3, BRICK)
    cv.line(x + w - 46, y + 12, x + w - 58, y + 22, BRICK)

def draw_palace(cv, x, y, w, h):
    cv.fill(x, y, w, h, (214, 186, 140))
    cv.fill(x, y + h - 16, w, 16, (122, 96, 66))
    cx = x + w // 2
    cv.poly([(cx - 52, y + 40), (cx + 52, y + 40), (cx + 40, y + 28), (cx - 40, y + 28)], BRICK_DK)
    cv.poly([(cx - 38, y + 28), (cx + 38, y + 28), (cx + 28, y + 18), (cx - 28, y + 18)], BRICK)
    cv.fill(cx - 24, y + 40, 48, 12, (240, 236, 224))
    for i in range(5):
        cv.fill(cx - 20 + i * 10, y + 40, 3, 12, (90, 70, 50))
    cv.vline(cx, y + 4, 14, (60, 50, 40))
    cv.fill(cx + 1, y + 4, 12, 8, (178, 58, 52))
    cv.fill(x + 8, y + h - 26, 14, 10, SAGE)
    cv.fill(x + w - 22, y + h - 26, 14, 10, SAGE)

def draw_missile(cv, x, y, w, h):
    cv.fill(x, y, w, h, (14, 24, 44))
    cv.fill(x, y + h * 3 // 4, w, h // 4, (20, 44, 62))
    cv.circle(x + 18, y + 12, 8, (232, 220, 190))
    pts = [(x + 16, y + h - 8), (x + 30, y + h - 20), (x + 48, y + h - 30),
           (x + 66, y + h - 34), (x + 82, y + h - 32)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GOLD_LT)
    mx, my = pts[-1]
    cv.poly([(mx, my - 8), (mx + 14, my - 2), (mx, my + 4)], (220, 220, 216))
    cv.circle(mx - 2, my - 2, 3, (232, 150, 60))
    cv.fill(x + 8, y + h - 12, 40, 3, (90, 120, 150))
    cv.fill(x + w - 52, y + h - 10, 44, 3, (90, 120, 150))

def draw_quake(cv, x, y, w, h):
    cv.fill(x, y, w, h, (196, 188, 168))
    cv.fill(x, y + 8, 26, 30, (120, 110, 96))
    cv.fill(x + 34, y + 16, 22, 22, (140, 128, 110))
    cv.poly([(x + 60, y + 38), (x + 78, y + 12), (x + 96, y + 38)], (150, 138, 118))
    cv.fill(x, y + h - 18, w, 18, (96, 84, 70))
    cv.line(x + 4, y + h - 18, x + 22, y + h - 6, BLACK)
    cv.line(x + 22, y + h - 6, x + 40, y + h - 16, BLACK)
    pts = [(x + 4, y + 46), (x + 14, y + 46), (x + 20, y + 38), (x + 26, y + 54),
           (x + 32, y + 40), (x + 38, y + 52), (x + 44, y + 46), (x + 52, y + 46),
           (x + 58, y + 36), (x + 64, y + 56), (x + 70, y + 44), (x + 78, y + 46),
           (x + 88, y + 46), (x + 94, y + 38), (x + 100, y + 52), (x + 106, y + 46)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], BRICK)

def draw_crowd(cv, x, y, w, h):
    cv.fill(x, y, w, h, (196, 176, 148))
    cv.fill(x, y + h - 22, w, 22, (150, 126, 96))
    for i in range(9):
        hx = x + 8 + i * 12
        cv.circle(hx + 4, y + h - 30, 4, (70, 56, 44))
        cv.fill(hx, y + h - 26, 9, 8, (90 + (i % 3) * 30, 70, 80))
    cv.fill(x + 14, y + 10, 34, 12, (240, 236, 224))
    cv.fill(x + 14, y + 10, 34, 3, BRICK)
    cv.fill(x + w - 52, y + 16, 38, 12, GOLD_LT)
    cv.line(x + 16, y + 22, x + 16, y + 34, (60, 50, 40))
    cv.line(x + w - 50, y + 28, x + w - 50, y + 40, (60, 50, 40))

# ---------------------------------------------------------------- stories
# All first reported on Wednesday 18 November 2026 (AP, Reuters, AFP,
# BBC, Al Jazeera, UN News and the day's wires). Disputed claims are
# worded as claims, never as fact.
HERO = {
    "kicker": "ASIA \u00b7 SUMMITS",
    "headline": "Three summits, one day in Asia",
    "body": ("APEC opens in Shenzhen as 21 leaders gather. Trump lands in "
             "Manila for the Quad, then flies on to China \u2014 where the "
             "first-ever Trump\u2013Xi\u2013Putin meeting is set for Thursday."),
    "pin": (114.0, 22.5),
}

GRID = [
    {"n": 2, "kicker": "EUROPE \u00b7 WAR",
     "headline": "Ukraine drops a second span of the Crimea bridge",
     "body": "A second day of strikes drops the arch; Russia hits Kyiv.",
     "pin": (38.5, 45.3), "art": draw_bridge},
    {"n": 3, "kicker": "MIDDLE EAST \u00b7 WAR",
     "headline": "US and Iran trade fire over Bahrain",
     "body": "Iranian drones hit a US radar; US jets strike a site on Qeshm.",
     "pin": (50.6, 26.2), "art": draw_jet},
    {"n": 4, "kicker": "ASIA \u00b7 POLITICS",
     "headline": "Mongolia\u2019s president quits in $25m scandal",
     "body": "Khurelsukh quits over a $25m claim he denies; MPs must confirm.",
     "pin": (106.9, 47.9), "art": draw_palace},
    {"n": 5, "kicker": "ASIA \u00b7 SECURITY",
     "headline": "North Korea fires a missile into the sea",
     "body": "A ballistic missile flies to the Sea of Japan as tensions rise.",
     "pin": (127.5, 39.0), "art": draw_missile},
    {"n": 6, "kicker": "EUROPE \u00b7 DISASTER",
     "headline": "5.3 quake shakes Romania",
     "body": "A magnitude 5.3 tremor strikes at night, felt across the region.",
     "pin": (25.0, 45.8), "art": draw_quake},
    {"n": 7, "kicker": "EUROPE \u00b7 PROTEST",
     "headline": "146,000 march in France over living costs",
     "body": "Unions strike over living costs; police clash with protesters.",
     "pin": (2.35, 48.85), "art": draw_crowd},
]

ALSO = [
    (8, "BRITAIN", "Sanctions on eight settlement builders"),
    (9, "CANADA", "China cuts tariffs as Xi meets Carney"),
    (10, "JAPAN", "Jets scrambled as Russian planes enter airspace"),
    (11, "INDIA", "Cyclone Akvan bears down on Andhra Pradesh"),
    (12, "INDIA", "Dhoni ends his IPL playing career"),
    (13, "INDIA", "India beat Pakistan 2-1 for a 10th SAFF title"),
    (14, "GAZA", "Board of Peace warns the ceasefire may collapse"),
    (15, "UKRAINE", "UN: 372 civilians killed in October"),
    (16, "RUSSIA", "An-12 crashes in Siberia; 19 dead"),
    (17, "GENEVA", "UN calls for a treaty on autonomous weapons"),
    (18, "SPACE", "Voyager 1 nears one light-day from Earth"),
    (19, "FILM", "Pattinson named the next James Bond"),
    (20, "MARKETS", "Nvidia in focus as Huang eyes CEO return"),
    (21, "ISRAEL", "Knesset elects Kahana as speaker"),
    (22, "USA", "Measles cases hit a 40-year high"),
    (23, "AUSTRALIA", "Fresh sanctions on Israeli settlements"),
    (24, "KUWAIT", "Army reports drone interceptions"),
    (25, "THAILAND", "US and Thailand reach a trade deal"),
    (26, "GERMANY", "New drone regiment for the Bundeswehr"),
    (27, "LATVIA", "Parliament approves a new cabinet"),
    (28, "KOREA", "IMF raises growth forecast to 3.9%"),
]

# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)

    # masthead
    cv.fill(0, 0, W, 112, TEAL)
    cv.fill(0, 108, W, 4, TEAL_DK)
    draw_text(cv, 24, 14, "THE WORLD IN ONE PICTURE", 2, GOLD_LT, bold=True)
    right = "28 STORIES \u00b7 6 CONTINENTS \u00b7 ONE PAGE"
    draw_text(cv, W - 24 - text_w(right, 2), 14, right, 2, GOLD_LT, bold=True)
    title = "WEDNESDAY 18 NOVEMBER 2026"
    draw_text(cv, (W - text_w(title, 5, spacing=2)) // 2, 40, title, 5, WHITE, spacing=2)
    sub = "Every story below happened, or was first reported, on this day."
    draw_text(cv, (W - text_w(sub, 2)) // 2, 88, sub, 2, (200, 210, 205))
    cv.fill(0, 112, W, 4, GOLD)

    # hero
    hx, hy, hw, hh = 24, 124, 976, 132
    cv.fill(hx, hy, hw, hh, CARD)
    cv.rect(hx, hy, hw, hh, INK, lw=2)
    draw_skyline(cv, hx + 2, hy + 2, 300, hh - 4)
    cv.vline(hx + 304, hy + 2, hh - 4, INK)
    tx = hx + 320
    cv.circle(tx + 10, hy + 22, 10, BRICK)
    draw_text(cv, tx + 6, hy + 19, "1", 1, WHITE, bold=True)
    draw_text(cv, tx + 26, hy + 15, HERO["kicker"], 2, BRICK, bold=True)
    hl = wrap(HERO["headline"], 640, 3, bold=True)
    draw_para(cv, tx, hy + 38, hl, 3, INK, lh=22, bold=True)
    body = wrap(HERO["body"], 640, 2)
    draw_para(cv, tx, hy + 76, body, 2, (48, 44, 38), lh=17)

    # grid of six
    gw, gh, gap = 318, 176, 11
    for i, s in enumerate(GRID):
        gx = 24 + (i % 3) * (gw + gap)
        gy = 268 + (i // 3) * (gh + 8)
        cv.fill(gx, gy, gw, gh, CARD)
        cv.rect(gx, gy, gw, gh, INK, lw=1)
        s["art"](cv, gx + 2, gy + 2, gw - 4, 54)
        cv.hline(gx + 2, gy + 56, gw - 4, INK)
        cv.circle(gx + 15, gy + 73, 9, BRICK)
        draw_text(cv, gx + 12, gy + 70, str(s["n"]), 1, WHITE, bold=True)
        draw_text(cv, gx + 30, gy + 66, s["kicker"], 2, BRICK, bold=True)
        hl = wrap(s["headline"], gw - 28, 2, bold=True)[:2]
        draw_para(cv, gx + 14, gy + 88, hl, 2, INK, lh=18, bold=True)
        bl = wrap(s["body"], gw - 28, 2)[:3]
        draw_para(cv, gx + 14, gy + 126, bl, 2, (48, 44, 38), lh=16)

    # bottom band: map + also list
    by = 640
    cv.fill(24, by, 460, 328, CARD)
    cv.rect(24, by, 460, 328, INK, lw=1)
    draw_text(cv, 36, by + 12, "WHERE IT HAPPENED", 2, INK, bold=True)
    draw_text(cv, 36, by + 30, "Numbered dots mark stories 1\u20137.", 1, MUTED)
    draw_map(cv, 24, by + 52)
    pins = [(1, HERO["pin"])] + [(s["n"], s["pin"]) for s in GRID]
    for n, (lon, lat) in pins:
        px, py = pin_xy(24, by + 52, lon, lat)
        draw_pin(cv, px, py, n)

    cv.fill(496, by, 504, 328, CARD)
    cv.rect(496, by, 504, 328, INK, lw=1)
    draw_text(cv, 508, by + 12, "ALSO ON 18 NOVEMBER \u2014 21 MORE STORIES",
              2, INK, bold=True)
    cols = [ALSO[:11], ALSO[11:]]
    for ci, items in enumerate(cols):
        cx = 508 + ci * 252
        yy = by + 44
        for n, place, text in items:
            lines = wrap("%d. %s \u2014 %s" % (n, place, text), 242, 1, bold=True)[:2]
            yy = draw_para(cv, cx, yy, lines, 1, (48, 44, 38), lh=11, bold=True)
            yy += 4

    # footer
    cv.fill(24, 976, 976, 2, INK)
    foot = ("Sources: AP \u00b7 Reuters \u00b7 AFP \u00b7 BBC \u00b7 Al Jazeera \u00b7 UN News. "
            "Original drawings. Every story was reported on Wednesday 18 November 2026; "
            "disputed claims are attributed.")
    draw_text(cv, 24, 986, foot, 1, MUTED)
    draw_text(cv, 24, 1000, "The world in one picture \u2014 28 stories from "
              "Wednesday 18 November 2026.", 1, MUTED)
    return cv

def main():
    cv = build()
    data = encode_png(W, H, bytes(cv.px))
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "entry.png"), "wb") as f:
        f.write(data)
    import hashlib
    print("entry.png %d bytes sha256=%s" % (len(data), hashlib.sha256(data).hexdigest()))

if __name__ == "__main__":
    main()
