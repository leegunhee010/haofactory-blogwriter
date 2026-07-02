# -*- coding: utf-8 -*-
"""브랜드 설정 관리 — 한 앱으로 여러 브랜드 운영.
brands/<id>/brand.json (설정) + brands/<id>/cards/ (카드 템플릿 에셋, 브랜드별).
폰트는 assets/fonts 공용."""
import os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
BRANDS_DIR = os.path.join(HERE, "brands")
os.makedirs(BRANDS_DIR, exist_ok=True)

# 사용자가 앱에서 직접 수정한 브랜드 설정은 여기(작성기_설정.json)에 저장 → 런처 PRESERVE 목록이라
# 업데이트(update.zip)로 덮어써지지 않음. 브랜드 담당자가 고친 설정이 업데이트 후에도 유지된다.
_CFG_FILE = os.path.join(HERE, "작성기_설정.json")


def _load_cfg_raw():
    try:
        return json.load(open(_CFG_FILE, encoding="utf-8"))
    except Exception:
        return {}


def load_overrides():
    """앱에서 사용자가 저장한 브랜드별 오버라이드({brand_id: {필드...}})."""
    d = _load_cfg_raw()
    return d.get("brand_overrides") or {}

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
    "brand_placement": "each",  # each=소제목마다 브랜드 언급 / end=본문은 정보만·브랜드는 마무리에서만
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
    ov = load_overrides().get(bid)          # 사용자가 앱에서 고친 설정(업데이트에도 보존) → 최우선
    if ov:
        out.update({k: v for k, v in ov.items() if k in DEFAULTS})
    out["id"] = bid
    out["has_cards"] = has_cards(bid)
    out["card_templates"] = card_templates(bid)
    if not out.get("stages"):
        out["stages"] = DEFAULT_STAGES
    return out


