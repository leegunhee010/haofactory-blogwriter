# -*- coding: utf-8 -*-
"""본문용 '사진 모음' 이미지 — 카드뉴스에 쓴 원본 사진을 2장·4장씩 묶어 한 장으로 렌더한다.

규칙(사용자 지정):
- 한 글에 모음 3장. 기본 구성 4장 + 2장 + 2장.
- 한 사진은 한 모음에만 쓴다(모음끼리 사진이 겹치지 않는다).
- 카드 사진 7장으로 8칸을 채울 수 없으므로 모자란 만큼만 폴더의 다른 사진에서 보충한다.

collage.json = 이 글의 모음 상태(칸마다 어떤 원본을 썼는지). 사진을 바꾸면 이 파일만 고치고
해당 모음 한 장만 다시 렌더한다.
"""
import json
import os

from PIL import Image

CELL_RATIO = 1.4          # 칸 가로/세로 비율
DEF_W = 2000              # 표·차트와 같은 가로 해상도
GAP = 12                  # 사진 사이 흰 여백
BG = (255, 255, 255)
STATE = "collage.json"


def _cover(path, w, h):
    """칸을 꽉 채우도록 비율 유지 확대 후 가운데를 잘라낸다."""
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = max(w, int(round(sw * s))), max(h, int(round(sh * s)))
    im = im.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, (nh - h) // 2
    return im.crop((x, y, x + w, y + h))


def grid(n):
    """칸 수 → (열, 행). 2·4장은 2열, 3장은 3열."""
    cols = 2 if n in (2, 4) else (3 if n == 3 else max(1, n))
    return cols, (n + cols - 1) // cols


def render(paths, out_path, width=DEF_W, gap=GAP, bg=BG):
    n = len(paths)
    cols, rows = grid(n)
    cw = (width - gap * (cols - 1)) // cols
    ch = int(round(cw / CELL_RATIO))
    canvas = Image.new("RGB", (cw * cols + gap * (cols - 1), ch * rows + gap * (rows - 1)), bg)
    for i, p in enumerate(paths):
        r, c = divmod(i, cols)
        canvas.paste(_cover(p, cw, ch), (c * (cw + gap), r * (ch + gap)))
    canvas.save(out_path, "PNG")
    return os.path.basename(out_path)


def _load(out_dir):
    try:
        return json.load(open(os.path.join(out_dir, STATE), encoding="utf-8")) or {}
    except Exception:
        return {}


def _save(out_dir, st):
    try:
        json.dump(st, open(os.path.join(out_dir, STATE), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    except Exception:
        pass


def meta(out_dir):
    """프런트에 넘길 모음 정보 — [{img, n, files}] (files = 칸별 파일명)."""
    st = _load(out_dir)
    out = []
    for i, g in enumerate(st.get("groups") or []):
        name = "모음%d.png" % (i + 1)
        out.append({"img": name, "n": len(g), "files": [os.path.basename(p) for p in g]})
    return out


def _order(card_paths, extra_paths):
    """표지(1번) 사진은 글 맨 위에 이미 단독으로 나오므로 마지막 모음으로 미룬다."""
    pool = [p for p in (card_paths or []) if p and os.path.isfile(p)]
    seen = set(pool)
    spare = [p for p in (extra_paths or []) if p and os.path.isfile(p) and p not in seen]
    return (pool[1:] + pool[:1] + spare) if pool else spare


def make_collages(card_paths, extra_paths, out_dir, sizes=(4, 2, 2), width=DEF_W):
    """모음 이미지를 처음 만든다. 사진이 모자라면 빈 목록."""
    order = _order(card_paths, extra_paths)
    need = sum(sizes)
    if len(order) < need:
        return []
    groups, k = [], 0
    for n in sizes:
        groups.append(order[k:k + n])
        k += n
    names = [render(g, os.path.join(out_dir, "모음%d.png" % (i + 1)), width=width)
             for i, g in enumerate(groups)]
    _save(out_dir, {"sizes": list(sizes), "width": width, "groups": groups, "files": names})
    return names


def set_cell(out_dir, gi, ci, path, width=None):
    """모음 gi(0부터)의 ci번째 칸 사진을 바꾸고 그 모음만 다시 렌더한다."""
    st = _load(out_dir)
    groups = st.get("groups") or []
    if not (0 <= gi < len(groups)) or not (0 <= ci < len(groups[gi])):
        raise ValueError("칸을 찾을 수 없습니다.")
    if not (path and os.path.isfile(path)):
        raise ValueError("파일을 찾을 수 없습니다.")
    groups[gi][ci] = path
    st["groups"] = groups
    name = render(groups[gi], os.path.join(out_dir, "모음%d.png" % (gi + 1)),
                  width=width or st.get("width") or DEF_W)
    _save(out_dir, st)
    return name


def replace_photo(out_dir, old_path, new_path):
    """카드 사진을 교체했을 때 — 그 사진이 들어간 칸만 새 사진으로 바꾸고 해당 모음만 다시 렌더.
    사용자가 손으로 바꾼 다른 칸은 그대로 둔다."""
    st = _load(out_dir)
    groups = st.get("groups") or []
    if not groups or not (new_path and os.path.isfile(new_path)):
        return []
    changed = []
    for gi, g in enumerate(groups):
        hit = False
        for ci, p in enumerate(g):
            if p and old_path and os.path.normcase(p) == os.path.normcase(old_path):
                g[ci] = new_path
                hit = True
        if hit:
            changed.append(render(g, os.path.join(out_dir, "모음%d.png" % (gi + 1)),
                                  width=st.get("width") or DEF_W))
    if changed:
        st["groups"] = groups
        _save(out_dir, st)
    return changed


def rebuild(out_dir):
    """저장된 구성 그대로 모음을 전부 다시 렌더(파일이 지워졌을 때 복구용)."""
    st = _load(out_dir)
    groups = st.get("groups") or []
    out = []
    for gi, g in enumerate(groups):
        try:
            out.append(render(g, os.path.join(out_dir, "모음%d.png" % (gi + 1)),
                              width=st.get("width") or DEF_W))
        except Exception:
            pass
    return out
