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


# 이 어미·기호로 끝나는 어절 뒤는 '의미 단위 경계' → 여기서 끊으면 자연스럽다(무겁고 / 기초 공사 필요)
_BREAK_ENDS = ("고", "며", "면", "서", "나", "지만", "는데", "도", ",", "·", ")", "및", "또는")
# 조사로 끝나는 어절 뒤 = 약한 경계(기초 공사와 / 앵커 고정이 …), 그 외(명사+명사 사이)는 가급적 끊지 않음
_SOFT_ENDS = ("와", "과", "에", "로", "을", "를", "이", "가", "은", "는", "의", "까지", "부터", "보다")

def _split_long(draw, word, font, maxw):
    """칸보다 긴 한 어절 → '·' '/' 우선, 안 되면 글자 단위로 쪼갠다(칸 밖으로 넘치지 않게)."""
    if draw.textlength(word, font=font) <= maxw:
        return [word]
    for sep in ("·", "/"):
        if sep in word:
            parts = word.split(sep)
            toks = [p + sep for p in parts[:-1]] + [parts[-1]]
            out, cur = [], ""
            for t in toks:
                if cur and draw.textlength(cur + t, font=font) > maxw:
                    out.append(cur); cur = t
                else:
                    cur += t
            if cur:
                out.append(cur)
            if all(draw.textlength(o, font=font) <= maxw for o in out):
                return out
    out, cur = [], ""
    for ch in word:
        if cur and draw.textlength(cur + ch, font=font) > maxw:
            out.append(cur); cur = ch
        else:
            cur += ch
    return out + ([cur] if cur else [])

def _wrap_cell(draw, text, font, maxw):
    """표 칸 줄바꿈 — 최소 줄 수를 유지하면서, 한 단어만 다음 줄로 떨어지는 '외톨이 줄'을 피하고
    의미 단위(…고 / …며 / ·)에서 끊으며 줄 길이를 고르게 맞춘다. 예) '무겁고 기초 공사 필요'
    → '무겁고 / 기초 공사 필요'(X '무겁고 기초 공사 / 필요'), '자외선 대비 / 도장 필요'."""
    from itertools import combinations
    words = []
    for w in str(text).split():
        words += _split_long(draw, w, font, maxw)
    if not words:
        return [""]
    full = " ".join(words)
    if draw.textlength(full, font=font) <= maxw:
        return [full]
    n = len(_wrap(draw, full, font, maxw))          # 최소 줄 수(순차 채우기 기준)
    m = len(words)
    if n >= m:
        return words
    W = lambda a, b: draw.textlength(" ".join(words[a:b]), font=font)
    best, best_cost = None, None
    tried = 0
    for k in (n, n + 1):                             # 같은 줄 수가 안 되면 한 줄 더까지만 허용
        if k > m:
            break
        for cuts in combinations(range(1, m), k - 1):
            tried += 1
            if tried > 6000:
                break
            b = (0,) + cuts + (m,)
            ws = [W(b[i], b[i + 1]) for i in range(k)]
            if max(ws) > maxw:
                continue
            cost = sum(((maxw - x) / maxw) ** 2 for x in ws)          # 줄 길이 고르게
            for c in cuts:                                             # 의미 경계에서 끊기면 가점, 명사 사이는 감점
                if words[c - 1].endswith(_BREAK_ENDS) or words[c] in ("및", "또는"):
                    cost -= 0.3
                elif words[c - 1].endswith(_SOFT_ENDS):
                    cost -= 0.15
                else:
                    cost += 0.15
            last = words[b[-2]:]
            if len(last) == 1 and len(last[0]) <= 3 and m > 1:        # '필요' 같은 외톨이 마지막 줄 강한 감점
                cost += 1.5
            cost += (k - n) * 2.0                                      # 줄 수 늘리기는 최후 수단
            if best_cost is None or cost < best_cost:
                best_cost, best = cost, b
        if best is not None:
            break
    if best is None:
        return _wrap(draw, full, font, maxw)
    return [" ".join(words[best[i]:best[i + 1]]) for i in range(len(best) - 1)]

