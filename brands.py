# -*- coding: utf-8 -*-
"""브랜드 설정 관리 — 한 앱으로 여러 브랜드 운영.
brands/<id>/brand.json (설정) + brands/<id>/cards/ (카드 템플릿 에셋, 브랜드별).
폰트는 assets/fonts 공용."""
import os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
BRANDS_DIR = os.path.join(HERE, "brands")
os.makedirs(BRANDS_DIR, exist_ok=True)

# 조형물 제작 기본 단계(다른 업종은 폼에서 바꿔도 됨)
DEFAULT_STAGES = [["대표", "대표"], ["콘셉트", "대표"], ["조각", "공정"], ["몰드", "공정"],
                  ["적층", "공정"], ["샌딩", "공정"], ["퍼티", "공정"], ["공정", "공정"],
                  ["도장", "도장"], ["채색", "도장"], ["설치", "설치"], ["현장", "설치"],
                  ["완성", "완성"], ["디테일", "완성"]]

DEFAULTS = {
    "name": "", "homepage": "", "color": "#FD6F22", "industry": "",
    "tone": "차분하고 신뢰감 있는 실무자 톤. 과장·AI티('~에 대해 알아보겠습니다' 등)·이모지 금지. "
            "한 문장(또는 의미단위)마다 줄바꿈(네이버 모바일 가독성).",
    "intro": '"안녕하세요." + 한 줄 소개 + "{name}입니다." 로 시작.',
    "sections": "개요/특징/과정/사례/장점/마무리 흐름",
    "extra": "",
    "cta": "고민되는 경우라면 {name}로 편하게 문의 주셔도 좋습니다.",
    "card_headlines": ["(메인키워드 그대로 — 표지)", "(핵심 후킹)", "(이유/배경)",
                       "(강점/차별점)", "(품질/디테일)", "(과정/사례)", "(전문성/마무리)"],
    "type_words": [], "stages": DEFAULT_STAGES, "tonggeom": "",
    "identity": "",  # 회사 정체성/서비스/강점 (공통 블로그 구조에 끼워짐)
    "label": "",     # 글 속 표기명(예: FIRST DESIGN). 비면 name 사용
    "prompt": "",    # 완전 커스텀 스크립트(있으면 공통구조 대신 이걸 사용, 출력형식은 자동 부착)
}


def slugify(name):
    s = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", (name or "").strip()).strip("-").lower()
    return s or "brand"


def brand_dir(bid):
    return os.path.join(BRANDS_DIR, bid)


def assets_dir(bid, tpl="1"):
    """카드 템플릿 에셋 폴더. tpl '1'(기본)→cards, 그 외→cards_<tpl>. 한 브랜드가 여러 디자인 보유."""
    tpl = str(tpl or "1")
    sub = "cards" if tpl in ("1", "", "None") else "cards_" + tpl
    return os.path.join(brand_dir(bid), sub)


def card_templates(bid):
    """이 브랜드에 등록된 카드 디자인 목록(layout.json 있는 슬롯). 예: ['1','2','3']."""
    out = []
    for tpl in ("1", "2", "3", "4", "5"):
        if os.path.isfile(os.path.join(assets_dir(bid, tpl), "layout.json")):
            out.append(tpl)
    return out


def has_cards(bid):
    return os.path.isfile(os.path.join(assets_dir(bid, "1"), "layout.json"))


def load_brand(bid):
    p = os.path.join(brand_dir(bid), "brand.json")
    try:
        c = json.load(open(p, encoding="utf-8"))
    except Exception:
        c = {}
    out = dict(DEFAULTS)
    out.update(c)
    out["id"] = bid
    out["has_cards"] = has_cards(bid)
    out["card_templates"] = card_templates(bid)
    if not out.get("stages"):
        out["stages"] = DEFAULT_STAGES
    return out


