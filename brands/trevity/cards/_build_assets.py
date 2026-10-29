# -*- coding: utf-8 -*-
"""트래비티 카드뉴스 디자인 1(코럴 핑크) 에셋 + layout.json 생성기.
브랜드 팔레트(trevity.com CSS): 포인트 #FA6781 · 연핑크 #FFF0F3 · 구분선 #FFD3DC · 제목 #1F1F1F · 본문 #434343.
색은 글마다 바뀌지 않고 브랜드 핑크 고정(auto_theme 없음, bg_palette=핑크 1색).
다시 만들려면: python brands/trevity/cards/_build_assets.py
"""
import os, json
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_LOGO = os.path.join(HERE, "_logo_src.png")      # trevity.com/assets/img/logo.png 원본(557x150)

SS = 4
PINK = (250, 103, 129)        # FA6781
SOFT = (255, 240, 243)        # FFF0F3
LINE = (255, 211, 220)        # FFD3DC
DARK = (31, 31, 31)
GREY = (238, 238, 238)


def canvas(w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def save(im, name):
    im.save(os.path.join(HERE, name))
    return name, im.size


# ── 표지: 연핑크 전면 배경 + 우상단 큰 핑크 원 + 좌하단 작은 원 ──
def build_coverbg(size=1080):
    im, d = canvas(size, size)
    s = size * SS
    d.rectangle([0, 0, s, s], fill=SOFT + (255,))
    d.ellipse([s * 0.66, -s * 0.28, s * 1.30, s * 0.36], fill=PINK + (255,))
    d.ellipse([-s * 0.16, s * 0.80, s * 0.16, s * 1.12], fill=LINE + (255,))
    return down(im, size, size)


# ── 표지: 흰 라운드 카드 + 부드러운 그림자 ──
def build_card(w=880, h=760, m=40):
    W, H = w + m * 2, h + m * 2
    sh = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([(m + 6) * SS, (m + 16) * SS, (m + w + 6) * SS, (m + h + 16) * SS],
                                         radius=28 * SS, fill=(250, 103, 129, 60))
    sh = down(sh, W, H).filter(ImageFilter.GaussianBlur(14))
    top, d = canvas(W, H)
    d.rounded_rectangle([m * SS, m * SS, (m + w) * SS, (m + h) * SS], radius=28 * SS, fill=(255, 255, 255, 255))
    return Image.alpha_composite(sh, down(top, W, H)), m


# ── 짧은 핑크 포인트 바(제목 위 아이브로우) ──
def build_dash(w=72, h=8):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=4 * SS, fill=PINK + (255,))
    return down(im, w, h)


