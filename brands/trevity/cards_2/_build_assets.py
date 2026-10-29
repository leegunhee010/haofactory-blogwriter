# -*- coding: utf-8 -*-
"""트래비티 카드뉴스 디자인 2(매거진 풀블리드) 에셋 + layout.json 생성기.
디자인 1(레드·윈 계열의 '로고 좌상단 + 사진 패널 + 체크리스트' 구조)과 다르게:
  내지 A = 사진 풀블리드(상단 660px) → 흰 페이드 → 좌측 핑크 바 + 좌정렬 큰 제목 + 본문
  내지 B = 상단 핑크 블록(흰 로고·흰 제목) 위로 떠 있는 흰 패널 체크리스트
브랜드 팔레트(trevity.com CSS): 포인트 #FA6781 · 연핑크 #FFF0F3 · 구분선 #FFD3DC · 제목 #1F1F1F · 본문 #434343.
다시 만들려면: python brands/trevity/cards_2/_build_assets.py
"""
import os, json
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_LOGO = os.path.join(HERE, "_logo_src.png")      # trevity.com/assets/img/logo.png 원본(557x150)

SS = 4
PINK = (250, 103, 129)        # FA6781
PINK_L = (252, 140, 160)      # 밝은 핑크(블록 장식 원)
SOFT = (255, 240, 243)        # FFF0F3
LINE = (255, 211, 220)        # FFD3DC
DARK = (31, 31, 31)
WHITE = (255, 255, 255)


def canvas(w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def save(im, name):
    im.save(os.path.join(HERE, name))
    return name, im.size


# ── 표지(디자인 1과 동일 계열: 연핑크 배경 + 핑크 원 + 흰 카드) ──
def build_coverbg(size=1080):
    im, d = canvas(size, size)
    s = size * SS
    d.rectangle([0, 0, s, s], fill=SOFT + (255,))
    d.ellipse([s * 0.66, -s * 0.28, s * 1.30, s * 0.36], fill=PINK + (255,))
    d.ellipse([-s * 0.16, s * 0.80, s * 0.16, s * 1.12], fill=LINE + (255,))
    return down(im, size, size)


def build_card(w=880, h=760, m=40):
    W, H = w + m * 2, h + m * 2
    sh = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([(m + 6) * SS, (m + 16) * SS, (m + w + 6) * SS, (m + h + 16) * SS],
                                         radius=28 * SS, fill=(250, 103, 129, 60))
    sh = down(sh, W, H).filter(ImageFilter.GaussianBlur(14))
    top, d = canvas(W, H)
    d.rounded_rectangle([m * SS, m * SS, (m + w) * SS, (m + h) * SS], radius=28 * SS, fill=WHITE + (255,))
    return Image.alpha_composite(sh, down(top, W, H)), m


def build_dash(w=72, h=8):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=4 * SS, fill=PINK + (255,))
    return down(im, w, h)


