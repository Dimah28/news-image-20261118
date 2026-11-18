#!/usr/bin/env python3
"""news-image-20261118 — "The world in one picture: Wednesday 18 November 2026".

A newspaper front page drawn entirely procedurally with the Python 3.13
standard library only: two embedded Hershey vector fonts (public domain,
A. V. Hershey, US National Bureau of Standards) — Complex Roman for the
serif display face, Simplex as fallback — rendered with 2x supersampled
anti-aliasing, a small vector drawing layer, and a hand-encoded PNG
(zlib). No network, no files read, no randomness, no clock — two runs
write byte-identical files.

Layout (1024x1024), 37 stories, 6 continents:
  masthead -> three hero stories (US-Iran, Crimea bridge, Trump/Quad)
  -> six illustrated stories (Nvidia, Knesset, EU loan, Cyclone Akvan,
  Britain sanctions, China-Canada) -> "BY THE NUMBERS" strip
  -> dotted world map with numbered pins beside "ALSO ON" list of
  28 more stories -> sources footer.
Every story below happened, or was first reported, on Wednesday
18 November 2026; disputed claims are labelled as claims.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (28, 26, 22)
NAVY = (22, 32, 63)        # masthead band
NAVY_DK = (14, 20, 42)
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
EU_BLUE = (16, 48, 120)
TEAL_DK = (14, 58, 66)

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

    def disc(self, cx, cy, r, c):
        """Filled disc (used for soft dots in art)."""
        self.circle(cx, cy, r, c, filled=True)

# Hershey vector fonts (public domain, A.V. Hershey, US NBS).
# Extracted from Paul Bourke's hershey JHF file; only the glyphs used here.
# Each glyph: (left bearing, right bearing, stroke data).
# Stroke data: char pairs, coords relative to ord("R"); a pair " R" = pen up.
SIMPLEX = {
    '!': (-2, 3, 'RMRR RSMSR RRURVSVSURU'),
    '"': (-4, 4, 'PMPQ RTMTQ'),
    '#': (-5, 6, 'RLPW RULSW ROPVP ROSVS'),
    '$': (-5, 5, 'UNSMQMONOPQQTRUSUUSVQVOU RRLRW'),
    '&': (-6, 6, 'VRURTSSURVOVNUNSORRQSPSNRMPMONOPQSSUUVVV'),
    "'": (-2, 2, 'RMRQ'),
    '(': (-3, 4, 'TLRNQPQSRUTW'),
    ')': (-4, 3, 'PLRNSPSSRUPW'),
    '*': (-5, 5, 'RORU ROPUT RUPOT'),
    '+': (-6, 6, 'RNRV RNRVR'),
    ',': (-2, 3, 'SVRVRUSUSWRY'),
    '-': (-6, 6, 'NRVR'),
    '.': (-2, 3, 'RURVSVSURU'),
    '/': (-5, 5, 'VLNW'),
    '0': (-5, 5, 'RMPNOPOSPURVTUUSUPTNRM'),
    '1': (-5, 5, 'PORMRV'),
    '2': (-5, 5, 'ONQMSMUNUPTROVUV'),
    '3': (-5, 5, 'ONQMSMUNUPSQ RRQSQURUUSVQVOU'),
    '4': (-5, 5, 'SMSV RSMNSVS'),
    '5': (-5, 5, 'PMOQQPRPTQUSTURVQVOU RPMTM'),
    '6': (-5, 5, 'TMRMPNOPOSPURVTUUSTQRPPQOS'),
    '7': (-5, 5, 'UMQV ROMUM'),
    '8': (-5, 5, 'QMONOPQQSQUPUNSMQM RQQOROUQVSVUUURSQ'),
    '9': (-5, 5, 'UPTRRSPROPPNRMTNUPUSTURVPV'),
    ':': (-2, 3, 'RPRQSQSPRP RRURVSVSURU'),
    ';': (-2, 3, 'RPRQSQSPRP RSVRVRUSUSWRY'),
    '=': (-6, 6, 'NPVP RNTVT'),
    '?': (-4, 5, 'PNRMSMUNUPRQRRSRSQUP RRURVSVSURU'),
    'A': (-5, 5, 'RMNV RRMVV RPSTS'),
    'B': (-5, 5, 'OMOV ROMSMUNUPSQ ROQSQURUUSVOV'),
    'C': (-5, 6, 'VNTMRMPNOPOSPURVTVVU'),
    'D': (-5, 5, 'OMOV ROMRMTNUPUSTURVOV'),
    'E': (-5, 5, 'OMOV ROMUM ROQSQ ROVUV'),
    'F': (-5, 4, 'OMOV ROMUM ROQSQ'),
    'G': (-5, 6, 'VNTMRMPNOPOSPURVTVVUVR RSRVR'),
    'H': (-5, 5, 'OMOV RUMUV ROQUQ'),
    'I': (-2, 2, 'RMRV'),
    'J': (-4, 3, 'SMSTRVPVOTOS'),
    'K': (-5, 5, 'OMOV RUMOS RQQUV'),
    'L': (-5, 4, 'OMOV ROVUV'),
    'M': (-6, 6, 'NMNV RNMRV RVMRV RVMVV'),
    'N': (-5, 5, 'OMOV ROMUV RUMUV'),
    'O': (-5, 6, 'RMPNOPOSPURVSVUUVSVPUNSMRM'),
    'P': (-5, 5, 'OMOV ROMSMUNUQSROR'),
    'Q': (-5, 6, 'RMPNOPOSPURVSVUUVSVPUNSMRM RSTVW'),
    'R': (-5, 5, 'OMOV ROMSMUNUQSROR RRRUV'),
    'S': (-5, 5, 'UNSMQMONOOPPTRUSUUSVQVOU'),
    'T': (-5, 5, 'RMRV RNMVM'),
    'U': (-5, 6, 'OMOSPURVSVUUVSVM'),
    'V': (-5, 5, 'NMRV RVMRV'),
    'W': (-6, 6, 'NMPV RRMPV RRMTV RVMTV'),
    'X': (-5, 5, 'OMUV RUMOV'),
    'Y': (-5, 5, 'NMRQRV RVMRQ'),
    'Z': (-5, 5, 'UMOV ROMUM ROVUV'),
    'a': (-9, 10, 'XMX[ RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'b': (-10, 9, 'LFL[ RLPNNPMSMUNWPXSXUWXUZS[P[NZLX'),
    'c': (-9, 9, 'XPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'd': (-9, 10, 'XFX[ RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'e': (-9, 9, 'LSXSXQWOVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'f': (-5, 7, 'WFUFSGRJR[ ROMVM'),
    'g': (-9, 10, 'XMX]W`VaTbQbOa RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'h': (-9, 10, 'MFM[ RMQPNRMUMWNXQX['),
    'i': (-4, 4, 'QFRGSFREQF RRMR['),
    'j': (-5, 5, 'RFSGTFSERF RSMS^RaPbNb'),
    'k': (-9, 8, 'MFM[ RWMMW RQSX['),
    'l': (-4, 4, 'RFR['),
    'm': (-15, 15, 'GMG[ RGQJNLMOMQNRQR[ RRQUNWMZM\\N]Q]['),
    'n': (-9, 10, 'MMM[ RMQPNRMUMWNXQX['),
    'o': (-9, 10, 'QMONMPLSLUMXOZQ[T[VZXXYUYSXPVNTMQM'),
    'p': (-10, 9, 'LMLb RLPNNPMSMUNWPXSXUWXUZS[P[NZLX'),
    'q': (-9, 10, 'XMXb RXPVNTMQMONMPLSLUMXOZQ[T[VZXX'),
    'r': (-7, 6, 'OMO[ ROSPPRNTMWM'),
    's': (-8, 9, 'XPWNTMQMNNMPNRPSUTWUXWXXWZT[Q[NZMX'),
    't': (-5, 7, 'RFRWSZU[W[ ROMVM'),
    'u': (-9, 10, 'MMMWNZP[S[UZXW RXMX['),
    'v': (-8, 8, 'LMR[ RXMR['),
    'w': (-11, 11, 'JMN[ RRMN[ RRMV[ RZMV['),
    'x': (-8, 9, 'MMX[ RXMM['),
    'y': (-8, 8, 'LMR[ RXMR[P_NaLbKb'),
    'z': (-8, 9, 'XMM[ RMMXM RM[X['),
    '|': (-2, 2, 'RLRW'),
    '°': (-4, 4, 'QMPNPPQQSQTPTNSMQM'),
    '·': (-2, 3, 'RQRRSRSQRQ'),
    '×': (-5, 5, 'OOUU RUOOU'),
    '‘': (-2, 2, 'RMRQ'),
    '’': (-2, 2, 'RMRQ'),
    '“': (-4, 4, 'PMPQ RTMTQ'),
    '”': (-4, 4, 'PMPQ RTMTQ'),
    '•': (-2, 3, 'RQRRSRSQRQ'),
    '→': (-6, 6, 'SOVRSU RNRVR'),
    "€": (-6, 7, 'VNTMRMPNOPOSPURVTVVU RLPYP RLSYS'),
    '–': (-4, 4, 'ORUR'),
    '—': (-6, 6, 'MRWR'),
}

COMPLEX = {
    '!': (-4, 4, 'RKQLRSSLRK RRLRO RRVQWRXSWRV'),
    '"': (-6, 6, 'OKOP RPKOP RUKUP RVKUP'),
    '#': (-7, 7, 'RKN\\ RVKR\\ RNQWQ RMVVV'),
    '$': (-7, 8, 'QHQ\\ RTHT\\ RWLVLVMWMWLUKPKNLNNOPVSWT RNNOOVRWTWVVWTXQXOWNVNUOUOVNV'),
    '%': (-8, 8, 'XKLX ROKPLPNOOMOLNLLMKOKSLVLXK RUTTUTWUXWXXWXUWTUT'),
    '&': (-8, 9, 'YPXPXQYQYPXOWOVPUTTVSWQXOXMWLVLTMSORRPSNSLRKPKOLONPQUWWXXXYW ROXMVMTOR RONPPVWWX'),
    "'": (-3, 4, 'RKRP RSKRP'),
    '(': (-5, 5, 'UHSJQMPPPTQWSZU\\ RSJRLQPQTRXSZ'),
    ')': (-5, 5, 'OHQJSMTPTTSWQZO\\ RQJRLSPSTRXQZ'),
    '*': (-5, 5, 'RJRP ROKUO RUKOO'),
    '+': (-9, 9, 'RLRX RLRXR'),
    ',': (-4, 4, 'SWRXQWRVSWSYQ['),
    '-': (-9, 9, 'LRXR'),
    '.': (-4, 4, 'RVQWRXSWRV'),
    '/': (-7, 8, 'XHM\\'),
    '0': (-6, 7, 'QKOLNONTOWQXTXVWWTWOVLTKQK RQKPLOOOTPWQX RTXUWVTVOULTK'),
    '1': (-6, 7, 'PNSKSX RRLRX ROXVX'),
    '2': (-6, 7, 'OMONNNNMOLQKTKVLWNVPTQQROSNUNX RTKULVNUPTQ RNWOVPVSWVWWV RPVSXVXWVWU'),
    '3': (-6, 7, 'OMONNNNMOLQKTKVLWNVPTQ RTKULVNUPTQ RRQTQVRWTWUVWTXQXOWNVNUOUOV RTQURVTVUUWTX'),
    '4': (-6, 7, 'SMSX RTKTX RTKMTXT RQXVX'),
    '5': (-6, 7, 'OKNQ ROKVK ROLSLVK RNQOPQOTOVPWRWUVWTXQXOWNVNUOUOV RTOUPVRVUUWTX'),
    '6': (-6, 7, 'VMVNWNWMVLTKRKPLOMNPNUOWQXTXVWWUWSVQTPQPNR RRKPMOPOUPWQX RTXUWVUVSUQTP'),
    '7': (-6, 7, 'NKNO RVMRTPX RWKTQQX RNMPKRKUM RNMPLRLUMVM'),
    '8': (-6, 7, 'QKOLNNOPQQTQVPWNVLTKQK RQKPLONPPQQ RTQUPVNULTK RQQORNTNUOWQXTXVWWUWTVRTQ RQQPROTOUPWQX RTXUWVUVTURTQ'),
    '9': (-6, 7, 'OVOUNUNVOWQXSXUWVVWSWNVLTKQKOLNNNPORQSTSWQ RSXUVVSVNULTK RQKPLONOPPRQS'),
    ':': (-4, 4, 'ROQPRQSPRO RRVQWRXSWRV'),
    ';': (-4, 4, 'ROQPRQSPRO RSWRXQWRVSWSYQ['),
    '<': (-5, 5, 'THPRT\\'),
    '=': (-9, 9, 'LPXP RLTXT'),
    '>': (-5, 5, 'PHTRP\\'),
    '?': (-6, 7, 'NNONOONONNOLQKTKVLWNWOVQSRRSRTST RTKVMVPUQSR RRWRXSXSWRW'),
    '@': (-8, 9, 'UPSOQOPQPRQTSTUS RUOUSVTXTYRYQXNVLSKRKOLMNLQLRMUOWRXSXVW'),
    'A': (-7, 7, 'RKMX RRNVX RRKWX ROTTT RKXPX RTXYX'),
    'B': (-8, 8, 'NKNX ROKOX RLKSKVLWNVPSQ RSKULVNUPSQ ROQSQVRWTWUVWSXLX RSQURVTVUUWSX'),
    'C': (-7, 7, 'VLWKWOVLTKQKOLNMMPMSNVOWQXTXVWWU RQKOMNPNSOVQX'),
    'D': (-8, 8, 'NKNX ROKOX RLKSKVLWMXPXSWVVWSXLX RSKULVMWPWSVVUWSX'),
    'E': (-8, 7, 'NKNX ROKOX RSOSS RLKVKVOUK ROQSQ RLXVXVTUX'),
    'F': (-8, 6, 'NKNX ROKOX RSOSS RLKVKVOUK ROQSQ RLXQX'),
    'G': (-7, 9, 'VLWKWOVLTKQKOLNMMPMSNVOWQXTXVW RQKOMNPNSOVQX RTXUWVU RVSVX RWSWX RTSYS'),
    'H': (-8, 9, 'NKNX ROKOX RVKVX RWKWX RLKQK RTKYK ROQVQ RLXQX RTXYX'),
    'I': (-4, 5, 'RKRX RSKSX RPKUK RPXUX'),
    'J': (-6, 6, 'SKSURWQX RTKTUSWQXPXNWMUNTOUNV RQKVK'),
    'K': (-8, 8, 'NKNX ROKOX RWKOS RQQVX RRQWX RLKQK RTKYK RLXQX RTXYX'),
    'L': (-7, 6, 'OKOX RPKPX RMKRK RMXWXWTVX'),
    'M': (-9, 10, 'MKMX RNNRX RNKRU RWKRX RWKWX RXKXX RKKNK RWKZK RKXOX RUXZX'),
    'N': (-8, 8, 'NKNX ROMVX ROKVV RVKVX RLKOK RTKXK RLXPX'),
    'O': (-7, 8, 'QKOLNMMPMSNVOWQXTXVWWVXSXPWMVLTKQK RQKOMNPNSOVQX RTXVVWSWPVMTK'),
    'P': (-8, 7, 'NKNX ROKOX RLKSKVLWNWOVQSROR RSKULVNVOUQSR RLXQX'),
    'Q': (-7, 8, 'QKOLNMMPMSNVOWQXTXVWWVXSXPWMVLTKQK RQKOMNPNSOVQX RTXVVWSWPVMTK RPWPUQTSTTUUZV[W[XZ RTUUXVZW['),
    'R': (-8, 8, 'NKNX ROKOX RLKSKVLWNWOVQSROR RSKULVNVOUQSR RLXQX RSRTSUWVXWXXW RSRUSVWWX'),
    'S': (-7, 8, 'VMWKWOVMULSKQKOLNMNOOPQQTRVSWT RNNOOQPTQVRWSWVVWTXRXPWOVNTNXOV'),
    'T': (-7, 8, 'RKRX RSKSX RNKMOMKXKXOWK RPXUX'),
    'U': (-8, 9, 'NKNUOWQXTXVWWUWK ROKOUPWQX RLKQK RUKYK'),
    'V': (-7, 7, 'MKRX RNKRU RWKRX RKKPK RTKYK'),
    'W': (-9, 9, 'LKOX RMKOT RRKOX RRKUX RSKUT RXKUX RJKOK RVKZK'),
    'X': (-7, 8, 'NKVX ROKWX RWKNX RLKQK RTKYK RLXQX RTXYX'),
    'Y': (-6, 7, 'NKRRRX ROKSR RWKSRSX RLKQK RTKYK RPXUX'),
    'Z': (-6, 7, 'VKNX RWKOX ROKNONKWK RNXWXWTVX'),
    '[': (-5, 5, 'PHP\\ RQHQ\\ RPHUH RP\\U\\'),
    ']': (-5, 5, 'SHS\\ RTHT\\ ROHTH RO\\T\\'),
    'a': (-6, 8, 'QOPPPQOQOPQOTOVQVWWXXX RTOUQUWWX RURRSPTOUOWPXSXTWUU RRSPUPWQX'),
    'b': (-8, 7, 'NKNX ROKOX RORPPROTOVPWRWUVWTXRXPWOU RTOUPVRVUUWTX RLKOK'),
    'c': (-6, 6, 'VQUQURVRVQUPSOQOOPNRNUOWQXSXUWVV RQOPPOROUPWQX'),
    'd': (-6, 9, 'VKVX RWKWX RVRUPSOQOOPNRNUOWQXSXUWVU RQOPPOROUPWQX RTKWK RVXYX'),
    'e': (-6, 6, 'OSVSVRUPSOQOOPNRNUOWQXSXUWVV RUSUQSO RQOPPOROUPWQX'),
    'f': (-6, 5, 'TKULUMVMVLTKRKPMPX RRKQMQX RNOSO RNXSX'),
    'g': (-6, 7, 'QOOQOSQUSUUSUQSOQO RQOPQPSQU RSUTSTQSO RTPUOVO RPTOUOXPYTYVZ ROWPXTXVYV[T\\P\\N[NYPX'),
    'h': (-8, 9, 'NKNX ROKOX RORPPROTOVPWRWX RTOUPVRVX RLKOK RLXQX RTXYX'),
    'i': (-4, 5, 'RKRLSLSKRK RRORX RSOSX RPOSO RPXUX'),
    'j': (-4, 5, 'SKSLTLTKSK RSOSZR\\ RTOTZR\\P\\O[OZPZP[O[ RQOTO'),
    'k': (-8, 8, 'NKNX ROKOX RWOOU RRSVX RSSWX RLKOK RTOYO RLXQX RTXYX'),
    'l': (-4, 5, 'RKRX RSKSX RPKSK RPXUX'),
    'm': (-12, 13, 'JOJX RKOKX RKRLPNOPORPSRSX RPOQPRRRX RSRTPVOXOZP[R[X RXOYPZRZX RHOKO RHXMX RPXUX RXX]X'),
    'n': (-8, 9, 'NONX ROOOX RORPPROTOVPWRWX RTOUPVRVX RLOOO RLXQX RTXYX'),
    'o': (-6, 7, 'QOOPNRNUOWQXTXVWWUWRVPTOQO RQOPPOROUPWQX RTXUWVUVRUPTO'),
    'p': (-8, 7, 'NON\\ ROOO\\ RORPPROTOVPWRWUVWTXRXPWOU RTOUPVRVUUWTX RLOOO RL\\Q\\'),
    'q': (-7, 7, 'UOU\\ RVOV\\ RURTPROPONPMRMUNWPXRXTWUU RPOOPNRNUOWPX RS\\X\\'),
    'r': (-7, 6, 'OOOX RPOPX RPRQPSOUOVPVQUQUPVP RMOPO RMXRX'),
    's': (-6, 7, 'TOUPUQVQVPTOQOOPORQSTTVU ROQQRTSVTVWTXQXOWOVPVPWQX'),
    't': (-6, 5, 'PKPVRXTXUWUV RQKQVRX RNOTO'),
    'u': (-8, 9, 'NONUOWQXSXUWVU ROOOUPWQX RVOVX RWOWX RLOOO RTOWO RVXYX'),
    'v': (-7, 7, 'NORX ROORV RVORX RLOQO RTOXO'),
    'w': (-9, 9, 'LOOX RMOOU RROOX RROUX RSOUU RXOUX RJOOO RVOZO'),
    'x': (-7, 7, 'NOUX ROOVX RVONX RLOQO RTOXO RLXPX RSXXX'),
    'y': (-7, 7, 'NORX ROORV RVORXP[N\\M\\L[LZMZM[L[ RLOQO RTOXO'),
    'z': (-6, 6, 'UONX RVOOX ROONQNOVO RNXVXVVUX'),
    '{': (-6, 5, 'SHQIPJPLRNSP RQIPL RSNRQ RPJQLSNSPRQPRRSSTSVQXPZ RRSSV RPXQ[ RSTRVPXPZQ[S\\'),
    '|': (-3, 3, 'RHR\\'),
    '}': (-5, 6, 'QHSITJTLRNQP RSITL RQNRQ RTJSLQNQPRQTRRSQTQVSXTZ RRSQV RTXS[ RQTRVTXTZS[Q\\'),
    '°': (-5, 5, 'QKPLPNQOSOTNTLSKQK'),
    '·': (-4, 4, 'RQQRRSSRRQ'),
    '×': (-8, 8, 'MMWW RWMMW'),
    '‘': (-3, 4, 'RKRP RSKRP'),
    '’': (-3, 4, 'RKRP RSKRP'),
    '“': (-6, 6, 'OKOP RPKOP RUKUP RVKUP'),
    '”': (-6, 6, 'OKOP RPKOP RUKUP RVKUP'),
    '•': (-4, 4, 'RQQRRSSRRQ'),
    "€": (-8, 8, 'VLWKWOVLTKQKOLNMMPMSNVOWQXTXVWWU RQKOMNPNSOVQX RJQZQ RJTZT'),
    '–': (-4, 4, 'OSUS'),
    '—': (-6, 6, 'MSWS'),
}

METRICS = {"S": {'cap_top': -5, 'cap_bot': 5, 'low_top': -13, 'low_bot': 16}, "C": {'cap_top': -7, 'cap_bot': 9, 'low_top': -7, 'low_bot': 10}}

# ---------------------------------------------------------------- vector text
# Hershey glyphs are stroke polylines in a y-down coordinate space.
# A pair " R" (space + 'R') lifts the pen. Each glyph is rasterised once
# per (font, size, pen) into a 2x-supersampled coverage bitmap, cached,
# then alpha-blended onto the canvas.
SS = 2
_DISC_CACHE = {}

def _disc_offsets(rad):
    key = round(rad, 2)
    hit = _DISC_CACHE.get(key)
    if hit is not None:
        return hit
    rr = int(math.ceil(rad))
    offs = [(dx, dy) for dy in range(-rr, rr + 1) for dx in range(-rr, rr + 1)
            if dx * dx + dy * dy <= rad * rad]
    _DISC_CACHE[key] = offs
    return offs

def _glyph_segments(data):
    segs = []
    pen = None
    for i in range(0, len(data), 2):
        c0, c1 = data[i], data[i + 1]
        if c0 == ' ':
            pen = None
        else:
            x, y = ord(c0) - 82, ord(c1) - 82
            if pen is not None:
                segs.append((pen, (x, y)))
            pen = (x, y)
    return segs

class VecFont:
    """One Hershey font: table char -> (left, right, stroke data)."""

    def __init__(self, table, metrics, space_adv):
        self.t = table
        self.m = metrics
        self.cap_h = metrics['cap_bot'] - metrics['cap_top']
        self.space_adv = space_adv
        self.cache = {}
        self.fallback = None

    def _resolve(self, ch):
        if ch in self.t:
            return self, self.t[ch]
        if self.fallback is not None and ch in self.fallback.t:
            return self.fallback, self.fallback.t[ch]
        return None, None

    def bitmap(self, ch, cap_px, pen_px):
        """Returns (W, H, bx, by, runs, advance_px); runs = [(dx, dy, cov)]."""
        key = (ch, cap_px, pen_px)
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        font, g = self._resolve(ch)
        if font is None:
            return None
        l, r, data = g
        m = font.m
        scale = cap_px / font.cap_h
        segs = _glyph_segments(data)
        ytop = (m['cap_top'] - 2 - m['cap_bot']) * scale
        ybot = (max(m['cap_bot'], m['low_bot']) + 1 - m['cap_bot']) * scale
        W = max(1, int(math.ceil((r - l) * scale)) + 2)
        H = max(1, int(math.ceil(ybot - ytop)) + 2)
        sw, sh = W * SS, H * SS
        buf = bytearray(sw * sh)
        rad = max(0.6, pen_px * SS / 2.0)
        offs = _disc_offsets(rad)
        ox = SS
        oy = (-ytop + 1) * SS
        for (ax, ay), (bx, by) in segs:
            X0 = (ax - l) * scale * SS + ox
            Y0 = (ay - m['cap_bot']) * scale * SS + oy
            X1 = (bx - l) * scale * SS + ox
            Y1 = (by - m['cap_bot']) * scale * SS + oy
            length = math.hypot(X1 - X0, Y1 - Y0)
            steps = max(1, int(length / 1.0) + 1)
            for s in range(steps + 1):
                t = s / steps
                ix = int(round(X0 + (X1 - X0) * t))
                iy = int(round(Y0 + (Y1 - Y0) * t))
                for dx, dy in offs:
                    px, py = ix + dx, iy + dy
                    if 0 <= px < sw and 0 <= py < sh:
                        buf[py * sw + px] = 255
        runs = []
        for yy in range(H):
            for xx in range(W):
                tot = 0
                for dy in range(SS):
                    row0 = (yy * SS + dy) * sw + xx * SS
                    tot += buf[row0] + buf[row0 + 1]
                if tot:
                    runs.append((xx, yy, min(255, tot * 64)))
        out = (W, H, -1, int(round(ytop)) - 1, runs, (r - l) * scale)
        self.cache[key] = out
        return out

    def advance(self, ch, cap_px, tracking=0.0):
        if ch == ' ':
            return self.space_adv * cap_px / self.cap_h + tracking
        font, g = self._resolve(ch)
        if font is None:
            return 0.0
        l, r, _ = g
        return (r - l) * cap_px / font.cap_h + tracking

    def text_w(self, s, cap_px, pen_px, tracking=0.0):
        return sum(self.advance(ch, cap_px, tracking) for ch in s) - tracking

SERIF = VecFont(COMPLEX, METRICS['C'], 6.0)
SANS = VecFont(SIMPLEX, METRICS['S'], 4.0)
SERIF.fallback = SANS
SANS.fallback = SERIF

def draw_text(cv, x, y_base, s, cap_px, color, font=SERIF, pen_frac=0.14,
              tracking=0.0):
    """Draw s with its baseline at y_base. Returns x of the string end."""
    pen_px = max(1.0, cap_px * pen_frac)
    cx = float(x)
    for ch in s:
        if ch == ' ':
            cx += font.advance(' ', cap_px, tracking)
            continue
        bm = font.bitmap(ch, cap_px, pen_px)
        if bm is None:
            continue
        W, H, bx, by, runs, adv = bm
        gx = int(round(cx)) + bx
        gy = int(round(y_base)) + by
        for dx, dy, cov in runs:
            px, py = gx + dx, gy + dy
            if 0 <= px < cv.w and 0 <= py < cv.h:
                i = (py * cv.w + px) * 3
                a = cov / 255.0
                cv.px[i] = int(color[0] * a + cv.px[i] * (1 - a))
                cv.px[i + 1] = int(color[1] * a + cv.px[i + 1] * (1 - a))
                cv.px[i + 2] = int(color[2] * a + cv.px[i + 2] * (1 - a))
        cx += adv + tracking
    return cx

def draw_text_c(cv, cx, y_base, s, cap_px, color, font=SERIF, pen_frac=0.14,
                tracking=0.0):
    """Centred variant of draw_text."""
    w = font.text_w(s, cap_px, max(1.0, cap_px * pen_frac), tracking)
    return draw_text(cv, cx - w / 2, y_base, s, cap_px, color, font,
                     pen_frac, tracking)

def wrap(font, s, width, cap_px, pen_px, tracking=0.0):
    """Greedy word wrap; returns list of lines fitting width px."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if font.text_w(trial, cap_px, pen_px, tracking) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            while font.text_w(word, cap_px, pen_px, tracking) > width:
                # hard-split an overlong word by characters
                cut = 1
                while (cut < len(word) and
                       font.text_w(word[:cut + 1], cap_px, pen_px, tracking)
                       <= width):
                    cut += 1
                lines.append(word[:cut])
                word = word[cut:]
            cur = word
    if cur:
        lines.append(cur)
    return lines

