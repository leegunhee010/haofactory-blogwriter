# -*- coding: utf-8 -*-
"""카드뉴스 PIL 엔진 — 브랜드별 템플릿을 순수 Pillow로 재현. PowerPoint 불필요.
브랜드 에셋: brands/<id>/cards/ (layout.json + s*.png), 폰트: assets/fonts 공용.
extract_template()으로 어떤 PPTX든 에셋+layout으로 추출(브랜드 등록용)."""
import io, os, json, random
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None   # 사용자 본인 사진 — 대형 이미지 허용(압축폭탄 방어 해제)
try:
    import numpy as _np
except Exception:
    _np = None

HERE = os.path.dirname(os.path.abspath(__file__))
FONTDIR = os.path.join(HERE, "assets", "fonts")
_HEAD_FONT = os.path.join(FONTDIR, "Pretendard-Bold.otf")
_LABEL_FONT = os.path.join(FONTDIR, "GmarketSansTTFBold.ttf")
_BODY_FONT = os.path.join(FONTDIR, "Pretendard-Regular.otf")
if not os.path.isfile(_BODY_FONT):
    _BODY_FONT = _HEAD_FONT

PALETTE = {"orange": (253, 111, 34), "yellow": (242, 178, 52), "green": (80, 178, 40),
           "blue": (108, 121, 214), "pink": (224, 106, 140)}

_layout_cache = {}
_recolor_cache = {}
_font_cache = {}


def _layout(assets_dir):
    if assets_dir not in _layout_cache:
        _layout_cache[assets_dir] = json.load(open(os.path.join(assets_dir, "layout.json"), encoding="utf-8"))
    return _layout_cache[assets_dir]


def _font(path, px):
    k = (path, px)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, px)
    return _font_cache[k]


def _remap(im, theme):
    """주황 장식 → 테마색 (흰→테마 tint 보존)."""
    im = im.convert("RGBA")
    if _np is not None:
        a = _np.asarray(im).astype("float32")
        mn = a[..., :3].min(axis=2)
        t = ((255.0 - mn) / (255 - 34)).clip(0, 1)[..., None]
        rgb = 255.0 * (1 - t) + _np.array(theme, "float32") * t
        out = _np.dstack([rgb, a[..., 3:4]]).clip(0, 255).astype("uint8")
        return Image.fromarray(out, "RGBA")
    px = im.load(); W, H = im.size
    for y in range(H):
        for x in range(W):
            r, g, b, al = px[x, y]
            if al < 5:
                continue
            tt = max(0.0, min(1.0, (255 - min(r, g, b)) / (255 - 34)))
            px[x, y] = (round(255 * (1 - tt) + theme[0] * tt), round(255 * (1 - tt) + theme[1] * tt),
                        round(255 * (1 - tt) + theme[2] * tt), al)
    return im


def _asset(assets_dir, name, box, theme, recolor):
    key = (assets_dir, name, theme if recolor else None)
    if key not in _recolor_cache:
        im = Image.open(os.path.join(assets_dir, name)).convert("RGBA")
        if recolor:
            im = _remap(im, theme)
        _recolor_cache[key] = im
    im = _recolor_cache[key]
    if im.size != (box[2], box[3]):
        im = im.resize((max(1, box[2]), max(1, box[3])), Image.LANCZOS)
    return im


def _paste(canvas, im, x, y):
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sx = max(0, -x); sy = max(0, -y)
    if sx or sy:
        im = im.crop((sx, sy, im.width, im.height)); x += sx; y += sy
    layer.paste(im, (x, y))
    return Image.alpha_composite(canvas, layer)


def _fit(path, W, H, seed, center=None, zoom=1.0):
    rnd = random.Random(seed)
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    im = ImageOps.exif_transpose(im)
    for E in (ImageEnhance.Brightness, ImageEnhance.Contrast, ImageEnhance.Color):
        im = E(im).enhance(rnd.uniform(0.96, 1.05))
    im = im.filter(ImageFilter.UnsharpMask(1.2, rnd.randint(40, 70), 2))
    cx = 0.5 if center is None else max(0.0, min(1.0, center[0]))
    cy = rnd.uniform(0.42, 0.58) if center is None else max(0.0, min(1.0, center[1]))
    zoom = max(1.0, min(2.5, float(zoom or 1.0)))
    if zoom > 1.0:
        w, h = im.size; cw, ch = int(w / zoom), int(h / zoom)
        left = int((w - cw) * cx); top = int((h - ch) * cy)
        im = im.crop((left, top, left + cw, top + ch))
    return ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(cx, cy))


