# -*- coding: utf-8 -*-
"""윈차이나 카드뉴스 '디자인 2'(종이/네이비) 에셋 + layout.json 생성기.
네이비 + 하늘색 + 흰 종이 톤. 표지=종이+테이프+전구+연필, 내지=파란 테두리 + 로고헤더.
다시 만들려면: python brands/winchina/cards_2/_build_assets.py
"""
import os, json
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC_LOGO = os.path.join(ROOT, "brands", "winchina", "cards", "s0_8.png")

SS = 4                              # 슈퍼샘플링 배율(안티에일리어싱)
NAVY = (31, 78, 121)                # 제목·아이콘·로고
TAPE = (26, 66, 105)                # 표지 테이프
SKY = (206, 231, 248)               # 표지 배경 · 체크리스트 패널
LINE = (138, 182, 220)              # 내지 테두리
RULE = (169, 203, 230)              # 체크리스트 구분선
INK = (26, 26, 26)
BODY = (51, 51, 51)


def canvas(w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def save(im, name):
    p = os.path.join(HERE, name)
    im.save(p)
    return name, im.size


# ── 표지: 흰 종이 + 부드러운 그림자 ──────────────────────────────
def build_paper(w=900, h=904, m=40):
    W, H = w + m * 2, h + m * 2
    sh = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [(m + 8) * SS, (m + 14) * SS, (m + w + 4) * SS, (m + h + 10) * SS],
        radius=6 * SS, fill=(60, 90, 120, 70))
    sh = down(sh, W, H).filter(ImageFilter.GaussianBlur(11))
    top, d = canvas(W, H)
    d.rounded_rectangle([m * SS, m * SS, (m + w) * SS, (m + h) * SS],
                        radius=5 * SS, fill=(255, 255, 255, 255),
                        outline=(226, 232, 238, 255), width=2 * SS)
    return Image.alpha_composite(sh, down(top, W, H)), m


# ── 표지: 비스듬한 마스킹 테이프 ────────────────────────────────
def build_tape():
    im, d = canvas(340, 120)
    d.rectangle([14 * SS, 30 * SS, 326 * SS, 90 * SS], fill=TAPE + (255,))
    im = down(im, 340, 120).rotate(-7, expand=True, resample=Image.BICUBIC)
    return im.crop(im.getbbox())


# ── 표지: 전구 일러스트 ────────────────────────────────────────
def build_bulb(S=230):
    im, d = canvas(S, S)
    s = S * SS
    ORG = (245, 166, 35, 255)
    cx, cy, r = s * 0.5, s * 0.44, s * 0.235
    for a, ln in ((-90, 0.20), (-140, 0.19), (-40, 0.19), (-175, 0.16), (-5, 0.16)):
        import math
        rad = math.radians(a)
        x0, y0 = cx + math.cos(rad) * r * 1.35, cy + math.sin(rad) * r * 1.35
        x1, y1 = cx + math.cos(rad) * r * (1.35 + ln * 4), cy + math.sin(rad) * r * (1.35 + ln * 4)
        d.line([(x0, y0), (x1, y1)], fill=ORG, width=int(s * 0.036))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 248, 230, 255),
              outline=ORG, width=int(s * 0.05))
    d.polygon([(cx - r * 0.55, cy + r * 0.72), (cx + r * 0.55, cy + r * 0.72),
               (cx + r * 0.42, cy + r * 1.02), (cx - r * 0.42, cy + r * 1.02)],
              fill=(255, 248, 230, 255), outline=ORG, width=int(s * 0.04))
    d.rounded_rectangle([cx - r * 0.42, cy + r * 1.00, cx + r * 0.42, cy + r * 1.46],
                        radius=int(s * 0.02), fill=(176, 182, 190, 255))
    for k in (0.14, 0.30):
        y = cy + r * (1.00 + k * 1.5)
        d.line([(cx - r * 0.42, y), (cx + r * 0.42, y)], fill=(255, 255, 255, 255), width=int(s * 0.018))
    return down(im, S, S)