def draw_para(cv, x, y_base, lines, cap_px, color, lh, font=SERIF,
              pen_frac=0.14, tracking=0.0):
    y = y_base
    for ln in lines:
        draw_text(cv, x, y, ln, cap_px, color, font, pen_frac, tracking)
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

def _land(c, r, cols, rows):
    # LAND ellipses are in a 46x29 grid; scale any grid into it.
    c46 = c * 46.0 / cols
    r29 = r * 29.0 / rows
    for cx, cy, rx, ry in LAND:
        if ((c46 - cx) / rx) ** 2 + ((r29 - cy) / ry) ** 2 <= 1:
            return True
    return False

def draw_map(cv, x, y, cols=88, rows=44, sx=4, sy=3.5, dot=2):
    """Dense dotted world map: small close dots so the land reads clearly."""
    for r in range(rows):
        for c in range(cols):
            if _land(c, r, cols, rows):
                cv.fill(int(x + c * sx), int(y + r * sy), dot, dot, MAPDOT)

def pin_xy(x, y, lon, lat, cols=88, rows=48, sx=5, sy=4):
    c = (lon + 180.0) / 360.0 * cols
    r = (75.0 - lat) / 135.0 * rows
    return int(x + c * sx), int(y + r * sy)

def draw_pin(cv, px, py, n):
    cv.circle(px, py, 9, BRICK)
    cv.circle(px, py, 9, BRICK_DK, filled=False)
    s = str(n)
    w = SERIF.text_w(s, 11, 1.5)
    draw_text(cv, px - w / 2, py + 4, s, 11, WHITE, SERIF, pen_frac=0.14)

