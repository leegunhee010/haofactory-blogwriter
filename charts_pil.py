# -*- coding: utf-8 -*-
"""내용 기반 표·차트 이미지(PIL 순수, matplotlib 불필요).
색상은 그 글 카드뉴스 색(theme)을 넘겨받아 통일. 유형: 표/막대/원/선."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FROZEN = False
try:
    import sys
    FROZEN = getattr(sys, "frozen", False)
    HERE = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.abspath(__file__))
except Exception:
    HERE = os.path.dirname(os.path.abspath(__file__))
FONTDIR = os.path.join(HERE, "assets", "fonts")
_BOLD = os.path.join(FONTDIR, "Pretendard-Bold.otf")
_REG = os.path.join(FONTDIR, "Pretendard-Regular.otf")
INK = (34, 40, 49)
MUT = (120, 128, 138)
LINE = (228, 231, 235)

_fc = {}
def _F(path, px):
    k = (path, px)
    if k not in _fc:
        try:
            _fc[k] = ImageFont.truetype(path, px)
        except Exception:
            _fc[k] = ImageFont.truetype(_BOLD, px)
    return _fc[k]

def _tint(c, t):
    return tuple(int(round(255 * (1 - t) + c[i] * t)) for i in range(3))

def _readable(c):
    """배경색 c 위 텍스트 색 — 밝으면 검정, 어두우면 흰색."""
    lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    return (255, 255, 255) if lum < 150 else (30, 34, 40)

def _wrap(draw, text, font, maxw):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= maxw or not cur:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def render_table(out, title, headers, rows, color=(37, 99, 175), W=920):
    pad = 28
    tf = _F(_BOLD, 34); hf = _F(_BOLD, 23); cf = _F(_REG, 22)
    ncol = max(1, len(headers))
    inner = W - pad * 2
    w0 = int(inner * (0.30 if ncol > 2 else 0.5))
    wr = (inner - w0) // (ncol - 1) if ncol > 1 else inner
    colw = [w0] + [wr] * (ncol - 1)
    colx = [pad]
    for w in colw[:-1]:
        colx.append(colx[-1] + w)
    tmp = Image.new("RGB", (10, 10)); d0 = ImageDraw.Draw(tmp)
    def rowh(cells):
        h = 0
        for i, c in enumerate(cells[:ncol]):
            ls = _wrap(d0, c, cf, colw[i] - 24)
            h = max(h, len(ls) * 30 + 22)
        return max(h, 52)
    header_h = 56
    rhs = [rowh(r) for r in rows]
    title_h = 0
    if title:
        title_h = len(_wrap(d0, title, tf, inner)) * 44 + 16
    H = pad + title_h + header_h + sum(rhs) + pad
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    y = pad
    if title:
        for ln in _wrap(d, title, tf, inner):
            d.text((pad, y), ln, font=tf, fill=color); y += 44
        y += 16
    d.rounded_rectangle([pad, y, W - pad, y + header_h], radius=10, fill=color)
    htc = _readable(color)
    for i, htxt in enumerate(headers[:ncol]):
        d.text((colx[i] + colw[i] / 2, y + header_h / 2), str(htxt), font=hf, fill=htc, anchor="mm")
    y += header_h
    for ri, r in enumerate(rows):
        h = rhs[ri]
        if ri % 2 == 1:
            d.rectangle([pad, y, W - pad, y + h], fill=_tint(color, 0.06))
        for ci in range(ncol):
            cell = r[ci] if ci < len(r) else ""
            ls = _wrap(d, str(cell), cf, colw[ci] - 24)
            ty = y + (h - len(ls) * 30) / 2
            for ln in ls:
                if ci > 0:
                    d.text((colx[ci] + colw[ci] / 2, ty), ln, font=cf, fill=INK, anchor="ma")
                else:
                    d.text((colx[ci] + 14, ty), ln, font=cf, fill=INK)
                ty += 30
        d.line([pad, y + h, W - pad, y + h], fill=LINE, width=1)
        y += h
    d.rounded_rectangle([pad, pad + title_h, W - pad, H - pad], radius=10, outline=LINE, width=1)
    im.save(out); return out


def render_bar(out, title, data, color=(37, 99, 175), W=920, H=520):
    pad = 40
    tf = _F(_BOLD, 34); lf = _F(_BOLD, 21); vf = _F(_BOLD, 20)
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    y0 = pad
    if title:
        d.text((pad, y0), title, font=tf, fill=color); y0 += 56
    base_y = H - 74; top_y = y0 + 26
    mx = max((v for _, v in data), default=1) or 1
    n = max(1, len(data)); gap = 34
    bw = (W - pad * 2 - gap * (n - 1)) / n
    for i, (lab, v) in enumerate(data):
        bx = pad + i * (bw + gap)
        bh = (base_y - top_y) * (v / mx)
        by = base_y - bh
        c = _tint(color, 0.55 + 0.45 * (v / mx))
        d.rounded_rectangle([bx, by, bx + bw, base_y], radius=8, fill=c)
        d.text((bx + bw / 2, by - 8), _fmt(v), font=vf, fill=color, anchor="mb")
        for ln in _wrap(d, lab, lf, bw + gap - 6):
            d.text((bx + bw / 2, base_y + 10), ln, font=lf, fill=MUT, anchor="ma")
    d.line([pad, base_y, W - pad, base_y], fill=LINE, width=2)
    im.save(out); return out


def render_line(out, title, data, color=(37, 99, 175), W=920, H=520):
    pad = 44
    tf = _F(_BOLD, 34); lf = _F(_BOLD, 20); vf = _F(_BOLD, 19)
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    y0 = pad
    if title:
        d.text((pad, y0), title, font=tf, fill=color); y0 += 56
    base_y = H - 74; top_y = y0 + 34
    mx = max((v for _, v in data), default=1) or 1
    n = max(1, len(data))
    xs = [pad + (W - pad * 2) * (i / (n - 1 if n > 1 else 1)) for i in range(n)]
    ys = [base_y - (base_y - top_y) * (v / mx) for _, v in data]
    d.line([pad, base_y, W - pad, base_y], fill=LINE, width=2)
    if n > 1:
        d.line(list(zip(xs, ys)), fill=color, width=5, joint="curve")
    for i, (lab, v) in enumerate(data):
        d.ellipse([xs[i] - 8, ys[i] - 8, xs[i] + 8, ys[i] + 8], fill=color)
        d.text((xs[i], ys[i] - 16), _fmt(v), font=vf, fill=color, anchor="mb")
        d.text((xs[i], base_y + 10), str(lab), font=lf, fill=MUT, anchor="ma")
    im.save(out); return out


def render_pie(out, title, data, color=(37, 99, 175), W=920, H=520):
    pad = 40
    tf = _F(_BOLD, 34); lf = _F(_REG, 22); pf = _F(_BOLD, 20)
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    y0 = pad
    if title:
        d.text((pad, y0), title, font=tf, fill=color); y0 += 56
    total = sum(v for _, v in data) or 1
    R = min((H - y0 - pad) // 2, 170)
    cx, cy = pad + R, y0 + (H - y0 - pad) // 2
    S = 4
    big = Image.new("RGBA", (R * 2 * S, R * 2 * S), (0, 0, 0, 0)); bd = ImageDraw.Draw(big)
    ang = -90
    cols = [_tint(color, t) for t in (1.0, 0.78, 0.58, 0.42, 0.3, 0.2)]
    for i, (lab, v) in enumerate(data):
        sweep = 360 * v / total
        bd.pieslice([0, 0, R * 2 * S, R * 2 * S], ang, ang + sweep, fill=cols[i % len(cols)] + (255,))
        ang += sweep
    big = big.resize((R * 2, R * 2), Image.LANCZOS)
    im.paste(big, (cx - R, cy - R), big)
    lx = cx + R + 50; ly = y0 + 10
    for i, (lab, v) in enumerate(data):
        pct = 100 * v / total
        d.rounded_rectangle([lx, ly, lx + 26, ly + 26], radius=6, fill=cols[i % len(cols)])
        d.text((lx + 38, ly + 1), str(lab), font=lf, fill=INK)
        d.text((lx + 38, ly + 29), "%.0f%%" % pct, font=pf, fill=color)
        ly += 62
    im.save(out); return out


def _fmt(v):
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else ("%.1f" % f)
    except Exception:
        return str(v)


_KIND = {"표": "table", "table": "table", "막대": "bar", "bar": "bar",
         "원": "pie", "pie": "pie", "선": "line", "line": "line"}


def render_spec(out_path, spec, color=(37, 99, 175)):
    """spec = {"kind","title","headers","rows"(표) | "data"[(label,value)](차트)} → 이미지."""
    kind = _KIND.get(str(spec.get("kind", "")).strip(), "table")
    title = spec.get("title", "")
    if kind == "table":
        return render_table(out_path, title, spec.get("headers", []), spec.get("rows", []), color)
    data = [(str(l), _num(v)) for l, v in spec.get("data", []) if _num(v) is not None]
    if not data:
        return None
    if kind == "bar":
        return render_bar(out_path, title, data, color)
    if kind == "line":
        return render_line(out_path, title, data, color)
    if kind == "pie":
        return render_pie(out_path, title, data, color)
    return render_bar(out_path, title, data, color)


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except Exception:
        return None