# ── 표지: 노란 연필(기울임) ─────────────────────────────────────
def build_pencil(W=150, H=470):
    im, d = canvas(W, H)
    w, h = W * SS, H * SS
    x0, x1 = w * 0.20, w * 0.80
    YEL = (247, 202, 69, 255)
    d.rounded_rectangle([x0, h * 0.10, x1, h * 0.74], radius=int(w * 0.04), fill=YEL)
    d.line([(w * 0.38, h * 0.10), (w * 0.38, h * 0.74)], fill=(226, 175, 40, 255), width=int(w * 0.03))
    d.line([(w * 0.62, h * 0.10), (w * 0.62, h * 0.74)], fill=(226, 175, 40, 255), width=int(w * 0.03))
    d.polygon([(x0, h * 0.74), (x1, h * 0.74), (w * 0.5, h * 0.955)], fill=(240, 219, 178, 255))
    d.polygon([(w * 0.40, h * 0.885), (w * 0.60, h * 0.885), (w * 0.5, h * 0.955)], fill=(52, 52, 58, 255))
    d.rectangle([x0, h * 0.045, x1, h * 0.105], fill=(190, 196, 204, 255))
    d.rounded_rectangle([x0, h * 0.005, x1, h * 0.06], radius=int(w * 0.12), fill=(241, 148, 138, 255))
    im = down(im, W, H).rotate(-22, expand=True, resample=Image.BICUBIC)
    return im.crop(im.getbbox())


# ── 표지 배경(연한 하늘색 전면) — recolor 대상이라 글마다 색이 바뀐다 ──
def build_coverbg(size=1080):
    return Image.new("RGBA", (size, size), SKY + (255,))


# ── 내지: 파란 테두리 프레임 ────────────────────────────────────
def build_frame(size=1080, inset=36, wd=3):
    im, d = canvas(size, size)
    d.rectangle([inset * SS, inset * SS, (size - inset) * SS, (size - inset) * SS],
                outline=LINE + (255,), width=wd * SS)
    return down(im, size, size)


# ── 내지: 제목 앞 네이비 세로 막대 ──────────────────────────────
def build_bar(w=8, h=132):
    im, d = canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=3 * SS, fill=NAVY + (255,))
    return down(im, w, h)


# ── 내지: 사진 뒤 흰 패널 + 하늘색 오프셋 ───────────────────────
def build_photopanel(W=880, H=500, off=18):
    im, d = canvas(W, H)
    d.rectangle([0, off * SS, (W - off) * SS, H * SS - 1], fill=SKY + (255,))
    d.rectangle([off * SS, 0, W * SS - 1, (H - off) * SS],
                fill=(255, 255, 255, 255), outline=LINE + (255,), width=2 * SS)
    return down(im, W, H)


# ── 로고: 브랜드 워드마크 원본 그대로(★색 바꾸지 말 것 — 원본 먹색 #231715 유지) ──
def build_logo():
    return Image.open(SRC_LOGO).convert("RGBA")