# ---------------------------------------------------------------- illustrations
# Every art function draws into the box (x, y, w, h) using relative
# coordinates, so the same scene works as a wide hero strip or a small
# square icon.
def _rx(x, w, f):
    return x + int(w * f)

def _ry(y, h, f):
    return y + int(h * f)

def art_jet(cv, x, y, w, h):
    """Night over the Gulf: a big fighter jet, missile streak, explosion, sea."""
    cv.fill(x, y, w, h, (16, 28, 44))
    cv.fill(x, y + h * 2 // 3, w, h // 3, (20, 44, 62))
    for sx, sy in ((0.06, 0.12), (0.20, 0.05), (0.35, 0.16), (0.52, 0.07),
                   (0.68, 0.14), (0.86, 0.05), (0.12, 0.30), (0.44, 0.26),
                   (0.78, 0.30), (0.28, 0.08), (0.58, 0.20)):
        cv.fill(_rx(x, w, sx), _ry(y, h, sy), 2, 2, WHITE)
    cv.fill(_rx(x, w, 0.35), _ry(y, h, 0.16), 3, 3, WHITE)
    cv.fill(_rx(x, w, 0.68), _ry(y, h, 0.14), 3, 3, WHITE)
    # faint cloud band, upper left
    cv.fill(_rx(x, w, 0.08), _ry(y, h, 0.10), int(w * 0.16), 4,
            (60, 80, 105))
    cv.fill(_rx(x, w, 0.14), _ry(y, h, 0.14), int(w * 0.12), 3,
            (60, 80, 105))
    # big explosion top-right: orange disc, yellow core, red sparks
    ex, ey = _rx(x, w, 0.86), _ry(y, h, 0.24)
    er = max(9, int(min(w, h) * 0.19))
    cv.disc(ex, ey, er, (232, 110, 40))
    cv.disc(ex, ey, max(5, er // 2), (240, 190, 60))
    cv.disc(ex, ey, max(3, er // 4), (250, 230, 150))
    for dx0, dy0 in ((0.74, 0.10), (0.94, 0.38), (0.76, 0.40), (0.93, 0.12)):
        cv.disc(_rx(x, w, dx0), _ry(y, h, dy0), 3, (232, 120, 60))
    # jet: big side profile flying right — deep fuselage, big delta wing
    def _jp(fx, fy):
        return _rx(x, w, fx), _ry(y, h, fy)
    # fuselage: pointed nose, deep body, flat tail
    cv.poly([_jp(0.04, 0.36), _jp(0.10, 0.30), _jp(0.48, 0.26),
             _jp(0.64, 0.30), _jp(0.66, 0.36), _jp(0.62, 0.42),
             _jp(0.48, 0.46), _jp(0.10, 0.46), _jp(0.04, 0.42)],
            (228, 228, 222))
    # canopy: dark window near the nose
    cv.poly([_jp(0.50, 0.28), _jp(0.58, 0.30), _jp(0.56, 0.34),
             _jp(0.50, 0.33)], (52, 78, 100))
    # big delta wing sweeping back-down
    cv.poly([_jp(0.30, 0.44), _jp(0.16, 0.82), _jp(0.44, 0.46)],
            (205, 205, 198))
    # tail fin sweeping up-back
    cv.poly([_jp(0.10, 0.32), _jp(0.06, 0.08), _jp(0.16, 0.30)],
            (205, 205, 198))
    # horizontal stabiliser at the tail
    cv.poly([_jp(0.06, 0.44), _jp(0.02, 0.58), _jp(0.12, 0.45)],
            (205, 205, 198))
    # engine flame: bright, layered
    bx0, by0 = _jp(0.04, 0.38)
    cv.poly([(bx0, by0 - 5), (bx0 - max(14, int(w * 0.06)), by0),
             (bx0, by0 + 5)], (240, 150, 50))
    cv.poly([(bx0, by0 - 3), (bx0 - max(9, int(w * 0.04)), by0),
             (bx0, by0 + 3)], (250, 210, 110))
    # missile streak from the jet toward the explosion, 3px thick
    mx0, my0 = _rx(x, w, 0.68), _ry(y, h, 0.30)
    mx1, my1 = _rx(x, w, 0.82), _ry(y, h, 0.26)
    for do in (-1, 0, 1):
        cv.line(mx0, my0 + do, mx1, my1 + do, (240, 140, 90))
    cv.disc(mx1, my1, 3, (250, 210, 110))
    # island silhouette bottom-right with a tiny light
    cv.poly([_jp(0.78, 1.00), _jp(0.84, 0.84), _jp(0.90, 0.88),
             _jp(0.96, 0.82), _jp(1.00, 1.00)], (10, 20, 32))
    cv.disc(_jp(0.88, 0.86)[0], _jp(0.88, 0.86)[1], 2, (240, 200, 110))
    # sea glints, 2px thick
    for wy, wl in ((0.74, 0.5), (0.82, 0.7), (0.90, 0.45), (0.70, 0.30)):
        cv.fill(_rx(x, w, 0.05), _ry(y, h, wy), int(w * wl), 2,
                (90, 120, 150))

def art_bridge(cv, x, y, w, h):
    """Kerch Strait: the road arch down, one span tilted into the sea."""
    cv.fill(x, y, w, h, SKY)
    cv.fill(x, y + h * 2 // 3, w, h // 3, SEA)
    cv.disc(_rx(x, w, 0.86), _ry(y, h, 0.18), max(7, int(h * 0.13)), GOLD_LT)
    # soft cloud puffs: overlapping discs, not bars
    for cx0, cy0 in ((0.14, 0.12), (0.66, 0.08)):
        for dx0, dy0, dr in ((0.00, 0.00, 0.035), (0.04, -0.02, 0.028),
                             (0.08, 0.00, 0.032)):
            cv.disc(_rx(x, w, cx0 + dx0), _ry(y, h, cy0 + dy0),
                    max(3, int(w * dr)), (228, 234, 240))
    # far shore
    cv.fill(x, y + h * 2 // 3 - 4, w, 4, (110, 130, 120))
    deck_y = y + h // 2
    deck_t = max(5, int(h * 0.07))
    # deck: thick filled slabs, left span intact, right span, gap in middle
    cv.fill(x + 4, deck_y - deck_t // 2, _rx(x, w, 0.40) - x - 4, deck_t,
            WHITE)
    cv.fill(_rx(x, w, 0.60), deck_y - deck_t // 2, x + w - 4 - _rx(x, w, 0.60),
            deck_t, WHITE)
    # deck edge line under each slab, so the slabs read solid
    cv.fill(x + 4, deck_y + deck_t // 2, _rx(x, w, 0.40) - x - 4, 2,
            (190, 195, 200))
    cv.fill(_rx(x, w, 0.60), deck_y + deck_t // 2,
            x + w - 4 - _rx(x, w, 0.60), 2, (190, 195, 200))
    # collapsed span: big jagged broken slab tilted steeply into the water
    cv.poly([(_rx(x, w, 0.40), deck_y - deck_t // 2),
             (_rx(x, w, 0.46), deck_y + int(h * 0.10)),
             (_rx(x, w, 0.44), deck_y + int(h * 0.16)),
             (_rx(x, w, 0.50), deck_y + int(h * 0.24)),
             (_rx(x, w, 0.58), deck_y + int(h * 0.28)),
             (_rx(x, w, 0.56), deck_y + int(h * 0.28) + deck_t),
             (_rx(x, w, 0.48), deck_y + int(h * 0.24) + deck_t),
             (_rx(x, w, 0.44), deck_y + int(h * 0.16) + deck_t),
             (_rx(x, w, 0.42), deck_y + int(h * 0.10) + deck_t),
             (_rx(x, w, 0.40), deck_y + deck_t // 2)], (222, 222, 218))
    # broken arch: two thick leaning bands, clearly snapped at the top
    ax = _rx(x, w, 0.50)
    ab = max(5, int(w * 0.018))
    cv.poly([(ax - int(w * 0.14), deck_y),
             (ax - int(w * 0.02), deck_y - int(h * 0.34)),
             (ax - int(w * 0.02) + ab, deck_y - int(h * 0.34)),
             (ax - int(w * 0.14) + ab, deck_y)], (70, 84, 96))
    cv.poly([(ax + int(w * 0.02), deck_y - int(h * 0.34)),
             (ax + int(w * 0.14), deck_y),
             (ax + int(w * 0.14) - ab, deck_y),
             (ax + int(w * 0.02) - ab, deck_y - int(h * 0.34))],
            (70, 84, 96))
    # arch cross-braces, so the arch reads as structure, not two lines
    for bx0 in (0.40, 0.44, 0.56, 0.60):
        px = _rx(x, w, bx0)
        cv.fill(px, deck_y - int(h * 0.22), 2, int(h * 0.22), (70, 84, 96))
    # piers: thick filled slabs down into the water
    for fx in (0.12, 0.28, 0.72, 0.88):
        px = _rx(x, w, fx)
        cv.fill(px - 3, deck_y, 7, y + h * 2 // 3 - deck_y, (200, 200, 196))
        cv.fill(px - 3, y + h * 2 // 3 - 2, 7, 2, (170, 175, 180))
    # smoke plume over the gap: a rising column drifting right with the
    # wind, thinning and lightening as it rises — not one round blob
    plume = [(0.50, 0.44, 0.050, (178, 178, 172)),
             (0.52, 0.37, 0.055, (182, 182, 176)),
             (0.55, 0.31, 0.050, (188, 188, 182)),
             (0.58, 0.25, 0.042, (195, 195, 190)),
             (0.61, 0.20, 0.035, (200, 200, 195)),
             (0.64, 0.16, 0.028, (205, 205, 200))]
    for sx, sy, sr, col in plume:
        cv.disc(_rx(x, w, sx), _ry(y, h, sy), max(4, int(w * sr)), col)
    # small dark core at the base of the plume, where the fire is
    cv.disc(_rx(x, w, 0.50), _ry(y, h, 0.44), max(3, int(w * 0.02)),
            (90, 90, 88))
    # splash at the waterline where the span went in + debris
    for dx0, dy0 in ((0.47, 0.80), (0.52, 0.86), (0.44, 0.88), (0.55, 0.82)):
        cv.fill(_rx(x, w, dx0), _ry(y, h, dy0), 3, 2, (235, 238, 240))
    cv.fill(_rx(x, w, 0.46), _ry(y, h, 0.78), int(w * 0.10), 2,
            (235, 238, 240))
    # water ripples
    for wy in (0.74, 0.86):
        cv.fill(_rx(x, w, 0.05), _ry(y, h, wy), int(w * 0.55), 2,
                (90, 130, 150))

def art_skyline(cv, x, y, w, h):
    """Dusk skyline over water, four summit flags — the summits art."""
    cv.fill(x, y, w, h, (56, 102, 118))
    cv.fill(x, y + h // 2, w, h - h // 2, (34, 68, 86))
    # moon top-left, clear of the flags (which sit top-right)
    cv.disc(_rx(x, w, 0.10), _ry(y, h, 0.18), max(9, int(h * 0.17)),
            (232, 196, 110))
    cv.disc(_rx(x, w, 0.10), _ry(y, h, 0.18), max(5, int(h * 0.09)),
            (250, 220, 140))
    # moon reflection on the water: short gold dashes under the moon
    for k in range(3):
        yy = y + h // 2 + 6 + k * 8
        if yy < y + h - 2:
            cv.fill(_rx(x, w, 0.07), yy, int(w * 0.07), 2, (200, 175, 110))
    base = y + h - int(h * 0.24)
    # building silhouettes, heights as fractions of the art height
    sil = [(0.00, 0.42), (0.06, 0.42), (0.06, 0.28), (0.11, 0.28),
           (0.11, 0.48), (0.17, 0.48), (0.17, 0.16), (0.22, 0.16),
           (0.22, 0.48), (0.29, 0.48), (0.29, 0.32), (0.34, 0.32),
           (0.34, 0.48), (0.40, 0.48), (0.40, 0.22), (0.44, 0.22),
           (0.44, 0.30), (0.47, 0.30), (0.47, 0.48), (0.53, 0.48),
           (0.53, 0.36), (0.58, 0.36), (0.58, 0.48), (0.65, 0.48),
           (0.65, 0.26), (0.70, 0.26), (0.70, 0.48), (0.77, 0.48),
           (0.77, 0.38), (0.82, 0.38), (0.82, 0.48), (0.88, 0.48),
           (0.88, 0.28), (0.93, 0.28), (0.93, 0.48), (1.00, 0.48)]
    pts = [(_rx(x, w, fx), base - int(fh * h)) for fx, fh in sil]
    pts += [(x + w, base), (x, base)]
    cv.poly(pts, (8, 22, 28))
    # lit windows, spread across the skyline so it reads inhabited
    for wx, wy in ((0.19, 0.30), (0.30, 0.40), (0.42, 0.34), (0.48, 0.18),
                   (0.67, 0.40), (0.79, 0.44), (0.90, 0.36), (0.24, 0.26),
                   (0.08, 0.44), (0.14, 0.34), (0.36, 0.44), (0.55, 0.44),
                   (0.61, 0.32), (0.73, 0.34), (0.85, 0.44), (0.95, 0.44)):
        cv.fill(_rx(x, w, wx), base - int(wy * h), 3, 3, GOLD_LT)
    # four flags: US, Japan, India, Australia (simplified but recognisable)
    for fx, kind in ((0.62, 'us'), (0.70, 'jp'), (0.78, 'in'), (0.86, 'au')):
        px = _rx(x, w, fx)
        py = y + int(h * 0.06)
        cv.vline(px, py, int(h * 0.30), (240, 236, 224))
        fw, fh = max(18, int(w * 0.09)), max(11, int(h * 0.16))
        if kind == 'us':
            for i in range(4):
                cv.fill(px + 1, py + i * (fh // 4), fw, fh // 8,
                        BRICK if i % 2 == 0 else WHITE)
            cv.fill(px + 1, py, fw // 2, fh // 2, (30, 50, 110))
        elif kind == 'jp':
            cv.fill(px + 1, py, fw, fh, WHITE)
            cv.disc(px + 1 + fw // 2, py + fh // 2, max(2, fh // 4), BRICK)
        elif kind == 'in':
            cv.fill(px + 1, py, fw, fh // 3, (232, 130, 40))
            cv.fill(px + 1, py + fh // 3, fw, fh // 3, WHITE)
            cv.fill(px + 1, py + 2 * fh // 3, fw, fh // 3, (20, 120, 60))
        else:
            cv.fill(px + 1, py, fw, fh, (30, 50, 110))
            cv.disc(px + 1 + fw // 2, py + fh // 2, max(2, fh // 5), WHITE)
    # water glints
    for wy in range(3):
        yy = base + 6 + wy * 7
        if yy < y + h - 2:
            cv.hline(x + 12, yy, w - 24, (52, 96, 108))

def art_chip(cv, x, y, w, h):
    """Nvidia: a chip with pins and a rising green chart arrow."""
    cv.fill(x, y, w, h, (14, 38, 34))
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    cs = int(s * 0.52)
    # pins
    for i in range(4):
        off = -cs // 2 + 4 + i * (cs // 4)
        cv.fill(cx + off, cy - cs // 2 - 5, 3, 5, (180, 190, 185))
        cv.fill(cx + off, cy + cs // 2, 3, 5, (180, 190, 185))
        cv.fill(cx - cs // 2 - 5, cy + off, 5, 3, (180, 190, 185))
        cv.fill(cx + cs // 2, cy + off, 5, 3, (180, 190, 185))
    cv.fill(cx - cs // 2, cy - cs // 2, cs, cs, (24, 58, 52))
    cv.rect(cx - cs // 2, cy - cs // 2, cs, cs, (120, 170, 150), lw=1)
    cv.fill(cx - cs // 4, cy - cs // 4, cs // 2, cs // 2, (40, 90, 80))
    # rising chart arrow across the chip, drawn 3px thick
    pts = [(cx - cs // 2 + 3, cy + cs // 4), (cx - cs // 6, cy + cs // 8),
           (cx + cs // 8, cy - cs // 8), (cx + cs // 2 - 3, cy - cs // 4)]
    for dy in (-1, 0, 1):
        for i in range(len(pts) - 1):
            cv.line(pts[i][0], pts[i][1] + dy, pts[i + 1][0],
                    pts[i + 1][1] + dy, (110, 220, 130))
    ex, ey = pts[-1]
    cv.poly([(ex + 2, ey - 2), (ex - 9, ey - 1), (ex - 1, ey + 9)],
            (110, 220, 130))

def art_parliament(cv, x, y, w, h):
    """Knesset: columned facade with pediment and steps."""
    cv.fill(x, y, w, h, (214, 196, 160))
    cv.fill(x, y + h - int(h * 0.14), w, int(h * 0.14), (122, 96, 66))
    cx = x + w // 2
    top = y + int(h * 0.16)
    # pediment
    cv.poly([(cx - int(w * 0.34), top + int(h * 0.16)),
             (cx + int(w * 0.34), top + int(h * 0.16)),
             (cx, top)], (90, 80, 70))
    # entablature + columns
    cv.fill(cx - int(w * 0.34), top + int(h * 0.16), int(w * 0.68),
            max(3, int(h * 0.05)), (240, 236, 224))
    col_top = top + int(h * 0.22)
    col_bot = y + h - int(h * 0.16)
    for i in range(5):
        ccx = cx - int(w * 0.26) + i * int(w * 0.13)
        cv.fill(ccx, col_top, max(3, int(w * 0.05)), col_bot - col_top,
                (240, 236, 224))
    # steps
    for i in range(3):
        yy = col_bot + 2 + i * max(2, int(h * 0.03))
        cv.hline(cx - int(w * 0.30) + i * 4, yy, int(w * 0.60) - i * 8,
                 (90, 80, 70))
    # small flag
    cv.vline(cx, y + int(h * 0.04), int(h * 0.12), (60, 50, 40))
    cv.fill(cx + 1, y + int(h * 0.04), max(8, int(w * 0.12)),
            max(5, int(h * 0.07)), (30, 70, 160))

def art_eu(cv, x, y, w, h):
    """EU: circle of gold stars on blue, big euro sign in the middle."""
    cv.fill(x, y, w, h, EU_BLUE)
    cx, cy = x + w // 2, y + h // 2
    rr = int(min(w, h) * 0.34)
    for i in range(12):
        a = 2 * math.pi * i / 12 - math.pi / 2
        sx = cx + int(rr * math.cos(a))
        sy = cy + int(rr * math.sin(a))
        cv.disc(sx, sy, max(2, int(min(w, h) * 0.035)), GOLD_LT)
    # big euro sign, centred, bold
    cap = int(min(w, h) * 0.52)
    tw = SERIF.text_w("\u20ac", cap, max(1.0, cap * 0.26))
    draw_text(cv, cx - tw / 2, cy + cap * 0.36, "\u20ac", cap, GOLD_LT,
              SERIF, pen_frac=0.26)

def art_cyclone(cv, x, y, w, h):
    """Cyclone Akvan: tight spiral bands over a coastline, landfall dot."""
    cv.fill(x, y, w, h, TEAL_DK)
    cv.fill(x, y + h * 3 // 4, w, h // 4, (214, 186, 140))
    cx, cy = x + int(w * 0.42), y + int(h * 0.44)
    # spiral: dense, more than two turns, thick 3px band so it reads solid
    for k in range(0, 241):
        a = k * 2.5 * math.pi / 180.0
        r = max(2, int(min(w, h) * 0.36) - k // 5)
        px = cx + int(r * math.cos(a))
        py = cy + int(r * math.sin(a))
        cv.disc(px, py, 3, WHITE)
    # clear eye: gold disc with a white ring
    cv.disc(cx, cy, max(4, int(min(w, h) * 0.07)), GOLD_LT)
    cv.circle(cx, cy, max(4, int(min(w, h) * 0.07)), WHITE, filled=False)
    # rain streaks, longer and brighter
    for rx0, ry0 in ((0.08, 0.10), (0.82, 0.12), (0.90, 0.30), (0.06, 0.42),
                     (0.70, 0.06), (0.16, 0.62)):
        cv.line(_rx(x, w, rx0), _ry(y, h, ry0), _rx(x, w, rx0) + 7,
                _ry(y, h, ry0) + 12, (190, 215, 225))
    # landfall dot on the coast + arrow, bigger and clearer
    lx, ly = _rx(x, w, 0.72), y + h * 3 // 4 - 4
    cv.disc(lx, ly, 5, BRICK)
    cv.disc(lx, ly, 2, WHITE)
    cv.line(lx - 14, ly - 14, lx - 5, ly - 5, BRICK)
    cv.line(lx - 14, ly - 13, lx - 5, ly - 4, BRICK)

def art_sanctions(cv, x, y, w, h):
    """Britain sanctions: a stamped document with a Union Jack corner."""
    cv.fill(x, y, w, h, (214, 196, 160))
    dx, dy = x + int(w * 0.14), y + int(h * 0.12)
    dw, dh = int(w * 0.72), int(h * 0.72)
    cv.fill(dx, dy, dw, dh, WHITE)
    cv.rect(dx, dy, dw, dh, INK, lw=1)
    # Union Jack corner (simplified)
    fw, fh = int(dw * 0.30), int(dh * 0.24)
    cv.fill(dx + 4, dy + 4, fw, fh, (30, 50, 110))
    cv.fill(dx + 4 + fw // 2 - 2, dy + 4, 4, fh, WHITE)
    cv.fill(dx + 4, dy + 4 + fh // 2 - 2, fw, 4, WHITE)
    cv.fill(dx + 4 + fw // 2 - 1, dy + 4, 2, fh, BRICK)
    cv.fill(dx + 4, dy + 4 + fh // 2 - 1, fw, 2, BRICK)
    # document text lines
    for i in range(3):
        yy = dy + int(dh * 0.38) + i * max(4, int(h * 0.09))
        cv.hline(dx + 6, yy, dw - 12, (150, 145, 135))
    # red FROZEN stamp: thick ring + thick diagonal bar
    sx, sy = dx + dw - int(dw * 0.26), dy + dh - int(dh * 0.30)
    sr = max(7, int(min(w, h) * 0.17))
    for rr in (sr, sr - 2, sr - 4):
        cv.circle(sx, sy, max(2, rr), BRICK, filled=False)
    for do in (-1, 0, 1):
        cv.line(sx - sr + 2, sy + sr - 2 + do, sx + sr - 2, sy - sr + 2 + do,
                BRICK)

def art_ship(cv, x, y, w, h):
    """China-Canada: a container ship at sea under a pale sky."""
    cv.fill(x, y, w, h, (176, 205, 222))
    cv.fill(x, y + h * 2 // 3, w, h // 3, SEA)
    # containers
    bx0, by0 = x + int(w * 0.14), y + int(h * 0.34)
    bw, bh = int(w * 0.62), int(h * 0.30)
    cols = [BRICK, (30, 90, 140), GOLD, (40, 120, 80), (150, 60, 90)]
    for row in range(2):
        for col in range(4):
            ccx = bx0 + col * (bw // 4) + 1
            ccy = by0 + row * (bh // 2) + 1
            cv.fill(ccx, ccy, bw // 4 - 2, bh // 2 - 2, cols[(row * 4 + col) % 5])
    # bridge tower + funnel
    cv.fill(bx0 + bw + 2, by0 - int(h * 0.10), int(w * 0.08), int(h * 0.40),
            WHITE)
    cv.fill(bx0 + bw + 2, by0 - int(h * 0.10), int(w * 0.08),
            max(3, int(h * 0.05)), BRICK)
    # hull
    hy = y + h * 2 // 3
    cv.poly([(x + int(w * 0.06), hy), (x + int(w * 0.94), hy),
             (x + int(w * 0.88), hy + int(h * 0.20)),
             (x + int(w * 0.12), hy + int(h * 0.20))], (24, 34, 44))
    # mast flags: China red, Canada red-white
    mx = bx0 + bw + int(w * 0.04)
    cv.vline(mx, by0 - int(h * 0.22), int(h * 0.14), (60, 50, 40))
    cv.fill(mx + 1, by0 - int(h * 0.22), max(8, int(w * 0.06)),
            max(5, int(h * 0.07)), BRICK)
    cv.fill(mx + 1, by0 - int(h * 0.13), max(8, int(w * 0.06)),
            max(5, int(h * 0.07)), WHITE)
    # waves
    for wy in (0.76, 0.86):
        cv.hline(x + int(w * 0.06), _ry(y, h, wy), int(w * 0.5),
                 (140, 180, 200))
        cv.hline(x + int(w * 0.55), _ry(y, h, wy) + 4, int(w * 0.38),
                 (140, 180, 200))


def art_plane(cv, x, y, w, h):
    """Siberia An-12: a big transport plane over dark hills, smoke trail."""
    cv.fill(x, y, w, h, (20, 32, 54))
    cv.fill(x, y + h * 3 // 4, w, h // 4, (30, 38, 44))
    # smoke trail behind the plane: discs shrinking as they drift right
    for sx, sy, sr in ((0.80, 0.30, 0.10), (0.86, 0.24, 0.12),
                       (0.92, 0.30, 0.08), (0.88, 0.38, 0.06)):
        cv.disc(_rx(x, w, sx), _ry(y, h, sy), max(3, int(w * sr)),
                (150, 150, 146))
    cv.disc(_rx(x, w, 0.86), _ry(y, h, 0.28), max(3, int(w * 0.05)),
            (232, 120, 50))
    # big plane, nose down, flying left — deep fuselage, big wing, engines
    def _pp(fx, fy):
        return _rx(x, w, fx), _ry(y, h, fy)
    cv.poly([_pp(0.74, 0.38), _pp(0.30, 0.50), _pp(0.18, 0.55),
             _pp(0.20, 0.63), _pp(0.34, 0.61), _pp(0.76, 0.50)],
            (228, 228, 222))
    # cockpit windows near the nose
    cv.poly([_pp(0.70, 0.41), _pp(0.76, 0.44), _pp(0.74, 0.48),
             _pp(0.68, 0.45)], (52, 78, 100))
    # big high wing sweeping down-right
    cv.poly([_pp(0.42, 0.58), _pp(0.52, 0.84), _pp(0.62, 0.58)],
            (205, 205, 198))
    # engine nacelles under the wing
    for ex0 in (0.46, 0.56):
        cv.fill(_pp(ex0, 0.66)[0] - 2, _pp(ex0, 0.66)[1], 5, 8,
                (180, 180, 175))
    # tail fin
    cv.poly([_pp(0.62, 0.42), _pp(0.68, 0.22), _pp(0.74, 0.44)],
            (205, 205, 198))
    # hills, two defined ridges
    cv.poly([_pp(0.00, 1.00), _pp(0.18, 0.72), _pp(0.38, 1.00)],
            (52, 62, 70))
    cv.poly([_pp(0.55, 1.00), _pp(0.74, 0.76), _pp(0.95, 1.00)],
            (44, 54, 62))

def art_cricket(cv, x, y, w, h):
    """Dhoni IPL: bat, red ball and stumps on a green outfield."""
    cv.fill(x, y, w, h, (26, 96, 52))
    cv.fill(x, y + h * 3 // 4, w, h // 4, (18, 74, 40))
    cx, cy = x + w // 2, y + h // 2
    # pitch strip
    cv.fill(cx - int(w * 0.16), y + int(h * 0.18), int(w * 0.32),
            int(h * 0.64), (214, 186, 140))
    # stumps: three tall cream bars with bails on top
    for i in range(3):
        sx = cx - 10 + i * 9
        cv.fill(sx, y + int(h * 0.20), 6, int(h * 0.20), (250, 246, 236))
    cv.fill(cx - 12, y + int(h * 0.18), 24, 4, (250, 246, 236))
    # bat: wide flat blade angled down-right + thick handle
    cv.poly([(cx - 4, cy - int(h * 0.10)), (cx + int(w * 0.14),
             cy + int(h * 0.26)), (cx + int(w * 0.08), cy + int(h * 0.30)),
             (cx - 10, cy - int(h * 0.04))], (232, 196, 110))
    cv.fill(cx - 6, cy - int(h * 0.24), 7, int(h * 0.16), (120, 80, 40))
    # red ball, bigger, with a white seam
    cv.disc(cx + int(w * 0.26), cy + int(h * 0.26), max(5, int(w * 0.06)),
            BRICK)
    cv.disc(cx + int(w * 0.26), cy + int(h * 0.26), max(2, int(w * 0.02)),
            WHITE)

def art_satellite(cv, x, y, w, h):
    """Voyager 1: a probe with gold panels in deep space, signal arcs."""
    cv.fill(x, y, w, h, (8, 14, 30))
    for sx, sy in ((0.10, 0.12), (0.26, 0.06), (0.46, 0.14), (0.66, 0.08),
                   (0.88, 0.12), (0.16, 0.30), (0.92, 0.30), (0.06, 0.55),
                   (0.94, 0.55), (0.36, 0.06), (0.76, 0.22), (0.10, 0.80)):
        cv.fill(_rx(x, w, sx), _ry(y, h, sy), 2, 2, WHITE)
    cx, cy = x + int(w * 0.42), y + int(h * 0.50)
    # gold panels left and right of the bus, bigger, with a bright top edge
    cv.fill(cx - int(w * 0.32), cy - int(h * 0.12), int(w * 0.24),
            int(h * 0.24), GOLD)
    cv.fill(cx + int(w * 0.08), cy - int(h * 0.12), int(w * 0.24),
            int(h * 0.24), GOLD)
    cv.fill(cx - int(w * 0.32), cy - int(h * 0.12), int(w * 0.24), 3,
            GOLD_LT)
    cv.fill(cx + int(w * 0.08), cy - int(h * 0.12), int(w * 0.24), 3,
            GOLD_LT)
    # panel grid lines so they read as solar cells
    cv.vline(cx - int(w * 0.20), cy - int(h * 0.12), int(h * 0.24),
             (150, 110, 40))
    cv.vline(cx + int(w * 0.20), cy - int(h * 0.12), int(h * 0.24),
             (150, 110, 40))
    # bus, bigger, with a small antenna mast
    cv.fill(cx - int(w * 0.08), cy - int(h * 0.16), int(w * 0.16),
            int(h * 0.32), (200, 200, 195))
    cv.fill(cx - int(w * 0.08), cy - int(h * 0.16), int(w * 0.16), 3,
            WHITE)
    cv.vline(cx, cy - int(h * 0.30), int(h * 0.14), (200, 200, 195))
    cv.disc(cx, cy - int(h * 0.30), 2, (240, 200, 110))
    # dish: bigger cone pointing right
    cv.poly([(cx + int(w * 0.08), cy - int(h * 0.10)),
             (cx + int(w * 0.24), cy - int(h * 0.22)),
             (cx + int(w * 0.24), cy + int(h * 0.06)),
             (cx + int(w * 0.08), cy + int(h * 0.02))], (170, 180, 190))
    # two signal arcs radiating from the dish
    for rr, n in ((0.06, 9), (0.12, 13)):
        for k in range(n):
            a = -0.9 + k * (1.8 / max(1, n - 1))
            px = cx + int(w * 0.30) + int(math.cos(a) * w * rr)
            py = cy - int(h * 0.05) + int(math.sin(a) * h * rr * 1.6)
            cv.disc(px, py, 2, (120, 200, 230))


# ---------------------------------------------------------------- stories
# All first reported on Wednesday 18 November 2026 (AP, Reuters, AFP,
# BBC, Al Jazeera, UN News and the day's wires). Disputed claims are
# worded as claims, never as fact.
HERO = [
    {"n": 1, "kicker": "MIDDLE EAST \u00b7 CONFLICT",
     "headline": "US and Iran trade fire over Bahrain",
     "body": ("US jets hit a Qeshm site after drones hit a US radar."),
     "pin": (50.6, 26.2), "art": art_jet},
    {"n": 2, "kicker": "EUROPE \u00b7 WAR",
     "headline": "Crimea bridge loses a second span",
     "body": ("A second strike felled the road arch; the rail arch "
              "stands."),
     "pin": (38.5, 45.3), "art": art_bridge},
    {"n": 3, "kicker": "ASIA \u00b7 DIPLOMACY",
     "headline": "Trump in Manila, then to Shenzhen",
     "body": ("Manila talks; Xi\u2013Putin trilateral set for Thursday."),
     "pin": (121.0, 14.6), "art": art_skyline},
]

SMALL = [
    {"n": 4, "kicker": "MARKETS \u00b7 TECHNOLOGY",
     "headline": "Nvidia revenue doubles to $115.8bn",
     "body": ("Sales rose 103%; board bars Huang's return."),
     "pin": (-121.9, 37.4), "art": art_chip},
    {"n": 5, "kicker": "ISRAEL \u00b7 POLITICS",
     "headline": "Knesset picks Kahana as speaker",
     "body": ("Kahana replaces Ohana on Arab votes."),
     "pin": (35.2, 31.8), "art": art_parliament},
    {"n": 6, "kicker": "EUROPE \u00b7 UKRAINE",
     "headline": "EU proposes a \u20ac45bn loan for Ukraine",
     "body": ("It covers two-thirds of Kyiv's 2027 gap."),
     "pin": (4.35, 50.85), "art": art_eu},
    {"n": 7, "kicker": "ASIA \u00b7 WEATHER",
     "headline": "Cyclone Akvan nears Andhra Pradesh",
     "body": ("Landfall Friday, gusts to 145 km/h."),
     "pin": (80.3, 15.9), "art": art_cyclone},
    {"n": 8, "kicker": "BRITAIN \u00b7 SANCTIONS",
     "headline": "Britain sanctions settlement builders",
     "body": ("Eight firms and Tzav 9 face asset freezes."),
     "pin": (-0.1, 51.5), "art": art_sanctions},
    {"n": 9, "kicker": "TRADE \u00b7 CHINA\u2013CANADA",
     "headline": "China cuts tariffs as Xi meets Carney",
     "body": ("C$400m relief on pork and seafood."),
     "pin": (116.4, 39.9), "art": art_ship},
    {"n": 10, "kicker": "DISASTER \u00b7 SIBERIA",
     "headline": "An-12 crashes in Siberia; 19 dead",
     "body": ("All 19 aboard killed."),
     "pin": (100.0, 62.0), "art": art_plane},
    {"n": 11, "kicker": "SPORT \u00b7 CRICKET",
     "headline": "Dhoni ends IPL playing career",
     "body": ("IPL's great finisher retires."),
     "pin": (80.2, 13.0), "art": art_cricket},
    {"n": 12, "kicker": "SPACE",
     "headline": "Voyager 1 nears one light-day from Earth",
     "body": ("Humanity's farthest spacecraft."),
     "pin": (-80.6, 28.4), "art": art_satellite},
]

ALSO = [
    (13, "MONGOLIA", "President quits"),
    (14, "NORTH KOREA", "Missiles to Sea of Japan"),
    (15, "ROMANIA", "5.3 quake; felt in Bucharest"),
    (16, "FRANCE", "146,000 march; unions: 500k"),
    (17, "JAPAN", "Scrambles jets; Russian planes"),
    (18, "GAZA", "Peace board: ceasefire may fail"),
    (19, "INDIA", "Beat Pakistan 2-1; 10th title"),
    (20, "UKRAINE", "UN: 372 civilians dead in Oct."),
    (21, "USA", "Loses measles elimination status"),
    (22, "GUINEA", "224 jailed in gold crackdown"),
    (23, "JORDAN\u2013IRAQ", "Both block Telegram"),
    (24, "THAILAND", "US trade deal reached"),
    (25, "KOREA", "IMF lifts growth to 3.9%"),
    (26, "AUSTRALIA", "Sanctions on settlements"),
    (27, "FILM", "Pattinson is next James Bond"),
    (28, "GENEVA", "UN treaty on robot arms"),
    (29, "GERMANY", "Drone regiment formed"),
    (30, "ESTONIA", "Shuts Russia border 1 Dec"),
    (31, "COSTA RICA", "Journalist shot dead"),
    (32, "SUDAN", "Drones killed 1,630 civilians"),
    (33, "COP31", "Draft seeks fossil-fuel exit"),
    (34, "AMAZON", "$7bn for India renewables"),
    (35, "VATICAN", "Pope Leo ends S. America tour"),
]

NUMBERS = [
    ("$115.8bn", "Nvidia revenue, up 103%"),
    ("66\u201352", "Kahana's winning margin"),
    ("145 km/h", "Akvan's gusts at landfall"),
    ("200,000", "People leaving the coast"),
]

# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)

    # masthead
    cv.fill(0, 0, W, 108, NAVY)
    draw_text(cv, 24, 26, "THE DAY IN WORLD NEWS", 11, GOLD_LT,
              SERIF, pen_frac=0.15, tracking=1.0)
    right = "35 STORIES \u00b7 6 CONTINENTS \u00b7 ONE PAGE"
    draw_text(cv, W - 24 - SERIF.text_w(right, 11, 1.8, 1.0), 26, right, 11,
              GOLD_LT, SERIF, pen_frac=0.15, tracking=1.0)
    draw_text(cv, 24, 78, "Wednesday 18 November 2026", 42, WHITE,
              SERIF, pen_frac=0.14)
    draw_text(cv, 24, 100,
              "Every story on this page happened, or was first reported, on this day.",
              11, (200, 210, 205), SERIF, pen_frac=0.14)
    cv.fill(0, 108, W, 4, GOLD)

    # hero row: three big illustrated stories (116-326)
    hw, hh, gap = 318, 210, 11
    hy = 116
    for i, s in enumerate(HERO):
        hx = 24 + i * (hw + gap)
        cv.fill(hx, hy, hw, hh, CARD)
        cv.rect(hx, hy, hw, hh, INK, lw=1)
        s["art"](cv, hx + 2, hy + 2, hw - 4, 88)
        cv.hline(hx + 2, hy + 94, hw - 4, INK)
        tx = hx + 14
        ty = hy + 108
        cv.circle(tx + 8, ty - 3, 9, BRICK)
        draw_text(cv, tx + 4, ty, str(s["n"]), 11, WHITE, SERIF, pen_frac=0.15)
        draw_text(cv, tx + 24, ty, s["kicker"], 11, BRICK, SERIF,
                  pen_frac=0.15, tracking=0.5)
        hl = wrap(SERIF, s["headline"], hw - 28, 19, 2.7)[:2]
        yy = draw_para(cv, tx, ty + 30, hl, 19, INK, 26, SERIF, pen_frac=0.16)
        bl = wrap(SERIF, s["body"], hw - 28, 11.5, 1.6)[:2]
        draw_para(cv, tx, yy + 2, bl, 11.5, (48, 44, 38), 15, SERIF,
                  pen_frac=0.14)

    # small rows: nine stories, big icon left, text right (334-678)
    sw, sh = 318, 112
    for i, s in enumerate(SMALL):
        sx = 24 + (i % 3) * (sw + gap)
        sy = 334 + (i // 3) * (sh + 8)
        cv.fill(sx, sy, sw, sh, CARD)
        cv.rect(sx, sy, sw, sh, INK, lw=1)
        s["art"](cv, sx + 8, sy + 14, 72, 72)
        cv.vline(sx + 88, sy + 8, sh - 16, (200, 195, 180))
        tx = sx + 98
        ty = sy + 20
        cv.circle(tx + 7, ty - 3, 8, BRICK)
        draw_text(cv, tx + 4, ty, str(s["n"]), 10, WHITE, SERIF, pen_frac=0.15)
        draw_text(cv, tx + 21, ty, s["kicker"], 10, BRICK, SERIF,
                  pen_frac=0.15, tracking=0.4)
        hl = wrap(SERIF, s["headline"], sw - 98 - 12, 14, 2.0)[:2]
        yy = draw_para(cv, tx, ty + 28, hl, 14, INK, 19, SERIF, pen_frac=0.16)
        bl = wrap(SERIF, s["body"], sw - 98 - 12, 11, 1.6)[:2]
        draw_para(cv, tx, yy, bl, 11, (48, 44, 38), 14, SERIF,
                  pen_frac=0.14)

    # by the numbers strip (686-734): figures centred in their columns
    ny = 686
    cv.fill(24, ny, 976, 48, CREAM)
    cv.rect(24, ny, 976, 48, INK, lw=1)
    draw_text(cv, 24, ny + 20, "BY THE", 12, BRICK, SERIF, pen_frac=0.15,
              tracking=0.5)
    draw_text(cv, 24, ny + 36, "NUMBERS", 12, BRICK, SERIF, pen_frac=0.15,
              tracking=0.5)
    cv.vline(24 + 110, ny + 8, 32, (200, 195, 180))
    col_w = (976 - 110) // 4
    for i, (fig, cap) in enumerate(NUMBERS):
        ccx = 24 + 110 + i * col_w + col_w // 2
        if i:
            cv.vline(24 + 110 + i * col_w - 8, ny + 10, 28, (200, 195, 180))
        draw_text_c(cv, ccx, ny + 28, fig, 22, INK, SERIF, pen_frac=0.15)
        draw_text_c(cv, ccx, ny + 42, cap, 10, MUTED, SERIF, pen_frac=0.14)

    # bottom band: map + also list (742-968)
    by = 742
    bh = 226
    cv.fill(24, by, 340, bh, CARD)
    cv.rect(24, by, 340, bh, INK, lw=1)
    draw_text(cv, 36, by + 18, "WHERE THE NEWS HAPPENED", 12, INK, SERIF,
              pen_frac=0.15, tracking=0.5)
    draw_text(cv, 36, by + 32, "Numbered dots mark stories 1\u201312.",
              10, MUTED, SERIF, pen_frac=0.14)
    draw_map(cv, 36, by + 40, cols=80, rows=44, sx=4, sy=4, dot=3)
    pins = [(s["n"], s["pin"]) for s in HERO + SMALL]
    # nudge the two Middle East pins apart so their discs don't overlap
    PIN_NUDGE = {1: (5, 4), 5: (-5, -4)}
    for n, (lon, lat) in pins:
        px, py = pin_xy(36, by + 40, lon, lat, cols=80, rows=44, sx=4, sy=4)
        dx, dy = PIN_NUDGE.get(n, (0, 0))
        draw_pin(cv, px + dx, py + dy, n)

    cv.fill(376, by, 624, bh, CARD)
    cv.rect(376, by, 624, bh, INK, lw=1)
    draw_text(cv, 388, by + 18, "ALSO ON 18 NOVEMBER \u2014 23 MORE STORIES",
              13, INK, SERIF, pen_frac=0.15, tracking=0.3)
    cols = [ALSO[:12], ALSO[12:]]
    for ci, items in enumerate(cols):
        cx = 388 + ci * 312
        yy = by + 40
        for n, place, text in items:
            s = "%d. %s \u2014 %s" % (n, place, text)
            lines = wrap(SERIF, s, 292, 9, 1.4)[:2]
            yy = draw_para(cv, cx, yy, lines, 9, (48, 44, 38), 13, SERIF,
                           pen_frac=0.14)
            yy += 2

    # footer
    cv.fill(24, 976, 976, 2, INK)
    foot = ("Sources: AP \u00b7 Reuters \u00b7 AFP \u00b7 BBC \u00b7 Al Jazeera \u00b7 UN News. "
            "Original drawings.")
    draw_text(cv, 24, 990, foot, 10, MUTED, SERIF, pen_frac=0.14)
    draw_text(cv, 24, 1004, "The world in one picture \u2014 35 stories from "
              "Wednesday 18 November 2026. Disputed claims are attributed.",
              10, MUTED, SERIF, pen_frac=0.14)
    return cv

def main():
    cv = build()
    data = encode_png(W, H, bytes(cv.px))
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    import hashlib
    print("entry.png %d bytes sha256=%s" % (len(data), hashlib.sha256(data).hexdigest()))

if __name__ == "__main__":
    main()
