#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws one 1024x1024 PNG: an open passport spread of the Republic of
Vessalia, a small maritime trading republic whose capital is Port Serein.

Everything on the document agrees with everything else:

  holder        Ana Sorin Velmar, born 12 MAY 1991 in Port Serein
  passport no.  V4820917, issued 14 MAR 2022 in Port Serein,
                expires 13 MAR 2032
  travel        Vessalia -> Kordavia, 03 JUN 2023 to 18 JUN 2023
                Ostmark, 27 OCT 2024 to 02 NOV 2024
  machine-readable zone encodes the same name, number, birth date,
                sex and expiry, with proper ICAO 7-3-1 check digits.

Python 3.13 standard library only. The PNG is written with a small
hand-rolled encoder (zlib + struct) and all lettering uses one built-in
5x7 bitmap font, so the whole document holds together typographically.
Output: /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
Deterministic: no clock, no network, no randomness.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
DESK      = (58, 62, 70)      # desk the passport lies on
DESK_DARK = (44, 47, 54)
PAGE      = (246, 241, 227)   # page stock
PAGE_EDGE = (203, 191, 158)
PATTERN   = (233, 224, 198)   # faint security pattern on the page
INK       = (38, 44, 58)      # printed text ink
LABEL     = (122, 118, 104)   # field labels
RULE      = (178, 168, 140)   # thin section rules
HEADER    = (30, 52, 84)      # country header blue
BLUE_INK  = (52, 84, 138)     # stamp ink, muted blue
RED_INK   = (158, 56, 48)     # stamp ink, muted red
GREEN_INK = (46, 104, 74)     # fee stamp ink
PHOTO_BG  = (219, 224, 226)
SKIN      = (206, 164, 128)
HAIR      = (74, 56, 44)
JACKET    = (90, 74, 84)
BLOUSE    = (232, 228, 218)

# ------------------------------------------------------------------- data
SURNAME      = "VELMAR"
GIVEN_NAMES  = "ANA SORIN"
NATIONALITY  = "VESSALIAN"
DOC_TYPE     = "P"
DOC_CODE     = "VES"
PASSPORT_NO  = "V4820917"
DOB_PRINT    = "12 MAY 1991"
DOB_MRZ      = "910512"
SEX          = "F"
BIRTH_PLACE  = "PORT SEREIN"
ISSUE_PRINT  = "14 MAR 2022"
EXPIRY_PRINT = "13 MAR 2032"
EXPIRY_MRZ   = "320313"
AUTHORITY    = "PREFECTURE OF PORT SEREIN"