# ── 핑크 알약(표지 하단 사이트 표기 배경) ──
def build_pill(w=300, h=64):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=(h // 2) * SS, fill=PINK + (255,))
    return down(im, w, h)


# ── 내지: 상단 얇은 핑크 헤더 라인 + 하단 그레이 라인 ──
def build_frame(size=1080):
    im, d = canvas(size, size)
    s = size * SS
    d.rectangle([0, 0, s, 10 * SS], fill=PINK + (255,))
    d.line([(64 * SS, 212 * SS), ((size - 64) * SS, 212 * SS)], fill=GREY + (255,), width=2 * SS)
    d.line([(64 * SS, (size - 70) * SS), ((size - 64) * SS, (size - 70) * SS)], fill=GREY + (255,), width=2 * SS)
    return down(im, size, size)


# ── 내지: 사진 뒤 연핑크 오프셋 패널 ──
def build_photopanel(W=900, H=520, off=22):
    im, d = canvas(W, H)
    d.rounded_rectangle([off * SS, off * SS, W * SS - 1, H * SS - 1], radius=18 * SS, fill=SOFT + (255,))
    return down(im, W, H)


def build_logo():
    im = Image.open(SRC_LOGO).convert("RGBA")
    return im


def main():
    a = {}
    a["coverbg"] = save(build_coverbg(), "coverbg.png")
    card, cm = build_card()
    a["card"] = save(card, "card.png")
    a["dash"] = save(build_dash(), "dash.png")
    a["pill"] = save(build_pill(), "pill.png")
    a["frame"] = save(build_frame(), "frame.png")
    a["panel"] = save(build_photopanel(), "photopanel.png")
    logo = build_logo()
    a["logo"] = save(logo, "logo.png")
    a["logo_sm"] = save(logo, "logo_sm.png")

    def box(key, x, y, w):
        name, (aw, ah) = a[key]
        return {"asset": name, "box": [int(x), int(y), int(w), int(round(w * ah / aw))]}

    def deco(key, x, y, w):
        b = box(key, x, y, w)
        return {"role": "deco", "box": b["box"], "asset": b["asset"], "recolor": False}

    HEAD_F = "Gmarket Sans Bold"
    BOLD_F = "Pretendard Bold"
    MED_F = "Pretendard Medium"
    PK, DK, BD = "FA6781", "1F1F1F", "434343"

    # ── 표지 ──
    cover = [
        deco("coverbg", 0, 0, 1080),
        deco("card", 100 - cm, 160 - cm, 880 + cm * 2),
        deco("logo", 391, 226, 298),
        deco("dash", 504, 330, 72),
        {"role": "headline", "box": [150, 372, 780, 330], "size": 94, "color": DK,
         "font": HEAD_F, "align": "center", "lines": 2},
        {"role": "subtitle", "box": [170, 728, 740, 64], "size": 36, "color": BD,
         "font": BOLD_F, "align": "center", "oneline": True},
        deco("pill", 390, 828, 300),
        {"role": "label", "box": [390, 840, 300, 40], "size": 26, "color": "FFFFFF",
         "font": BOLD_F, "align": "center", "text": "trevity.com"},
    ]

    def header():
        return [
            deco("frame", 0, 0, 1080),
            deco("logo_sm", 64, 60, 190),
            deco("dash", 64, 132, 56),
            {"role": "headline", "box": [64, 148, 952, 60], "size": 44, "color": DK,
             "font": BOLD_F, "align": "left"},
        ]

    # ── 내지 A: 사진 + 설명 ──
    photo_a = header() + [
        deco("panel", 90, 268, 900),
        {"role": "photo", "box": [90, 268, 878, 498], "round": 0.035},
        {"role": "body", "box": [120, 812, 840, 170], "size": 30, "color": BD,
         "font": MED_F, "align": "center", "phrase_break": True},
    ]

    # ── 내지 B: 체크리스트 ──
    bullets = header() + [
        {"role": "bullets", "box": [90, 262, 900, 720], "size": 38, "color": DK,
         "font": BOLD_F,
         "panel": "FFF0F3", "panel_round": 18, "pad": 44, "row_h": 132,
         "inset": 52, "icon": 44, "icon_gap": 34, "rule": "FFD3DC", "rule_w": 2,
         "max_rows": 5, "min_size": 28, "row_lines": 2,
         "fill": 0.62, "row_h_max": 1.55},
    ]

    spec = {
        "size": 1080, "pt_height": 1080.0, "bg": "FFFFFF",
        "slide_bg": ["FFFFFF", "FFFFFF", "FFFFFF"],
        "theme_recolor": False, "auto_theme": False, "photo_round": 0.035,
        "bg_palette": [PK],
        "pick_by_content": {"default": 1, "list": 2},
        "card_note": ("헤드라인은 12자 내외의 짧은 명사형으로(질문형·문장형 금지). "
                      "절차·순서·비용 구조·체크리스트·주의사항 성격의 카드는 본문설명을 한 문장 대신 "
                      "**짧은 구절 3~5개를 ' / '로 이어서** 쓴다(예: 위생허가 전 인지도 확보 / KOC 다수 후기 선점 / 쇼피 입점 동시 진행). "
                      "각 구절 14자 이내, 서술어 없이 명사형으로 끝낸다. 그 외 카드는 한 문장(35자 내외)으로 쓴다."),
        "slides": [cover, photo_a, bullets],
    }
    with open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    for k, (n, sz) in a.items():
        print("%-8s %-16s %s" % (k, n, sz))
    print("layout.json slides:", len(spec["slides"]))


if __name__ == "__main__":
    main()