def main():
    a = {}
    paper, pm = build_paper()
    a["paper"] = save(paper, "paper.png")
    a["tape"] = save(build_tape(), "tape.png")
    a["bulb"] = save(build_bulb(), "bulb.png")
    a["pencil"] = save(build_pencil(), "pencil.png")
    a["coverbg"] = save(build_coverbg(), "coverbg.png")
    a["frame"] = save(build_frame(), "frame.png")
    a["bar"] = save(build_bar(), "bar.png")
    a["panel"] = save(build_photopanel(), "photopanel.png")
    logo = build_logo()
    a["logo"] = save(logo, "logo.png")
    a["logo_sm"] = save(logo, "logo_sm.png")

    def box(key, x, y, w):
        """가로폭 w에 맞춰 비율 유지 박스."""
        name, (aw, ah) = a[key]
        return {"asset": name, "box": [int(x), int(y), int(w), int(round(w * ah / aw))]}

    def deco(key, x, y, w, recolor=False):
        """recolor=True인 장식은 그 글의 대표색(사진에서 추출)으로 다시 칠해진다.
        진한 부분→대표색, 옅은 부분→대표색의 옅은 톤. 로고·사진·일러스트는 False로 원본 유지."""
        b = box(key, x, y, w)
        return {"role": "deco", "box": b["box"], "asset": b["asset"], "recolor": bool(recolor)}

    HEAD_F = "Gmarket Sans Bold"
    BOLD_F = "Pretendard Bold"
    MED_F = "Pretendard Medium"
    NV = "1F4E79"

    # ── 표지 ──
    cover = [
        deco("coverbg", 0, 0, 1080, True),
        deco("paper", 90 - pm, 84 - pm, 900 + pm * 2),
        deco("tape", 368, 52, 350, True),
        deco("bulb", 108, 104, 230),
        {"role": "headline", "box": [130, 300, 820, 370], "size": 132, "color": NV,
         "font": HEAD_F, "align": "center", "lines": 2, "auto_color": True},
        {"role": "subtitle", "box": [150, 690, 780, 68], "size": 38, "color": "1A1A1A",
         "font": BOLD_F, "align": "center", "oneline": True},
        deco("logo", 412, 838, 256),
        deco("pencil", 862, 612, 216),
    ]

    def header(title_h=144):
        return [
            deco("frame", 0, 0, 1080, True),
            # 로고는 옆 세로 막대(72~204)의 정중앙에 오도록 y를 맞춘다
            deco("logo_sm", 73, 138 - int(round(155 * 69 / 258 / 2)), 155),
            deco("bar", 258, 72, 8, True),
            {"role": "headline", "box": [297, 66, 700, title_h], "size": 50, "color": NV,
             "font": BOLD_F, "align": "left", "auto_color": True},
        ]

    # ── 내지 A: 사진 위 / 설명 아래 ──
    photo_a = header() + [
        deco("panel", 70, 440, 880, True),
        {"role": "photo", "box": [190, 250, 700, 394]},
        {"role": "body", "box": [150, 686, 780, 194], "size": 30, "color": "333333",
         "font": MED_F, "align": "center"},
    ]

    # ── 내지 B: 체크리스트 ──
    bullets = header() + [
        {"role": "bullets", "box": [83, 210, 914, 800], "size": 40, "color": NV,
         "font": BOLD_F, "auto_color": True,
         "panel": "auto", "panel_tint": 0.22, "panel_round": 6, "pad": 40, "row_h": 139,
         "inset": 53, "icon": 46, "icon_gap": 37, "rule": "auto", "rule_tint": 0.45, "rule_w": 2,
         "max_rows": 5, "min_size": 30, "row_lines": 2,
         "fill": 0.62, "row_h_max": 1.55},
    ]

    spec = {
        "size": 1080, "pt_height": 1080.0, "bg": "FFFFFF",
        "slide_bg": ["FFFFFF", "FFFFFF", "FFFFFF"],
        "theme_recolor": False, "photo_round": 0.0,
        # 글마다 표지 사진에서 대표색을 뽑아 네이비/하늘색 자리를 그 색으로 교체
        "auto_theme": True,
        # 사진 색이 흐리면 채도를 올려 글자가 회색으로 뜨는 것 방지
        "accent_min_sat": 0.45, "accent_max_val": 0.56,
        "bg_palette": ["1F4E79", "0F8C84", "1E965C", "5B5FC7", "96508C", "C85060"],
        # 절차·단계·주의·체크리스트성 내용이면 리스트 카드(2), 아니면 사진 카드(1)
        "pick_by_content": {"default": 1, "list": 2},
        # 이 디자인이 원고에 요구하는 본문 형식(작성기가 프롬프트에 얹는다)
        "card_note": ("절차·단계·순서·필요서류·주의사항·체크리스트 성격의 카드는 본문설명을 한 문장 대신 "
                      "**짧은 구절 3~5개를 ' / '로 이어서** 쓴다"
                      "(예: 전 과정 통합 관리 / 서류 목적 및 제출 국가 분석 / 전문 번역 및 검수 / 공증·아포스티유 연계). "
                      "각 구절 14자 이내, 서술어 없이 명사형으로 끝낸다. 그 외 카드는 지금처럼 한 문장으로 쓴다."),
        "slides": [cover, photo_a, bullets],
    }
    with open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    for k, (n, sz) in a.items():
        print("%-8s %-16s %s" % (k, n, sz))
    print("layout.json slides:", len(spec["slides"]))


if __name__ == "__main__":
    main()