def save_override(cfg):
    """앱 UI에서 사용자가 저장한 브랜드 설정 → 작성기_설정.json(보존됨)에 브랜드별로 기록.
    base brand.json(배포본)은 건드리지 않음 → 업데이트가 base를 갱신해도 사용자 수정분은 유지."""
    bid = cfg.get("id") or slugify(cfg.get("name", ""))
    cfg["id"] = bid
    keep = {k: cfg.get(k, DEFAULTS.get(k)) for k in DEFAULTS}
    keep["id"] = bid
    d = _load_cfg_raw()
    ov = d.get("brand_overrides") or {}
    ov[bid] = keep
    d["brand_overrides"] = ov
    try:
        json.dump(d, open(_CFG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return bid


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


_AEO_BLOCK = """[AEO·GEO 최적화 — AI(네이버 AI·ChatGPT·Gemini 등)가 읽고 '인용'하기 쉬운 글쓰기]
- 두괄식: 도입과 각 소제목의 첫 1~2문장에서 그 질문에 대한 '결론·핵심 답'을 먼저 분명히 말한 뒤 근거를 푼다.
- 소제목은 독자가 실제로 검색·질문하는 형태(질문형 또는 핵심 명사형)로 짓는다. 매 소제목이 하나의 구체적 궁금증에 답하게 한다.
- 구체적 사실 우선: '다양한/여러/많은' 같은 막연한 표현 금지 → 개수·명칭·수치로 명시한다(예: "다양한 방법" X → "3가지: A·B·C" O).
- 수치·통계·법령을 지어내지 말 것. 근거가 분명한 사실만 쓰고, 확실치 않으면 그 수치·데이터 자체를 아예 언급하지 않는다.
- 비교·가격·절차·조건처럼 정리가 필요한 정보는 이미지가 아니라 '텍스트 표/목록'으로 또박또박 제시한다(줄바꿈으로 항목을 나눠 네이버에 붙여도 읽기 쉽게). 글자로 정리해야 AI가 읽고 인용할 수 있다.
- 지역·대상·서비스를 분명히 밝혀(누구를 위한 무슨 서비스인지) AI가 "이건 누가 하나?"라는 질문에 이 브랜드를 떠올리게 한다.
- 절대 뻔한 일반론으로 흐르지 말고, 실제로 바로 써먹을 수 있는 사실·기준·팁으로 채운다. 각도는 창의적으로 잡되 사실은 정확해야 한다."""


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
    placement = (b.get("brand_placement") or "each").strip()
    if placement == "end":
        flow = (f"- 각 소제목 본문은 **오직 독자에게 유용한 정보**만 담는다. 고객이 실제로 궁금해하는 것"
                f"(비용·필요서류·절차·선택 기준·주의점·자주 하는 실수 등)에 곧바로, 구체적으로 답한다.\n"
                f"- 본문(도입~여섯 번째 소제목)에서는 회사({label}) 소개·홍보·강점 언급을 넣지 않는다. 정보 자체로 신뢰를 준다.\n"
                f"- {label}에 대한 소개·강점·문의 유도는 **오직 마지막 마무리 문단에서만** 자연스럽게 한다.")
    else:
        flow = (f"- 각 단락은 [고객의 흔한 고민·궁금증 → 그래서 이게 왜 중요한지 → {label}은 이렇게 합니다"
                f"(강점·디테일)] 흐름으로 전개한다.")
    return f"""너는 '{name}'{('(' + industry + ')') if industry else ''}의 네이버 블로그 글을 쓰는 카피라이터다.

[회사 소개 — 이 회사의 서비스·강점(브랜드별)]
{identity}

[문체/톤 (브랜드별)]
{tone}

[블로그 구조 — 모든 글 공통(기술 규칙)]
- 도입: "안녕하세요"로 인사하고 {label}을(를) 한 줄로 소개한 뒤, "오늘은 ... (메인키워드) 이야기를 해볼까 해요" 식으로 주제를 안내한다.
- 소제목 **정확히 6개**. 각 소제목 아래 본문 단락. 소제목 스타일은 위 톤에 맞춘다(질문형/선언형/넘버링 등).
{flow}
- 제목에 메인키워드를 포함한다. 공백 제외 1,500자 이상. 메인키워드를 제목·소제목·본문에 자연스럽게 5~8회 녹인다(억지 반복 금지).
- 한 문장(또는 의미단위)마다 줄바꿈(네이버 모바일 가독성). 과장·AI티('~에 대해 알아보겠습니다' 등) 금지.

{_AEO_BLOCK}

[마무리]
{cta}"""


def guide_text(bid):
    """브랜드 폴더의 guide.md(사실 기준서) 텍스트. 없으면 빈 문자열."""
    try:
        p = os.path.join(brand_dir(bid), "guide.md")
        if os.path.isfile(p):
            return open(p, encoding="utf-8").read().strip()
    except Exception:
        pass
    return ""


def _guide_block(b):
    """브랜드 사실 기준서를 '반드시 준수' 블록으로 부착(가격·절차·규칙 오정보 방지)."""
    g = guide_text(b.get("id", ""))
    if not g:
        return ""
    return ("\n\n[★브랜드 사실 기준서 — 반드시 준수(오정보 금지)]\n"
            "아래는 이 브랜드의 실제 서비스·가격·절차·규칙 기준이다. 블로그에 사실관계를 쓸 때 "
            "반드시 아래 기준만 따른다. 특히:\n"
            "- 협약국=아포스티유 / 비협약국=영사인증 구분을 절대 혼동하지 말 것.\n"
            "- 번역 지원 8개 언어 외 국가는 '영어로 번역공증 후 진행' 안내를 넣을 것.\n"
            "- 가격·소요기간은 아래 표(블로그 표기가)에 있는 값만 쓰고, 표에 없으면 지어내지 말고 "
            "'서류 확인 후 안내'로 열어 둘 것. '무조건 가능' 같은 단정 표현 금지.\n"
            "- 공증 타입(공문서=번역공증 / 사문서·위임=사실공증 / 무번역 원본=원본대조공증)을 정확히 구분할 것.\n"
            "----- 기준서 시작 -----\n" + g + "\n----- 기준서 끝 -----")


_NATURAL_TONE = """[자연스러운 말투 — 'AI가 쓴 티'를 지운다 ★모든 브랜드 공통]
- 종결어미(합니다/됩니다 · 해요/이에요 등)는 위에서 지정한 브랜드 톤을 그대로 지킨다. 바꾸는 건 어미가 아니라 '쓰는 방식'이다.
- AI 티 나는 상투구 금지: "~에 대해 알아보겠습니다", "지금까지 ~를 알아봤습니다", "먼저/다음으로/마지막으로"의 기계적 나열, 질문을 그대로 되풀이한 뒤 답하기.
- 실제 실무자가 말하듯 쓴다: 현장에서 겪는 구체적 상황·사례·자주 받는 질문을 곁들이고, 뻔한 일반론·교과서식 정리는 피한다.
- 문장 길이와 리듬에 변화를 준다(짧은 문장·긴 문장 섞기). '또한/그리고/이러한' 같은 접속 표현을 남발하지 않는다.
- 결론을 빙빙 돌리지 말고 핵심을 먼저 담백하게. 매 문단이 똑같은 리듬으로 반복되지 않게 한다.
- 사람이 읽었을 때 '광고·AI 글'이 아니라 '아는 사람이 편하게 알려주는 글' 느낌이 나야 한다."""


_SELFCHECK = """[발행 전 자가 점검 — 아래를 스스로 확인한 뒤 최종본만 출력한다. 점검 결과·체크리스트는 절대 출력하지 말 것]
- 지어낸 수치·사실이 없는가. (사실 기준서가 있으면 그 값만 썼는가.)
- 막연한 표현 대신 구체적 사실·수치·명칭으로 썼는가. 뻔한 일반론이 아니라 실제로 유용한가.
- 소제목 정확히 6개, (사진) 정확히 7개, 제목·본문에 메인키워드가 자연스럽게 들어갔는가.
- 문체가 지정한 톤(어미)은 지키되, 'AI가 쓴 티'가 나지 않고 사람이 쓴 것처럼 자연스러운가.
- 비교·가격·절차 같은 정보는 텍스트 표/목록으로 정리했는가."""


def build_style(b):
    """브랜드 설정 → 글 생성 시스템 프롬프트.
    prompt(완전 커스텀)가 있으면 그걸 쓰고, 없으면 전 브랜드 공통 구조 + 회사 소개. 출력 형식은 항상 부착.
    브랜드 폴더에 guide.md(사실 기준서)가 있으면 '반드시 준수' 블록으로 함께 부착.
    발행 전 자가 점검(AEO·사실 정확성)은 모든 글에 부착."""
    custom = (b.get("prompt") or "").strip()
    head = custom.replace("{name}", b.get("name", "")) if custom else _shared_structure(b)
    return (head + _guide_block(b) + "\n\n" + _output_format(b) +
            "\n\n" + _NATURAL_TONE + "\n\n" + _SELFCHECK)