def build_pill(w=300, h=64):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=(h // 2) * SS, fill=PINK + (255,))
    return down(im, w, h)


# ── 내지 A: 사진 하단 → 흰색 페이드(사진이 본문 영역으로 자연스럽게 녹아듦) ──
def build_fade(w=1080, h=240):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        t = y / (h - 1)
        a = int(255 * (t ** 1.6))
        for x in range(w):
            px[x, y] = (255, 255, 255, a)
    return im


# ── 내지 A: 사진 위 좌상단 작은 태그 알약(반투명 흰 + 핑크 글자용) ──
def build_tag(w=430, h=52):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=(h // 2) * SS, fill=WHITE + (235,))
    return down(im, w, h)


# ── 내지 A: 제목 왼쪽 세로 핑크 바 ──
def build_vbar(w=10, h=96):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=5 * SS, fill=PINK + (255,))
    return down(im, w, h)


# ── 내지 B: 상단 핑크 블록 + 우측 밝은 원 장식 ──
def build_pinkblock(w=1080, h=440):
    im, d = canvas(w, h)
    W, H = w * SS, h * SS
    d.rectangle([0, 0, W, H], fill=PINK + (255,))
    d.ellipse([W * 0.72, -H * 0.55, W * 1.18, H * 0.75], fill=PINK_L + (255,))
    d.ellipse([W * 0.86, H * 0.45, W * 1.06, H * 1.05], fill=(253, 165, 182, 255))
    return down(im, w, h)


# ── 내지 B: 떠 있는 흰 패널(부드러운 그림자) ──
def build_whitepanel(w=936, h=640, m=36):
    W, H = w + m * 2, h + m * 2
    sh = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([(m + 4) * SS, (m + 14) * SS, (m + w + 4) * SS, (m + h + 14) * SS],
                                         radius=26 * SS, fill=(31, 31, 31, 55))
    sh = down(sh, W, H).filter(ImageFilter.GaussianBlur(16))
    top, d = canvas(W, H)
    d.rounded_rectangle([m * SS, m * SS, (m + w) * SS, (m + h) * SS], radius=26 * SS, fill=WHITE + (255,))
    return Image.alpha_composite(sh, down(top, W, H)), m


def build_logo():
    return Image.open(SRC_LOGO).convert("RGBA")


def build_logo_white():
    im = Image.open(SRC_LOGO).convert("RGBA")
    a = im.split()[3]
    out = Image.new("RGBA", im.size, WHITE + (0,))
    out.putalpha(a)
    return out


def main():
    a = {}
    a["coverbg"] = save(build_coverbg(), "coverbg.png")
    card, cm = build_card()
    a["card"] = save(card, "card.png")
    a["dash"] = save(build_dash(), "dash.png")
    a["pill"] = save(build_pill(), "pill.png")
    a["fade"] = save(build_fade(), "fade.png")
    a["tag"] = save(build_tag(), "tag.png")
    a["vbar"] = save(build_vbar(), "vbar.png")
    a["pinkblock"] = save(build_pinkblock(), "pinkblock.png")
    wp, wm = build_whitepanel()
    a["whitepanel"] = save(wp, "whitepanel.png")
    a["logo"] = save(build_logo(), "logo.png")
    a["logo_sm"] = save(build_logo(), "logo_sm.png")
    a["logo_w"] = save(build_logo_white(), "logo_white.png")

    def deco(key, x, y, w, h=None):
        name, (aw, ah) = a[key]
        hh = h if h else int(round(w * ah / aw))
        return {"role": "deco", "box": [int(x), int(y), int(w), int(hh)], "asset": name, "recolor": False}

    HEAD_F = "Gmarket Sans Bold"
    BOLD_F = "Pretendard Bold"
    MED_F = "Pretendard Medium"
    PK, DK, BD, WH = "FA6781", "1F1F1F", "434343", "FFFFFF"

    # ── 표지 ──
    cover = [
        deco("coverbg", 0, 0, 1080),
        deco("card", 100 - cm, 160 - cm, 880 + cm * 2),
        deco("logo", 391, 226, 298),
        deco("dash", 504, 330, 72),
        {"role": "headline", "box": [150, 372, 780, 330], "size": 94, "color": DK,
         "font": HEAD_F, "align": "center", "line_gap": 22},   # 2줄 강제 없음: 짧은 키워드는 1줄, 길면 폭에 맞춰 자동 줄바꿈
        {"role": "subtitle", "box": [170, 728, 740, 64], "size": 36, "color": BD,
         "font": BOLD_F, "align": "center", "oneline": True},
        deco("pill", 390, 828, 300),
        {"role": "label", "box": [390, 840, 300, 40], "size": 26, "color": WH,
         "font": BOLD_F, "align": "center", "text": "trevity.com"},
    ]

    # ── 내지 A: 사진 풀블리드 + 페이드 + 좌정렬 제목·본문 ──
    photo_a = [
        {"role": "photo", "box": [0, 0, 1080, 660], "round": 0},
        deco("fade", 0, 430, 1080, 231),
        deco("tag", 60, 56, 430),
        {"role": "label", "box": [60, 56, 430, 52], "size": 21, "color": PK,
         "font": BOLD_F, "align": "center", "text": "GLOBAL INFLUENCER MARKETING"},
        deco("vbar", 72, 706, 10),
        {"role": "headline", "box": [106, 690, 900, 130], "size": 54, "color": DK,
         "font": HEAD_F, "align": "left"},
        {"role": "body", "box": [106, 838, 890, 130], "size": 31, "color": BD,
         "font": MED_F, "align": "left", "phrase_break": True},
        {"role": "label", "box": [72, 992, 400, 36], "size": 22, "color": PK,
         "font": BOLD_F, "align": "left", "text": "trevity.com"},
        deco("logo_sm", 858, 986, 150),
    ]

    # ── 내지 B: 핑크 헤더 블록 + 떠 있는 흰 패널 체크리스트 ──
    bullets = [
        deco("pinkblock", 0, 0, 1080, 440),
        deco("logo_w", 72, 70, 172),
        {"role": "headline", "box": [72, 150, 936, 190], "size": 58, "color": WH,
         "font": HEAD_F, "align": "left"},
        deco("whitepanel", 72 - wm, 372 - wm, 936 + wm * 2, 640 + wm * 2),
        {"role": "bullets", "box": [112, 392, 856, 600], "size": 36, "color": DK,
         "font": BOLD_F,
         "panel": "", "pad": 28, "row_h": 108,
         "inset": 36, "icon": 40, "icon_gap": 30, "rule": "F1F1F1", "rule_w": 2,
         "max_rows": 5, "min_size": 27, "row_lines": 2,
         "fill": 0.72, "row_h_max": 1.6},
        {"role": "label", "box": [0, 1034, 1080, 30], "size": 21, "color": PK,
         "font": BOLD_F, "align": "center", "text": "trevity.com"},
    ]

    spec = {
        "size": 1080, "pt_height": 1080.0, "bg": "FFFFFF",
        "slide_bg": ["FFFFFF", "FFFFFF", "FFFFFF"],
        "theme_recolor": False, "auto_theme": False, "photo_round": 0.0,
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
        print("%-10s %-16s %s" % (k, n, sz))
    print("layout.json slides:", len(spec["slides"]))


if __name__ == "__main__":
    main()