def _col_widths(draw, headers, rows, hf, cf, inner, P, ncol, minw_floor):
    """열 너비를 내용 길이에 맞춰 배분 — 긴 문장이 든 열은 넓게, 짧은 열은 좁게(불필요한 줄바꿈 감소)."""
    nat, mn = [], []
    for i in range(ncol):
        cells = [str(r[i]) if i < len(r) else "" for r in rows]
        hw = draw.textlength(str(headers[i]) if i < len(headers) else "", font=hf)
        cw = max([draw.textlength(c, font=cf) for c in cells] + [0])
        lw = max([draw.textlength(w, font=cf) for c in cells for w in c.split()] + [0])
        nat.append(max(hw, cw) + P)
        mn.append(max(hw + P, lw + P, minw_floor))
    if sum(nat) <= inner:                       # 다 한 줄에 들어감 → 남는 폭을 고르게 나눔
        extra = (inner - sum(nat)) / ncol
        ws = [x + extra for x in nat]
    elif sum(mn) >= inner:                      # 최소폭도 안 들어감 → 비율 축소(긴 어절은 _split_long이 처리)
        ws = [x * inner / sum(mn) for x in mn]
    else:                                       # 최소폭 보장 후, 남는 폭을 '더 필요한 만큼' 비율로 배분
        rest = inner - sum(mn)
        need = [nat[i] - mn[i] for i in range(ncol)]
        tn = sum(need) or 1
        ws = [mn[i] + rest * need[i] / tn for i in range(ncol)]
    ws = [int(x) for x in ws]
    ws[-1] += inner - sum(ws)
    return ws


def render_table(out, title, headers, rows, color=(37, 99, 175), W=920):
    k = max(0.5, W / 920.0)          # W가 커지면(예: 2000px) 글자·여백도 같은 비율로 키운다(가독성 유지)
    S = lambda v: int(round(v * k))
    pad = S(28)
    tf = _F(_BOLD, S(34)); hf = _F(_BOLD, S(23)); cf = _F(_REG, S(22))
    lh, tlh, header_h = S(30), S(44), S(56)
    ncol = max(1, len(headers))
    inner = W - pad * 2
    tmp = Image.new("RGB", (10, 10)); d0 = ImageDraw.Draw(tmp)
    colw = _col_widths(d0, headers, rows, hf, cf, inner, S(24), ncol, S(90))
    colx = [pad]
    for w in colw[:-1]:
        colx.append(colx[-1] + w)
    def rowh(cells):
        h = 0
        for i, c in enumerate(cells[:ncol]):
            ls = _wrap_cell(d0, c, cf, colw[i] - S(24))
            h = max(h, len(ls) * lh + S(22))
        return max(h, S(52))
    rhs = [rowh(r) for r in rows]
    title_h = 0
    if title:
        title_h = len(_wrap(d0, title, tf, inner)) * tlh + S(16)
    H = pad + title_h + header_h + sum(rhs) + pad
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    y = pad
    if title:
        for ln in _wrap(d, title, tf, inner):
            d.text((pad, y), ln, font=tf, fill=color); y += tlh
        y += S(16)
    d.rounded_rectangle([pad, y, W - pad, y + header_h], radius=S(10), fill=color)
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
            ls = _wrap_cell(d, str(cell), cf, colw[ci] - S(24))
            ty = y + (h - len(ls) * lh) / 2
            for ln in ls:
                if ci > 0:
                    d.text((colx[ci] + colw[ci] / 2, ty), ln, font=cf, fill=INK, anchor="ma")
                else:
                    d.text((colx[ci] + S(14), ty), ln, font=cf, fill=INK)
                ty += lh
        d.line([pad, y + h, W - pad, y + h], fill=LINE, width=max(1, S(1)))
        y += h
    d.rounded_rectangle([pad, pad + title_h, W - pad, H - pad], radius=S(10), outline=LINE, width=max(1, S(1)))
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


def render_spec(out_path, spec, color=(37, 99, 175), W=None):
    """spec = {"kind","title","headers","rows"(표) | "data"[(label,value)](차트)} → 이미지.
    W: 표 가로 픽셀(브랜드 table_width, 예 2000). 없으면 기본 920. 차트는 기본 크기."""
    kind = _KIND.get(str(spec.get("kind", "")).strip(), "table")
    title = spec.get("title", "")
    if kind == "table":
        try:
            W = int(W) if W else 0
        except Exception:
            W = 0
        if W >= 600:
            return render_table(out_path, title, spec.get("headers", []), spec.get("rows", []), color, W=W)
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