def _round(im, rad):
    rad = max(0, int(rad))
    if rad == 0:
        return im.convert("RGBA")
    im = im.convert("RGBA"); W, H = im.size
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=rad, fill=255)
    im.putalpha(m)
    return im


def _circle(im):
    im = im.convert("RGBA"); W, H = im.size
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([0, 0, W - 1, H - 1], fill=255)
    im.putalpha(m)
    return im


def _draw_text(canvas, box, text, font_path, size_pt, theme, align, pt2px):
    if not text:
        return canvas
    x, y, w, h = box
    col = (theme[0], theme[1], theme[2], 255)
    px = max(10, int(round(size_pt * pt2px)))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def build(fnt):   # 명시적 줄바꿈(\n) 먼저 분리 후, 박스 폭에 맞춰 단어 줄바꿈
        out = []
        for raw in str(text).split("\n"):
            raw = raw.strip()
            if not raw:
                out.append(""); continue
            if d.textlength(raw, font=fnt) <= w or " " not in raw:
                out.append(raw); continue
            cur = ""
            for wd in raw.split(" "):
                tt = (cur + " " + wd).strip()
                if d.textlength(tt, font=fnt) <= w:
                    cur = tt
                else:
                    if cur:
                        out.append(cur)
                    cur = wd
            if cur:
                out.append(cur)
        return out
    fnt = _font(font_path, px)
    lines = build(fnt)
    while px > 12 and lines and max((d.textlength(ln, font=fnt) for ln in lines if ln), default=0) > w:
        px -= 2; fnt = _font(font_path, px); lines = build(fnt)
    asc, desc = fnt.getmetrics(); lh = asc + desc
    cy = y + (h - lh * len(lines)) / 2
    for ln in lines:
        tw = d.textlength(ln, font=fnt) if ln else 0
        tx = x + (w - tw) / 2 if align == "center" else x
        d.text((tx, cy), ln, font=fnt, fill=col)
        cy += lh
    return Image.alpha_composite(canvas, layer)


def _two_lines(text):
    """텍스트를 길이 균형 맞춰 2줄로 강제 분할(공백 기준)."""
    text = " ".join(str(text).split())
    words = text.split(" ")
    if len(words) <= 1:
        return text
    best_i, best_diff = 1, 10 ** 9
    for i in range(1, len(words)):
        a = " ".join(words[:i]); b = " ".join(words[i:])
        diff = abs(len(a) - len(b))
        if diff < best_diff:
            best_diff, best_i = diff, i
    return " ".join(words[:best_i]) + "\n" + " ".join(words[best_i:])