# ------------------------------------------------------------- PNG encoder
def encode_png(pix, w, h):
    """pix: bytearray of w*h*3 RGB bytes. Returns PNG file bytes."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += pix[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))

# ----------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, colour):
        self.w, self.h = w, h
        self.pix = bytearray(colour) * (w * h)
        self.clip = None  # optional (x0, y0, x1, y1) drawing clip

    def px(self, x, y, colour, alpha=1.0):
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                return
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            if alpha >= 1.0:
                self.pix[i:i + 3] = bytes(colour)
            else:
                for k in range(3):
                    self.pix[i + k] = int(self.pix[i + k] * (1 - alpha)
                                          + colour[k] * alpha)

    def fill_rect(self, x0, y0, x1, y1, colour, alpha=1.0):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px(x, y, colour, alpha)

    def hline(self, x0, x1, y, colour, thick=1, alpha=1.0):
        for t in range(thick):
            for x in range(x0, x1 + 1):
                self.px(x, y + t, colour, alpha)

    def vline(self, x, y0, y1, colour, thick=1, alpha=1.0):
        for t in range(thick):
            for y in range(y0, y1 + 1):
                self.px(x + t, y, colour, alpha)

    def rect(self, x0, y0, x1, y1, colour, thick=1, alpha=1.0):
        self.hline(x0, x1, y0, colour, thick, alpha)
        self.hline(x0, x1, y1 - thick + 1, colour, thick, alpha)
        self.vline(x0, y0, y1, colour, thick, alpha)
        self.vline(x1 - thick + 1, y0, y1, colour, thick, alpha)

    def line(self, x0, y0, x1, y1, colour, thick=1, alpha=1.0):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = x0 + dx * i // steps
            y = y0 + dy * i // steps
            for tx in range(thick):
                for ty in range(thick):
                    self.px(x + tx, y + ty, colour, alpha)

    def circle(self, cx, cy, r, colour, thick=1, alpha=1.0):
        for a in range(720):
            t = a * math.pi / 360.0
            for rr in range(r - thick + 1, r + 1):
                self.px(int(cx + rr * math.cos(t)),
                        int(cy + rr * math.sin(t)), colour, alpha)

    def fill_ellipse(self, cx, cy, rx, ry, colour, alpha=1.0):
        for y in range(cy - ry, cy + ry + 1):
            span = int(rx * math.sqrt(max(0.0, 1 - ((y - cy) / ry) ** 2)))
            for x in range(cx - span, cx + span + 1):
                self.px(x, y, colour, alpha)

# ------------------------------------------------------------- bitmap font
# One 5x7 font for the whole document: headers, fields, stamps, MRZ.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    'Y': ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10001", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
}

def text_width(s, scale, spacing=1):
    if not s:
        return 0
    return len(s) * (5 + spacing) * scale - spacing * scale

def draw_text(cv, x, y, s, scale, colour, spacing=1, alpha=1.0, bold=False):
    """Draw string s with the 5x7 font; returns the x just past the text."""
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        wide = scale * 2 if bold else scale  # bold = doubled stroke width
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '1':
                    for dx in range(wide):
                        for dy in range(scale):
                            cv.px(cx + col * scale + dx,
                                  y + row * scale + dy, colour, alpha)
        cx += (5 + spacing) * scale
    return cx

def draw_text_centered(cv, cx, y, s, scale, colour, spacing=1, alpha=1.0,
                       bold=False):
    x = cx - text_width(s, scale, spacing) // 2
    return draw_text(cv, x, y, s, scale, colour, spacing, alpha, bold)

# ------------------------------------------------------------ page layout
LEFT_X0, LEFT_X1 = 28, 500        # data page
RIGHT_X0, RIGHT_X1 = 524, 996     # visas page
PAGE_Y0, PAGE_Y1 = 52, 972

def draw_spread(cv):
    """Desk, page shadows, the two pages, spine shadow, security pattern."""
    cv.fill_rect(0, 0, W, H, DESK)
    # gentle vertical shading on the desk
    for y in range(H):
        shade = DESK_DARK if y > H * 3 // 4 else DESK
        if y % 3 == 0:
            cv.hline(0, W - 1, y, shade)
    # drop shadows under the pages
    cv.fill_rect(LEFT_X0 + 8, PAGE_Y0 + 10, RIGHT_X1 + 8, PAGE_Y1 + 10,
                 (30, 32, 38))
    # the two pages
    cv.fill_rect(LEFT_X0, PAGE_Y0, LEFT_X1, PAGE_Y1, PAGE)
    cv.fill_rect(RIGHT_X0, PAGE_Y0, RIGHT_X1, PAGE_Y1, PAGE)
    # faint diagonal security pattern, clipped to each page
    for (x0, x1) in ((LEFT_X0, LEFT_X1), (RIGHT_X0, RIGHT_X1)):
        for d in range(-PAGE_Y1, x1 - x0, 16):
            for t in range(0, PAGE_Y1 - PAGE_Y0, 4):
                x = x0 + d + t
                y = PAGE_Y0 + t
                if x0 + 3 <= x < x1 - 3:
                    cv.px(x, y, PATTERN)
                    cv.px(x + 1, y, PATTERN)
    # page edges
    cv.rect(LEFT_X0, PAGE_Y0, LEFT_X1, PAGE_Y1, PAGE_EDGE, 2)
    cv.rect(RIGHT_X0, PAGE_Y0, RIGHT_X1, PAGE_Y1, PAGE_EDGE, 2)
    # centre spine: shadow falling on both pages near the fold
    for i, x in enumerate(range(LEFT_X1 - 16, LEFT_X1)):
        cv.vline(x, PAGE_Y0 + 2, PAGE_Y1 - 2, (214, 205, 178),
                 alpha=0.10 + 0.05 * i)
    for i, x in enumerate(range(RIGHT_X0, RIGHT_X0 + 16)):
        cv.vline(x, PAGE_Y0 + 2, PAGE_Y1 - 2, (214, 205, 178),
                 alpha=0.85 - 0.05 * i)

def draw_emblem(cv, cx, cy):
    """Restrained arms of Vessalia: a ring, a wave, one star."""
    cv.circle(cx, cy, 30, HEADER, 3)
    cv.circle(cx, cy, 24, HEADER, 1)
    # star above the wave
    for a in range(5):
        t1 = -math.pi / 2 + a * 2 * math.pi / 5
        t2 = -math.pi / 2 + (a + 0.5) * 2 * math.pi / 5
        x1, y1 = int(cx + 11 * math.cos(t1)), int(cy - 8 + 11 * math.sin(t1))
        x2, y2 = int(cx + 5 * math.cos(t2)), int(cy - 8 + 5 * math.sin(t2))
        cv.line(cx, cy - 8, x1, y1, HEADER, 2)
        cv.line(x1, y1, x2, y2, HEADER, 1)
    # wave across the lower half
    for x in range(cx - 20, cx + 20):
        y = cy + 10 + int(4 * math.sin((x - cx) / 5.5))
        for t in range(2):
            cv.px(x, y + t, HEADER)
    for x in range(cx - 16, cx + 16):
        y = cy + 18 + int(3 * math.sin((x - cx) / 5.5))
        cv.px(x, y, HEADER)

def draw_portrait(cv, x0, y0, x1, y1):
    """Stylised passport photograph: frontal head and shoulders."""
    cv.clip = (x0, y0, x1, y1)  # nothing may spill out of the photo box
    cv.fill_rect(x0, y0, x1, y1, PHOTO_BG)
    # faint guilloche curves behind the sitter
    for k in range(3):
        for x in range(x0 + 4, x1 - 4):
            y = y0 + 26 + k * 52 + int(9 * math.sin((x - x0) / 17.0 + k))
            cv.px(x, y, (188, 198, 205))
            cv.px(x, y + 1, (196, 205, 212))
    cx = (x0 + x1) // 2
    # hair mass behind the head, falling to the shoulders
    cv.fill_ellipse(cx, y0 + 74, 40, 52, HAIR)
    cv.fill_rect(cx - 40, y0 + 74, cx - 26, y1 - 34, HAIR)
    cv.fill_rect(cx + 26, y0 + 74, cx + 40, y1 - 34, HAIR)
    # shoulders / jacket (the clip keeps the ellipse inside the frame)
    cv.fill_ellipse(cx, y1 + 26, 62, 52, JACKET)
    # blouse V at the neck
    for i in range(20):
        cv.line(cx - 12 + i // 2, y1 - 44 + i, cx, y1 - 24 + i, BLOUSE, 2)
        cv.line(cx + 12 - i // 2, y1 - 44 + i, cx, y1 - 24 + i, BLOUSE, 2)
    # neck and face
    cv.fill_rect(cx - 9, y0 + 96, cx + 9, y0 + 118, SKIN)
    cv.fill_ellipse(cx, y0 + 72, 31, 40, SKIN)
    # hair over the crown
    cv.fill_ellipse(cx, y0 + 46, 33, 20, HAIR)
    cv.fill_rect(cx - 33, y0 + 40, cx + 33, y0 + 50, HAIR)
    # features: brows, eyes, nose, mouth — minimal and frontal
    cv.hline(cx - 19, cx - 7, y0 + 68, HAIR, 2)
    cv.hline(cx + 7, cx + 19, y0 + 68, HAIR, 2)
    cv.fill_rect(cx - 16, y0 + 76, cx - 10, y0 + 79, INK)
    cv.fill_rect(cx + 10, y0 + 76, cx + 16, y0 + 79, INK)
    cv.vline(cx, y0 + 82, y0 + 92, (178, 138, 102), 1)
    cv.hline(cx - 7, cx + 7, y0 + 100, (150, 84, 74), 2)
    cv.clip = None
    # photo frame
    cv.rect(x0, y0, x1, y1, INK, 2)

def field(cv, x, y, label, value, vscale=2, vcolour=INK, bold=False):
    """One passport field: small grey bilingual label, value beneath."""
    draw_text(cv, x, y, label, 1, LABEL, spacing=1)
    draw_text(cv, x, y + 11, value, vscale, vcolour, spacing=1, bold=bold)

def draw_data_page(cv):
    x0 = LEFT_X0 + 26          # 54
    x1 = LEFT_X1 - 26          # 474
    mid = (LEFT_X0 + LEFT_X1) // 2

    # --- header
    draw_emblem(cv, x0 + 30, 104)
    draw_text_centered(cv, mid + 26, 76, "REPUBLICA VESSALIA", 3, HEADER,
                       spacing=1, bold=True)
    draw_text_centered(cv, mid + 26, 122, "REPUBLIC OF VESSALIA", 2, HEADER,
                       spacing=2)
    cv.hline(x0, x1, 152, RULE, 2)
    draw_text_centered(cv, mid, 164, "PASSPORT / PASSAPORT", 2, INK,
                       spacing=2)
    cv.hline(x0, x1, 196, RULE, 1)

    # --- photograph, left column
    draw_portrait(cv, x0, 216, x0 + 150, 406)

    # --- fields beside the photograph
    fx = x0 + 176
    # type / code / number on one row
    field(cv, fx, 216, "TYPE / TIP", DOC_TYPE)
    field(cv, fx + 74, 216, "CODE / COD", DOC_CODE)
    field(cv, fx + 148, 216, "PASSPORT NO.", PASSPORT_NO)
    field(cv, fx, 268, "SURNAME / NUME", SURNAME, vscale=3, bold=True)
    field(cv, fx, 322, "GIVEN NAMES / PRENUME", GIVEN_NAMES)
    field(cv, fx, 362, "NATIONALITY / CETATENIE", NATIONALITY)

    cv.hline(x0, x1, 428, RULE, 1)

    # --- fields under the photograph, two columns
    c2 = x0 + 226
    field(cv, x0, 446, "DATE OF BIRTH / DATA NASTERII", DOB_PRINT)
    field(cv, c2, 446, "SEX / SEX", SEX)
    field(cv, x0, 494, "PLACE OF BIRTH / LOC NASTERE", BIRTH_PLACE)
    field(cv, c2, 494, "DATE OF ISSUE / ELIBERAT", ISSUE_PRINT)
    field(cv, x0, 542, "DATE OF EXPIRY / VALABIL PANA LA", EXPIRY_PRINT)
    field(cv, c2, 542, "ISSUING AUTHORITY", "PREFECTURE OF")
    draw_text(cv, c2, 542 + 11 + 17, "PORT SEREIN", 2, INK)

    cv.hline(x0, x1, 606, RULE, 1)

    # --- holder's signature: a ruled line with a quiet squiggle
    draw_text(cv, x0, 622, "HOLDER'S SIGNATURE / SEMNATURA", 1, LABEL)
    for x in range(x0 + 6, x0 + 190):
        y = 668 + int(7 * math.sin((x - x0) / 13.0)
                      + 3 * math.sin((x - x0) / 4.7))
        cv.px(x, y, (52, 58, 96))
        cv.px(x, y + 1, (52, 58, 96))
    cv.hline(x0, x0 + 210, 682, RULE, 1)
    draw_text(cv, x0 + 250, 622, "PAGE / PAGINA", 1, LABEL)
    draw_text(cv, x0 + 250, 633, "3", 2, INK)

# ------------------------------------------------------ machine-readable
def _mrz_value(ch):
    if ch == '<':
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55  # A=10 ... Z=35

def mrz_check_digit(s):
    total = 0
    for i, ch in enumerate(s):
        total += _mrz_value(ch) * (7, 3, 1)[i % 3]
    return str(total % 10)

def mrz_lines():
    line1 = ("P<" + DOC_CODE
             + SURNAME + "<<" + GIVEN_NAMES.replace(" ", "<"))
    line1 = (line1 + "<" * 44)[:44]
    doc = (PASSPORT_NO + "<" * 9)[:9]
    personal = "<" * 14
    body = (doc + mrz_check_digit(doc)
            + DOC_CODE
            + DOB_MRZ + mrz_check_digit(DOB_MRZ)
            + SEX
            + EXPIRY_MRZ + mrz_check_digit(EXPIRY_MRZ)
            + personal + mrz_check_digit(personal))
    composite = body[0:10] + body[13:20] + body[21:43]
    line2 = body + mrz_check_digit(composite)
    assert len(line1) == 44 and len(line2) == 44
    return line1, line2

def draw_mrz(cv):
    # a slightly warmer band across the foot of the data page
    cv.fill_rect(LEFT_X0 + 8, 852, LEFT_X1 - 8, 958, (238, 231, 208))
    line1, line2 = mrz_lines()
    draw_text(cv, 44, 878, line1, 2, INK, spacing=0)
    draw_text(cv, 44, 912, line2, 2, INK, spacing=0)

# ----------------------------------------------------------------- stamps
class StampInk:
    """Collects a stamp's pixels in local coords, then blits them rotated."""

    def __init__(self):
        self.pts = set()

    def px(self, x, y):
        self.pts.add((x, y))

    def hline(self, x0, x1, y, thick=1):
        for t in range(thick):
            for x in range(x0, x1 + 1):
                self.px(x, y + t)

    def vline(self, x, y0, y1, thick=1):
        for t in range(thick):
            for y in range(y0, y1 + 1):
                self.px(x + t, y)

    def rect(self, x0, y0, x1, y1, thick=2):
        self.hline(x0, x1, y0, thick)
        self.hline(x0, x1, y1 - thick + 1, thick)
        self.vline(x0, y0, y1, thick)
        self.vline(x1 - thick + 1, y0, y1, thick)

    def circle(self, r, thick=2):
        for a in range(720):
            t = a * math.pi / 360.0
            for rr in range(r - thick + 1, r + 1):
                self.px(int(rr * math.cos(t)), int(rr * math.sin(t)))

    def text(self, cx, y, s, scale=1, spacing=1):
        x = cx - text_width(s, scale, spacing) // 2
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == '1':
                        for dx in range(scale):
                            for dy in range(scale):
                                self.px(x + col * scale + dx,
                                        y + row * scale + dy)
            x += (5 + spacing) * scale

    def blit(self, cv, cx, cy, angle_deg, colour, alpha=0.88):
        t = math.radians(angle_deg)
        ca, sa = math.cos(t), math.sin(t)
        for (x, y) in self.pts:
            rx = int(round(x * ca - y * sa))
            ry = int(round(x * sa + y * ca))
            cv.px(cx + rx, cy + ry, colour, alpha)