def save_brand(cfg):
    bid = cfg.get("id") or slugify(cfg.get("name", ""))
    cfg["id"] = bid
    os.makedirs(brand_dir(bid), exist_ok=True)
    keep = {k: cfg.get(k, DEFAULTS.get(k)) for k in DEFAULTS}
    keep["id"] = bid
    json.dump(keep, open(os.path.join(brand_dir(bid), "brand.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return bid


def list_brands():
    out = []
    for d in sorted(os.listdir(BRANDS_DIR)) if os.path.isdir(BRANDS_DIR) else []:
        if os.path.isfile(os.path.join(BRANDS_DIR, d, "brand.json")):
            b = load_brand(d)
            out.append({"id": d, "name": b["name"] or d, "color": b["color"],
                        "has_cards": b["has_cards"], "card_templates": b.get("card_templates", [])})
    return out


def _output_format(b):
    """앱이 파싱하려면 반드시 필요한 출력 형식(제목/사진슬롯7/카드헤드라인) — 어떤 문체든 끝에 부착."""
    heads = (b.get("card_headlines") or DEFAULTS["card_headlines"])[:7]
    while len(heads) < 7:
        heads.append("(요약)")
    head_lines = "\n".join(f"{i+1}. {h} | (이 카드 본문 한 줄 설명)" for i, h in enumerate(heads))
    return f"""[출력 형식 — 정확히 이 형식만, 다른 설명/머리말 금지]
제목: (메인키워드 포함한 제목)
(사진1: 파일명)
본문 도입...
**1. 소제목**
(사진2: 파일명)
본문...
(... 정확히 6개 소제목, 각 소제목 아래 사진 1장씩 ...)
★(사진)은 **정확히 7개**: 도입 1장(사진1) + 소제목 6개 각 1장(사진2~사진7). 카드뉴스 7장과 1:1로 맞춘다. 더도 덜도 말 것.
규칙: 사진은 아래 '사용 사진' 목록의 파일명만 (사진N: 정확한파일명) 형태로 배치. 목록에 없는 파일명 만들지 말 것.
★중요: **각 (사진N) 슬롯에는 서로 다른 사진**을, 그 단락 내용에 **가장 어울리는 사진**으로 배치하라. 같은 사진을 두 번 쓰지 말 것. 파일명에 단계/타입 힌트가 있으면 그 단락에 맞춰라.

[카드뉴스]
원고를 다 쓴 뒤, 맨 끝에 아래 형식으로 카드 7장을 출력하라. 각 줄은 "헤드라인 | 본문설명" 형식이다.
- 헤드라인: 짧고 강하게(12자 내외), 본문 흐름 요약
- 본문설명: 그 카드 내용을 1문장으로 자연스럽게 풀어 설명(35자 내외)
카드뉴스:
{head_lines}
표지부제: (표지 큰제목 아래 들어갈 한 줄 부제 — 이 글 주제를 요약하는 짧은 후킹 문장, 18자 내외)"""


def _shared_structure(b):
    """전 브랜드 공통 블로그 '기술 구조'(소제목6·제목키워드·SEO·도입/마무리 형식)는 고정.
    톤·회사소개·서비스·장점·CTA만 브랜드별 필드로 끼워 넣는다."""
    name = b.get("name", "")
    label = (b.get("label") or name).strip()
    industry = (b.get("industry") or "").strip()
    identity = (b.get("identity") or "").strip() or f"{name}는 {industry or '고객을 위해 일하는'} 회사다."
    tone = (b.get("tone") or "").strip() or DEFAULTS["tone"]
    cta = (b.get("cta") or "").strip().replace("{name}", label) or \
        f'부담을 덜어주는 한 줄로 자연스럽게 닫되, 메인키워드를 제대로 하고 싶다면 {label}을(를) 떠올리게 한다.'
    return f"""너는 '{name}'{('(' + industry + ')') if industry else ''}의 네이버 블로그 글을 쓰는 카피라이터다.

[회사 소개 — 이 회사의 서비스·강점(브랜드별)]
{identity}

[문체/톤 (브랜드별)]
{tone}

[블로그 구조 — 모든 글 공통(기술 규칙)]
- 도입: "안녕하세요"로 인사하고 {label}을(를) 한 줄로 소개한 뒤, "오늘은 ... (메인키워드) 이야기를 해볼까 해요" 식으로 주제를 안내한다.
- 소제목 **정확히 6개**. 각 소제목 아래 본문 단락. 소제목 스타일은 위 톤에 맞춘다(질문형/선언형/넘버링 등).
- 각 단락은 [고객의 흔한 고민·궁금증 → 그래서 이게 왜 중요한지 → {label}은 이렇게 합니다(강점·디테일)] 흐름으로 전개한다.
- 제목에 메인키워드를 포함한다. 공백 제외 1,500자 이상. 메인키워드를 제목·소제목·본문에 자연스럽게 5~8회 녹인다(억지 반복 금지).
- 한 문장(또는 의미단위)마다 줄바꿈(네이버 모바일 가독성). 과장·AI티('~에 대해 알아보겠습니다' 등) 금지.

[마무리]
{cta}"""


def build_style(b):
    """브랜드 설정 → 글 생성 시스템 프롬프트.
    prompt(완전 커스텀)가 있으면 그걸 쓰고, 없으면 전 브랜드 공통 구조 + 회사 소개. 출력 형식은 항상 부착."""
    custom = (b.get("prompt") or "").strip()
    head = custom.replace("{name}", b.get("name", "")) if custom else _shared_structure(b)
    return head + "\n\n" + _output_format(b)