def render_card(slide_idx, photo_path, headline, theme, out_path, assets_dir,
                center=None, zoom=1.0, seed="", subtitle="", body="", title=""):
    lay = _layout(assets_dir)
    SIZE = lay["size"]
    pt2px = SIZE / float(lay.get("pt_height", 810))
    theme_recolor = lay.get("theme_recolor", True)   # 기존(하오팩토리) layout은 키 없음 → True
    pround = lay.get("photo_round", 0.045)
    items = lay["slides"][slide_idx]
    sb = lay.get("slide_bg")
    bg = (sb[slide_idx] if sb and slide_idx < len(sb) else lay.get("bg", "FFFFFF")) or "FFFFFF"
    canvas = Image.new("RGBA", (SIZE, SIZE), tuple(int(bg[i:i+2], 16) for i in (0, 2, 4)) + (255,))

    def textcol(it):
        if not theme_recolor and it.get("color"):
            c = it["color"]
            return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
        return theme
    for it in items:
        role = it["role"]; box = it["box"]
        if role == "photo":
            if photo_path and os.path.isfile(photo_path):
                if it.get("shape") == "circle":
                    d = min(box[2], box[3])
                    ph = _fit(photo_path, d, d, seed or "0", center=center, zoom=zoom)
                    ph = _circle(ph)
                    canvas = _paste(canvas, ph, box[0] + (box[2] - d) // 2, box[1] + (box[3] - d) // 2)
                else:
                    ph = _fit(photo_path, box[2], box[3], seed or "0", center=center, zoom=zoom)
                    ph = _round(ph, int(min(box[2], box[3]) * pround))
                    canvas = _paste(canvas, ph, box[0], box[1])
        elif role in ("deco", "line", "logo"):
            canvas = _paste(canvas, _asset(assets_dir, it["asset"], box, theme, it.get("recolor", False)), box[0], box[1])
        elif role == "headline":
            txt = title if it.get("source") == "title" else (headline or "")
            if it.get("lines") == 2:
                txt = _two_lines(txt)
            canvas = _draw_text(canvas, box, txt, _HEAD_FONT, it.get("size", 40), textcol(it), it.get("align", "center"), pt2px)
        elif role == "subtitle":
            canvas = _draw_text(canvas, box, subtitle or "", _HEAD_FONT, it.get("size", 28), textcol(it), it.get("align", "center"), pt2px)
        elif role == "body":
            canvas = _draw_text(canvas, box, body or "", _BODY_FONT, it.get("size", 19), textcol(it), it.get("align", "center"), pt2px)
        elif role == "label":
            canvas = _draw_text(canvas, box, it.get("text", ""), _LABEL_FONT, it.get("size", 14), textcol(it), it.get("align", "left"), pt2px)
    canvas.convert("RGB").save(out_path, "PNG")
    return out_path


def make_cards(photo_paths, headlines, out_dir, assets_dir, theme=None, subtitle="", bodies=None, title=""):
    """카드 N장 생성. subtitle=표지부제, bodies=카드별본문, title=블로그제목(source=title 헤드라인용)."""
    os.makedirs(out_dir, exist_ok=True)
    bodies = bodies or []
    if theme is None:
        theme = PALETTE[random.choice([c for c in PALETTE if c != "orange"])]
    slides = _layout(assets_dir)["slides"]
    n = len(slides)
    salt = "%08x" % random.randrange(16 ** 8)
    pngs, cards = [], []
    hi = 0   # 카드 헤드라인은 '제목소스가 아닌 헤드라인 슬라이드'에만 순서대로
    for i in range(n):
        src = photo_paths[i % len(photo_paths)] if photo_paths else ""
        head_item = next((it for it in slides[i] if it.get("role") == "headline"), None)
        head = bod = ""
        if head_item is not None and head_item.get("source") != "title":
            head = headlines[hi] if hi < len(headlines) else ""
            bod = bodies[hi] if hi < len(bodies) else ""
            hi += 1
        sub = subtitle if any(it.get("role") == "subtitle" for it in slides[i]) else ""
        out = os.path.join(out_dir, "card%02d.png" % (i + 1))
        render_card(i, src, head, theme, out, assets_dir, seed=f"{salt}:{i}", subtitle=sub, body=bod, title=title)
        flds = []
        for it in slides[i]:
            r = it.get("role")
            if r == "headline":
                flds.append("title" if it.get("source") == "title" else "headline")
            elif r in ("subtitle", "body"):
                flds.append(r)
        pngs.append(out)
        cards.append({"src": src, "headline": head, "subtitle": sub, "body": bod, "title": title,
                      "fields": flds, "cx": 0.5, "cy": 0.5, "zoom": 1.0})
    state = {"theme": list(theme), "assets_dir": assets_dir, "cards": cards}
    json.dump(state, open(os.path.join(out_dir, "cards.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return {"pngs": pngs, "theme": "%02X%02X%02X" % theme, "cards": cards}


def load_state(out_dir):
    return json.load(open(os.path.join(out_dir, "cards.json"), encoding="utf-8"))


def save_state(out_dir, state):
    json.dump(state, open(os.path.join(out_dir, "cards.json"), "w", encoding="utf-8"), ensure_ascii=False)


def edit_card(out_dir, index, src=None, center=None, zoom=None,
              headline=None, subtitle=None, body=None, title=None):
    """cards.json 상태 기반으로 카드 1장만 다시 렌더(사진교체/위치·확대/글 수정)."""
    st = load_state(out_dir); c = st["cards"][index]
    adir = st.get("assets_dir")
    if src is not None:
        c["src"] = src; c["cx"] = 0.5; c["cy"] = 0.5; c["zoom"] = 1.0
    if center is not None:
        c["cx"], c["cy"] = float(center[0]), float(center[1])
    if zoom is not None:
        c["zoom"] = float(zoom)
    if headline is not None:
        c["headline"] = headline
    if subtitle is not None:
        c["subtitle"] = subtitle
    if body is not None:
        c["body"] = body
    if title is not None:
        c["title"] = title
    out = os.path.join(out_dir, "card%02d.png" % (index + 1))
    render_card(index, c["src"], c["headline"], tuple(st["theme"]), out, adir,
                center=(c["cx"], c["cy"]), zoom=c["zoom"], seed=f"edit:{index}",
                subtitle=c.get("subtitle", ""), body=c.get("body", ""), title=c.get("title", ""))
    save_state(out_dir, st)
    return out


def extract_template(pptx_path, out_assets_dir, theme_recolor=False, photo_round=0.0):
    """어떤 카드뉴스 PPTX든 장식 PNG + layout.json 으로 추출(브랜드 카드 등록용). 정사각 가정.
    - 사진 슬롯 = 슬라이드별 '비(非)풀블리드 이미지 중 최대 바이트'(배경 풀블리드는 고정 장식으로 유지).
    - theme_recolor=True면 하오팩토리식(주황 장식→테마색, 헤드라인=테마색). False면 디자인 그대로 + 헤드라인은 원래 색.
    - 헤드라인/라벨의 실제 글자색을 캡처."""
    from pptx import Presentation
    from pptx.oxml.ns import qn
    os.makedirs(out_assets_dir, exist_ok=True)
    prs = Presentation(pptx_path)
    W = prs.slide_width; H = prs.slide_height
    SIZE = 1080
    sc = SIZE / float(W)
    pt_height = H / 914400.0 * 72.0
    def px(v):
        return int(round(int(v) * sc)) if v is not None else 0
    def slide_bg(s):
        cSld = s._element.find(qn("p:cSld"))
        bgEl = cSld.find(qn("p:bg")) if cSld is not None else None
        if bgEl is not None:
            srgb = bgEl.findall(".//" + qn("a:srgbClr"))
            if srgb:
                return srgb[0].get("val")
        return "FFFFFF"
    spec = {"size": SIZE, "pt_height": round(pt_height, 2), "bg": "FFFFFF", "slide_bg": [],
            "theme_recolor": bool(theme_recolor), "photo_round": photo_round, "slides": []}
    for f in os.listdir(out_assets_dir):
        if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg"):
            try: os.remove(os.path.join(out_assets_dir, f))
            except Exception: pass
    for i, s in enumerate(prs.slides):
        pics = []   # (shape, box, nb, part)
        texts = []
        for sh in s.shapes:
            box = [px(sh.left), px(sh.top), px(sh.width), px(sh.height)]
            if sh.shape_type == 13:
                part = s.part.related_part(sh._element.blipFill.blip.rEmbed)
                pics.append((sh, box, len(part.blob), part))
            elif sh.has_text_frame and sh.text_frame.text.strip():
                texts.append((sh, box))
        # 사진 슬롯: 비풀블리드 중 최대 바이트(없으면 전체 최대)
        def fullbleed(b):
            return b[0] <= 2 and b[1] <= 2 and b[2] >= SIZE - 5 and b[3] >= SIZE - 5
        nonfb = [p for p in pics if not fullbleed(p[1])]
        photo_shape = max(nonfb or pics, key=lambda p: p[2]) if pics else None
        if photo_shape is not None:   # 너무 작으면(타이틀카드 장식) 사진 슬롯 아님
            pb = photo_shape[1]
            if pb[2] * pb[3] < 80000:
                photo_shape = None
        items = []
        for j, (sh, box, nb, part) in enumerate(pics):
            if photo_shape is not None and sh is photo_shape[0]:
                items.append({"role": "photo", "box": box})
            else:
                ext = os.path.splitext(part.partname)[1] or ".png"
                asset = "s%d_%d%s" % (i, j, ext)
                with open(os.path.join(out_assets_dir, asset), "wb") as f:
                    f.write(part.blob)
                recolor = theme_recolor and (box[3] <= 3 or not (i == 0 and box[2] < 220 and box[1] < 160))
                items.append({"role": "deco", "box": box, "asset": asset, "recolor": bool(recolor)})
        def _fsz(sh):
            r = sh.text_frame.paragraphs[0].runs
            return (r[0].font.size.pt if r and r[0].font.size else 40)
        maxsz = max((_fsz(sh) for sh, _ in texts), default=0)
        head_used = False
        for sh, box in texts:
            tf = sh.text_frame; p0 = tf.paragraphs[0]; run = p0.runs[0] if p0.runs else None
            txt = tf.text.strip()
            fsz = (run.font.size.pt if run and run.font.size else 40)
            color = None
            try:
                if run and run.font.color and run.font.color.type is not None:
                    color = str(run.font.color.rgb)
            except Exception:
                pass
            # 슬라이드에서 가장 큰 글자 1개만 동적 헤드라인, 나머지는 고정 라벨(원문 유지)
            role = "headline" if (not head_used and fsz == maxsz and fsz >= 24) else "label"
            if role == "headline":
                head_used = True
            items.append({"role": role, "box": box, "text": (txt if role == "label" else ""),
                          "size": fsz, "color": color,
                          "align": "center" if (p0.alignment and p0.alignment == 2) else "left"})
        spec["slide_bg"].append(slide_bg(s))
        spec["slides"].append(items)
    json.dump(spec, open(os.path.join(out_assets_dir, "layout.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    _layout_cache.pop(out_assets_dir, None)
    nassets = len([f for f in os.listdir(out_assets_dir) if not f.endswith(".json")])
    return {"slides": len(spec["slides"]), "assets": nassets}