def rect_stamp(lines, w, h):
    """lines: list of (text, scale). A double-ruled rectangular stamp."""
    st = StampInk()
    st.rect(-w // 2, -h // 2, w // 2, h // 2, 2)
    st.rect(-w // 2 + 5, -h // 2 + 5, w // 2 - 5, h // 2 - 5, 1)
    total = sum(7 * s + 6 for (_, s) in lines) - 6
    y = -total // 2
    for (s, scale) in lines:
        st.text(0, y, s, scale)
        y += 7 * scale + 6
    return st

def round_stamp(lines, r):
    st = StampInk()
    st.circle(r, 2)
    st.circle(r - 7, 1)
    total = sum(7 * s + 5 for (_, s) in lines) - 5
    y = -total // 2
    for (s, scale) in lines:
        st.text(0, y, s, scale)
        y += 7 * scale + 5
    return st

def draw_visas_page(cv):
    x0 = RIGHT_X0 + 26         # 550
    x1 = RIGHT_X1 - 26         # 970
    mid = (RIGHT_X0 + RIGHT_X1) // 2

    # --- header
    draw_text_centered(cv, mid, 76, "VISAS", 3, HEADER, spacing=2, bold=True)
    draw_text_centered(cv, mid, 122, "VISE", 2, HEADER, spacing=3)
    cv.hline(x0, x1, 152, RULE, 2)

    # --- the telling detail: a printed harbour-dues condition, top of page
    draw_text(cv, x0, 168, "CONDITIONS OF ENTRY / CONDITII DE INTRARE", 1,
              LABEL)
    notice = [
        "THE HOLDER MAY REMAIN 90 DAYS IN VESSALIA.",
        "HARBOUR DUES ARE PAID AT PORT SEREIN FOR THE",
        "BEARER'S VESSEL AND CREW. FEE: 12 THALERS.",
    ]
    for i, line in enumerate(notice):
        draw_text(cv, x0, 186 + i * 13, line, 1, INK)
    # the small fee stamp that proves the dues were paid
    fee = rect_stamp([("TH 12", 2), ("HARBOUR DUES", 1), ("PAID", 1)],
                     148, 62)
    fee.blit(cv, 892, 200, -3, GREEN_INK)
    cv.hline(x0, x1, 244, RULE, 1)

    # --- border stamps: two trips, every date inside 14 MAR 2022 -
    #     13 MAR 2032, in and out in the right order.
    # trip 1: Vessalia -> Kordavia, June 2023
    rect_stamp([("PORT SEREIN", 1), ("DEPARTED", 2), ("03 JUN 2023", 1)],
               196, 84).blit(cv, 656, 356, -5, BLUE_INK)
    rect_stamp([("KORDAVIA", 2), ("BORDER CONTROL", 1),
                ("ARRIVED 03 JUN 2023", 1)],
               204, 88).blit(cv, 866, 352, 3, RED_INK)
    rect_stamp([("KORDAVIA", 2), ("DEPARTED", 1), ("18 JUN 2023", 1)],
               196, 84).blit(cv, 656, 540, -2, RED_INK)
    round_stamp([("REPUBLICA", 1), ("VESSALIA", 1), ("ENTERED", 1),
                 ("18 JUN 2023", 1)], 62).blit(cv, 868, 540, 5, BLUE_INK)
    # trip 2: Ostmark, autumn 2024
    rect_stamp([("OSTMARK", 2), ("ARRIVED", 1), ("27 OCT 2024", 1)],
               196, 84).blit(cv, 656, 724, 6, BLUE_INK)
    rect_stamp([("OSTMARK", 2), ("DEPARTED", 1), ("02 NOV 2024", 1)],
               196, 84).blit(cv, 866, 720, -4, RED_INK)

    # --- page furniture
    draw_text_centered(cv, mid, 930, "REPUBLICA VESSALIA", 1, LABEL,
                       spacing=2)
    draw_text(cv, x1 - 24, 922, "12", 2, LABEL)

def main():
    cv = Canvas(W, H, DESK)
    draw_spread(cv)
    draw_data_page(cv)
    draw_visas_page(cv)
    draw_mrz(cv)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(encode_png(cv.pix, W, H))
    print("wrote", path)

if __name__ == "__main__":
    main()
