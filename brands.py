# -*- coding: utf-8 -*-
"""브랜드 설정 관리 — 한 앱으로 여러 브랜드 운영.
brands/<id>/brand.json (설정) + brands/<id>/cards/ (카드 템플릿 에셋, 브랜드별).
폰트는 assets/fonts 공용."""
import os, json, re, random, time, urllib.request

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
    "brand_placement": "end",   # end=본문은 정보만·브랜드는 마무리에서만(기본) / each=소제목마다 브랜드 언급
    "crm_on": False,             # CRM 성과추적 링크 부착 여부(브랜드별 — CRM 서버가 그 브랜드를 받을 준비가 됐을 때만 켠다)
    "crm_prefix": "",            # 추적키 접두어(예: firstdesign=fd). CRM 게시현황과 약속된 값
    "crm_label": "문의",         # 추적링크 앞 문구(예: 홍보물 디자인·인쇄 문의)
    "crm_mode": "go",            # go=CRM 서버 경유(/go/) · utm=홈페이지로 바로(UTM, 홈페이지 분석 도구가 유입 기록)
    "web_update": False,         # True면 작성 전 웹검색으로 최신 공개 정보 확인(레드트랜스·윈차이나). 회사 가격·절차는 기준서 유지
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
    keep = {}
    try:   # 기존 brand.json 의 DEFAULTS 밖 설정(length·final_faq_promo·faq_list 등)은 그대로 보존
        old = json.load(open(os.path.join(brand_dir(bid), "brand.json"), encoding="utf-8"))
        keep.update({k: v for k, v in old.items() if k not in DEFAULTS})
    except Exception:
        pass
    keep.update({k: cfg.get(k, DEFAULTS.get(k)) for k in DEFAULTS})
    keep["id"] = bid
    json.dump(keep, open(os.path.join(brand_dir(bid), "brand.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return bid


def load_crm(bid):
    """brands/<id>/crm.json — 성과추적 링크 설정(link:{key} 템플릿, cta:앞말, prefix:키 접두어).
    brand.json과 분리해 두어 앱 UI의 브랜드 저장(save_brand/save_override)에 지워지지 않음."""
    p = os.path.join(brand_dir(bid), "crm.json")
    try:
        return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
    except Exception:
        return {}


def list_brands():
    out = []
    for d in sorted(os.listdir(BRANDS_DIR)) if os.path.isdir(BRANDS_DIR) else []:
        if os.path.isfile(os.path.join(BRANDS_DIR, d, "brand.json")):
            b = load_brand(d)
            out.append({"id": d, "name": b["name"] or d, "color": b["color"],
                        "has_cards": b["has_cards"], "card_templates": b.get("card_templates", []),
                        # 브랜드 기본값(brand.json 선택 키): 기본 카드 디자인 슬롯 · 기본 사진 폴더(새 글 탭에 자동 입력)
                        "default_template": str(b.get("default_template") or "1"),
                        "photo_folder": b.get("photo_folder") or "",
                        "crm": load_crm(d),
                        # 채널 표준 프롬프트(네이버 블로그/카페) — brands/<id>/channels.json 이 있는 브랜드만
                        "channels": channel_list(d),
                        "drive_link": bool(b.get("drive_link"))})
    return out


# ── 채널(네이버 블로그 / 카페) 표준 프롬프트 ─────────────────────────────────
# brands/<id>/channels.json — sync_channel_prompts.py 가 운영자 원본 프롬프트(E:\13. red&win blog 0812\prompt)에서 생성.
#   {"blog": {label, prompt(파일명), version, length[min,max], links(bool), extra_files[], track_hint, blocks{NAME:설명}}, "cafe": {...}, "_links": {...}}
# 채널을 고르면 그 채널 프롬프트 전문이 brand["prompt"](완전 커스텀)로 얹히고, 출력 형식은 channel_output_format()이 앱 형식으로 강제한다.
TRACK_TOKEN = "{{추적링크}}"


def load_channels(bid):
    p = os.path.join(brand_dir(bid), "channels.json")
    try:
        d = json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
    except Exception:
        d = {}
    return {k: v for k, v in d.items() if not k.startswith("_") and isinstance(v, dict)}


def links_cfg(bid):
    p = os.path.join(brand_dir(bid), "channels.json")
    try:
        d = json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
        return d.get("_links") or {}
    except Exception:
        return {}


def channel_list(bid):
    return [{"id": k, "label": v.get("label") or k, "version": v.get("version", ""),
             "length": v.get("length") or []} for k, v in load_channels(bid).items()]


def channel_prompt_text(bid, ch):
    cfg = load_channels(bid).get(ch) or {}
    fn = cfg.get("prompt") or f"prompt_{ch}.md"
    try:
        p = os.path.join(brand_dir(bid), fn)
        if os.path.isfile(p):
            return open(p, encoding="utf-8-sig").read().strip()
    except Exception:
        pass
    return ""


def apply_channel(b, ch):
    """브랜드 dict(load_brand 결과)에 채널 표준 프롬프트를 얹은 복사본을 돌려준다.
    prompt=채널 프롬프트 전문(완전 커스텀 경로), length=채널 분량, channel/channel_label/channel_cfg 추가.
    채널이 없거나 파일이 없으면 원본 그대로(기존 동작)."""
    ch = (ch or "").strip()
    if not b or not ch:
        return b
    cfg = load_channels(b.get("id", "")).get(ch)
    if not cfg:
        return b
    txt = channel_prompt_text(b["id"], ch)
    if not txt:
        return b
    out = dict(b)
    out["prompt"] = txt
    out["channel"] = ch
    out["channel_label"] = cfg.get("label") or ch
    out["channel_cfg"] = cfg
    if cfg.get("length"):
        out["length"] = cfg["length"]
    return out


def _extra_files_block(b):
    """채널 설정 extra_files(예: 원고_로테이션_뱅크.md) — 운영자가 관리하는 파일을 생성 시점에 그대로 읽어 부착."""
    out = ""
    for f in (b.get("channel_cfg") or {}).get("extra_files") or []:
        try:
            if os.path.isfile(f):
                name = os.path.splitext(os.path.basename(f))[0]
                txt = open(f, encoding="utf-8-sig").read().strip()
                out += (f"\n\n[{name} — 운영자가 관리하는 파일 그대로. '사용 이력'과 아래 [직전 글 정보]를 보고 "
                        f"직전 3편과 겹치지 않는 형식을 고른다(고른 형식은 ===META===에 기록)]\n----- 파일 시작 -----\n{txt}\n----- 파일 끝 -----")
        except Exception:
            pass
    return out


def channel_output_format(b):
    """채널 글의 출력 형식 — 앱이 파싱하는 제목:/(사진N)/**소제목**/카드뉴스: 형식 + 채널 프롬프트가 요구하는 ===부가 블록===."""
    cfg = b.get("channel_cfg") or {}
    blocks = cfg.get("blocks") or {}
    crm = load_crm(b.get("id", ""))
    note = (b.get("card_note") or "").strip()
    card_extra = ("\n- ★" + note) if note else ""
    order = [n for n in ("CATEGORY", "TAGS", "COMMENTS", "ANALYSIS") if n in blocks]
    extra_fmt = "".join(f"==={n}===\n({blocks[n]})\n" for n in order)
    extra_rules = "".join(f"  · ==={n}=== : {blocks[n].splitlines()[0]}\n" for n in order)
    track = ""
    if crm.get("link"):
        hint = cfg.get("track_hint") or "문의 채널을 말하는 자리에 「홈페이지 {{추적링크}}」 형태로"
        track = (f"- ★성과추적 링크(CRM/UTM): {hint} — URL 대신 토큰 `{TRACK_TOKEN}` 을 **정확히 1회** 넣는다. "
                 "앱이 이 토큰을 글별 추적 링크(UTM)로 치환한다. 위 프롬프트의 'URL 창작 금지' 규칙은 이 토큰에는 적용하지 않는다. "
                 "그 외 다른 URL(카카오톡 링크·전화번호 등)은 위 프롬프트가 허용한 것만.\n")
    if (cfg.get("media") or "photos") == "thumb_only":
        # 카페: 본문 이미지·카드뉴스·표 이미지 없음(썸네일 1장은 앱이 따로 만든다) — 순수 텍스트 + 부가 블록
        return f"""[출력 형식 — 앱 전용 ★위 프롬프트의 '출력 형식'(===TITLE===/===BODY===)은 쓰지 않고 이 형식으로만 출력한다. 설명·머리말·코드블록 금지]
제목: (제목 — 위 프롬프트의 제목 규칙대로. 제목이 지정돼 있으면 그대로)
(첫 줄 인사부터 본문 시작 — 위 프롬프트의 본문 구조·골격·문체·줄바꿈 규칙을 그대로 따른다)
**1. 소제목**
본문...
**2. 소제목**
본문...
(... 위 프롬프트가 요구하는 소제목 수만큼. FAQ·클로징·오피스 블록·태그 줄까지 본문 전부 여기에 쓴다 ...)
{extra_fmt}===META===
골격: (이 글에 쓴 골격/글 유형 — A/B/C/D 또는 S/I)
인사: (첫 줄 인사에 쓴 전문성 수식어 문구 그대로)
도입: (도입 방식 한 줄)
요약: (핵심 요약 블록의 형식·제목·위치 한 줄)
마무리: (마무리·CTA 방식 한 줄)
썸네일: (카페 목록 썸네일용 초단문 제목 — "1행 / 2행" 형식, 각 행 3~6자. 1행=메인 키워드 축약(예: 번역공증), 2행=이 글의 각도(예: 비용 기준). 문장 금지·조사 최소)
썸네일부제: (썸네일 제목 아래 한 줄 10~18자, 이 글의 핵심 대비·기준. 예: 일한·중한 직접번역 vs 전문업체)

[형식 규칙 — 앱이 파싱하므로 반드시]
- 소제목: 위 프롬프트가 요구하는 대로 짓되(번호 1. 2. 3. 포함 여부·명사형 등 그대로), **소제목 줄은 반드시 `**` 로 감싼 한 줄**로 출력한다(앱 인식용 — 복사할 때 자동으로 제거돼 순수 텍스트가 된다). 마크다운 # 은 쓰지 않는다. ✔ 줄·Q./A. 줄·오피스 블록 줄은 소제목이 아니므로 `**` 를 붙이지 않는다.
- ★이 채널은 본문 이미지가 없다: (사진N) 줄·[이미지N] 마커·'카드뉴스:'·'표차트:' 섹션을 **모두 쓰지 않는다**. 표가 필요하면 "항목 : 값" 텍스트 나열로. 썸네일 1장은 앱이 ===META=== 썸네일 문구로 따로 만든다.
{track}- ===부가 블록===: 본문이 끝난 뒤 위 순서대로 붙인다. 각 블록은 위 프롬프트의 해당 규칙대로, 한국어로.
{extra_rules}- ===META===: 다음 글 로테이션용 기록 + 썸네일 문구. 일곱 줄 그대로(해당 없으면 '-').
- 본문의 줄바꿈은 위 프롬프트의 줄바꿈 규칙(짧은 구절마다 줄바꿈, 의미 덩어리 사이 빈 줄)을 그대로 유지한다."""
    return f"""[출력 형식 — 앱 전용 ★위 프롬프트의 '출력 형식'(===TITLE===/===BODY===)은 쓰지 않고 이 형식으로만 출력한다. 설명·머리말·코드블록 금지]
제목: (제목 — 위 프롬프트의 제목 규칙대로. 제목이 지정돼 있으면 그대로)
(사진1: 파일명)
(첫 줄 인사부터 본문 시작 — 위 프롬프트의 본문 구조·골격·문체·줄바꿈 규칙을 그대로 따른다)
**1. 소제목**
(사진2: 파일명)
본문...
**2. 소제목**
(사진3: 파일명)
본문...
(... 위 프롬프트가 요구하는 소제목 수만큼. FAQ·관련 글·서비스/접수 안내·연락처·태그 줄까지 본문 전부 여기에 쓴다 ...)
카드뉴스:
1. 메인키워드 그대로 | 표지 한 줄 설명
2. 첫째 소제목 핵심 12자 내외 | 그 소제목 내용 한 문장 35자 내외
3. 둘째 소제목 핵심 12자 내외 | 그 소제목 내용 한 문장 35자 내외
(... 본문의 `**소제목**` 전부(FAQ·관련 글·서비스 문단 포함) 수만큼, 같은 순서 1:1. 헤드라인·설명을 괄호로 감싸지 말 것 ...)
표지부제: 표지 큰제목 아래 한 줄 부제 — 이 글 주제를 요약하는 짧은 후킹 문장, 18자 내외
표차트: 없음
{extra_fmt}===META===
골격: (이 글에 쓴 골격/글 유형 — A/B/C/D 또는 S/I)
인사: (첫 줄 인사에 쓴 전문성 수식어 문구 그대로)
도입: (도입 방식 한 줄)
요약: (핵심 요약 블록의 형식·제목·위치 한 줄)
마무리: (마무리·CTA 방식 한 줄)
썸네일: (카페/블로그 목록 썸네일용 초단문 제목 — "1행 / 2행" 형식, 각 행 3~6자. 1행=메인 키워드 축약(예: 번역공증), 2행=이 글의 각도(예: 비용 기준). 문장 금지·조사 최소)
썸네일부제: (썸네일 제목 아래 한 줄 10~18자, 이 글의 핵심 대비·기준. 예: 일한·중한 직접번역 vs 전문업체)

[형식 규칙 — 앱이 파싱하므로 반드시]
- 소제목: 위 프롬프트가 요구하는 대로 짓되(번호 1. 2. 3. 포함 여부·명사형 등 그대로), **소제목 줄은 반드시 `**` 로 감싼 한 줄**로 출력한다(앱 인식용 — 복사할 때 자동으로 제거돼 순수 텍스트가 된다). 위 프롬프트의 [인용구] 마커·마크다운 # 은 쓰지 않는다. 📌 요약 줄·✔ 줄·Q./A. 줄·『』볼드·해시태그 줄·오피스 블록 줄은 소제목이 아니므로 `**` 를 붙이지 않는다.
- 사진 슬롯: 위 프롬프트의 [이미지N] 마커는 쓰지 않는다. 대신 (사진N: 파일명) 한 줄을 **도입 직후 1개 + 본문 `**소제목**` 바로 아래 1개씩** 넣는다 — ★FAQ·관련 글·서비스/접수 안내 소제목까지 **모든 `**소제목**` 아래에 예외 없이** 1개씩(카드뉴스와 1:1). 파일명은 아래 '사용 사진' 목록에 있는 것만, 슬롯마다 서로 다른 사진, 없는 파일명 창작 금지. 사진이 슬롯보다 적으면 있는 만큼만 넣고 나머지 슬롯은 생략한다. 사진 목록이 '(없음)'이면 (사진N: ) 처럼 파일명을 비워 둔다.
- 표: 위 프롬프트가 [표]를 요구하면 그 자리에 (표1) 마커 한 줄 + 바로 아래 표 요지를 텍스트 2~3줄로 다시 적고(AEO — 이미지 속 글자는 AI가 못 읽는다), 맨 끝 '표차트:' 섹션에 `표1 | 제목 | 헤더1,헤더2,헤더3 ; 항목,값,값 ; 항목,값,값` 형식으로 데이터를 준다. 표를 안 넣으면 '표차트: 없음'. 차트는 넣지 않는다.
- 카드뉴스: 표지 1장 + 본문 `**소제목**` 전부 수만큼(FAQ·관련 글·서비스 문단 소제목 포함, 같은 순서 1:1 — 카드N(2~)의 주제 = (N-1)번째 소제목. 소제목이 9개면 카드 10장). FAQ 카드는 대표 질문·답 한 줄, 관련 글 카드는 '함께 보면 좋은 글' 성격의 한 줄, 서비스 문단 카드는 문의 안내 한 줄로. 헤드라인은 그 소제목 핵심을 12자 내외로, 본문설명은 1문장 35자 내외. ★헤드라인마다 강조하고 싶은 핵심어 1곳(1~2어절)만 `*별표*`로 감싼다(예: 학력증명서 *원본 점검* / 대사관 예약은 *불필요*) — 문장 전체를 감싸거나 2곳 이상 감싸지 말 것(앱이 그 부분만 강조색으로 칠한다). 표지 헤드라인은 앱이 메인키워드로 고정한다.{card_extra}
{track}- ===부가 블록===: 본문(카드뉴스·표차트)이 끝난 뒤 위 순서대로 붙인다. 각 블록은 위 프롬프트의 해당 규칙대로, 한국어로.
{extra_rules}- ===META===: 다음 글 로테이션용 기록 + 썸네일 문구. 일곱 줄 그대로(해당 없으면 '-').
- 본문의 줄바꿈은 위 프롬프트의 줄바꿈 규칙(한 문장/짧은 구절마다 줄바꿈, 의미 덩어리 사이 빈 줄)을 그대로 유지한다."""


def channel_selfcheck(b):
    lo, hi = length_range(b)
    cfg = b.get("channel_cfg") or {}
    names = "·".join(f"==={n}===" for n in ("CATEGORY", "TAGS", "COMMENTS", "ANALYSIS") if n in (cfg.get("blocks") or {}))
    crm = load_crm(b.get("id", ""))
    tk = f"\n- 성과추적 토큰 {TRACK_TOKEN} 이 본문에 정확히 1회 있는가." if crm.get("link") else ""
    return ("[발행 전 자가 점검 — 스스로 확인한 뒤 최종본만 출력한다. 점검 결과·체크리스트는 절대 출력하지 말 것]\n"
            "- 위 프롬프트의 '발행 전 자가 체크' 항목을 전부 통과했는가(팩트 시트 값만·인증 경로·인사 형태·서브 키워드 배치·상투 문형 금지 등).\n"
            f"- ★분량이 공백 제외 {lo:,}~{hi:,}자 범위인가(목표 약 {(lo + hi) // 2:,}자. {hi:,}자를 넘기면 안 된다 — 출력 전에 실제로 세어 보고, 넘으면 사례·설명 문장을 덜어내 {hi:,}자 아래로 맞춘 뒤 출력한다).\n"
            "- [직전 글 정보]의 직전 골격·인사 수식어·도입·마무리 방식과 겹치지 않는가.\n"
            + ("- '제목:' 줄, `**소제목**` 형식이 있고 (사진N)·카드뉴스·표차트 섹션은 없는가(이 채널은 본문 이미지 없음).\n"
               if (cfg.get("media") or "photos") == "thumb_only" else
               "- '제목:' 줄, `**소제목**` 형식, (사진N: 파일명) 슬롯(도입 1 + 모든 소제목별 1 — FAQ·관련 글·서비스 문단 포함), '카드뉴스:'(표지+모든 소제목 1:1, 소제목 수와 카드 수-1 이 같은가), '표지부제:', '표차트:' 가 모두 있는가.\n")
            +
            f"- 부가 블록 {names}·===META=== 를 빠짐없이, 지정 순서로 붙였는가." + tk)


def build_style_channel(b):
    """채널 표준 프롬프트 브랜드용 시스템 프롬프트: 채널 프롬프트 전문(팩트 시트 내장) + 운영자 파일(로테이션 뱅크 등)
    + [내부링크 후보](블로그 채널만) + 앱 전용 출력 형식 + 자연스러운 말투 + 자가 점검. guide.md는 채널 프롬프트에 팩트 시트가 있으므로 붙이지 않는다."""
    head = (b.get("prompt") or "").replace("{name}", b.get("name", ""))
    cfg = b.get("channel_cfg") or {}
    lk = links_block(b) if cfg.get("links") else ""
    return (head + _extra_files_block(b) + lk + "\n\n" + channel_output_format(b) +
            "\n\n" + _NATURAL_TONE + "\n\n" + channel_selfcheck(b))


def refresh_links(bid, force=False):
    """channels.json _links(rss·pages) → brands/<id>/links.txt('제목 | URL') 갱신. ttl_hours 안이면 건너뜀. 실패해도 조용히."""
    cfg = links_cfg(bid)
    if not cfg:
        return False
    p = os.path.join(brand_dir(bid), "links.txt")
    ttl = float(cfg.get("ttl_hours") or 24) * 3600
    try:
        import time
        if not force and os.path.isfile(p) and (time.time() - os.path.getmtime(p)) < ttl:
            return False
    except Exception:
        pass
    rows = []
    try:
        import urllib.request, html as _html
        def fetch(u):
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
        half = max(4, int(cfg.get("max") or 15) // 2)
        for pg in cfg.get("pages") or []:          # 홈페이지 칼럼(1순위) — 절반까지
            try:
                x = fetch(pg["url"])
                for href, title in re.findall(pg["pattern"], x, re.S)[:half]:
                    title = re.sub(r"<[^>]+>", "", _html.unescape(title)).strip()
                    if title:
                        rows.append(f"{title} | {pg.get('base', '')}{href}")
            except Exception:
                pass
        for u in cfg.get("rss") or []:             # 네이버 블로그 RSS(2순위)
            try:
                x = fetch(u)
                for it in re.findall(r"<item>(.*?)</item>", x, re.S):
                    t = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", it, re.S)
                    g = re.search(r"<guid>(.*?)</guid>", it, re.S)
                    if t and g:
                        rows.append(f"{_html.unescape(t.group(1).strip())} | {g.group(1).strip()}")
            except Exception:
                pass
    except Exception:
        pass
    if not rows:
        return False
    seen, uniq = set(), []
    for r in rows:
        if r not in seen:
            seen.add(r); uniq.append(r)
    uniq = uniq[: int(cfg.get("max") or 15)]
    try:
        open(p, "w", encoding="utf-8").write("# 자동 생성(refresh_links) — RSS·칼럼 목록 최신 글. 제목 | URL\n" + "\n".join(uniq) + "\n")
        return True
    except Exception:
        return False


def _output_format(b):
    """앱이 파싱하려면 반드시 필요한 출력 형식(제목/사진슬롯7/카드헤드라인) — 어떤 문체든 끝에 부착.
    brand.json card_note가 있으면 카드뉴스 규칙에 브랜드별 지시를 한 줄 추가."""
    note = (b.get("card_note") or "").strip()
    extra = ("\n- ★" + note) if note else ""
    if photo_layout(b) == "pairs":
        photo_fmt = """[출력 형식 — 정확히 이 형식만, 다른 설명/머리말 금지]
제목: (메인키워드 포함한 제목)
(사진1: 파일명)
(사진2: 파일명)
도입(요약 블록)...
**1. 소제목**
(사진3: 파일명)
(사진4: 파일명)
본문...
(... 정확히 6개 소제목, 각 소제목 바로 아래 사진 2장씩 ...)
마무리(CTA)...
(사진15: 파일명)
(사진16: 파일명)
★(사진)은 **2장씩 묶어** 배치: 도입 2장 + 소제목 6개 각 2장 + 마무리 2장 = 총 12~16장. 각 (사진N) 줄은 한 줄에 하나씩 연속해서 쓴다.
★사용 사진이 그보다 적으면 있는 만큼만 배치한다(같은 사진 반복 금지, 없는 파일명 지어내기 금지). 부족하면 묶음을 1장으로 줄이거나 자리를 비운다.
규칙: 사진은 아래 '사용 사진' 목록의 파일명만 (사진N: 정확한파일명) 형태로 배치. 목록에 없는 파일명 만들지 말 것.
★중요: 각 슬롯에는 **서로 다른 사진**을, 그 단락 내용에 **가장 어울리는 사진**으로 배치하라.

[카드뉴스]"""
    else:
        photo_fmt = """[출력 형식 — 정확히 이 형식만, 다른 설명/머리말 금지]
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

[카드뉴스]"""
    if (b.get("table_rule") or "") == "required":
        table_fmt = """[표 — ★필수 정확히 1개 (브랜드 규칙)]
- 견적·일정·선택 기준을 다루는 소제목 본문의 해당 자리에 (표1) 마커를 한 줄로 넣는다(표는 1개, 차트는 넣지 않는다). 그리고 맨 끝 '표차트:' 섹션에 데이터를 준다.
- ★표는 이미지로 렌더되므로 (표1) 바로 아래 본문에 표 요지를 텍스트 2~3줄로 다시 적는다(AEO — 글로도 설명).
- 지어낸 수치 금지 — 근거가 분명한 값만.
표차트:
표1 | 제목 | 헤더1,헤더2,헤더3 ; 항목,값,값 ; 항목,값,값 ; 항목,값,값 ; 항목,값,값 ; 항목,값,값"""
    else:
        table_fmt = """[표·차트 — 선택. 한눈에 보면 정말 도움되는 정보가 있을 때만(비교/단계/비율/추이 등). 억지로 넣지 말 것]
- 넣을 경우: 그 정보가 나오는 자리의 본문에 (표1) 또는 (차트1) 마커를 한 줄로 넣는다(최대 2개). 그리고 맨 끝에 아래 '표차트:' 섹션에 데이터를 준다.
- ★이미지는 보조일 뿐이므로, 표·차트를 넣더라도 본문 텍스트 설명은 그대로 유지한다(AEO를 위해 글로도 설명).
- 지어낸 수치 금지 — 근거가 분명한 값만. 마커를 하나도 안 넣었으면 '표차트: 없음'.
표차트: (없으면 "없음")
표1 | 제목 | 헤더1,헤더2,헤더3 ; 항목,값,값 ; 항목,값,값
차트1 | 막대 | 제목 | 라벨:숫자, 라벨:숫자, 라벨:숫자   (막대 대신 원/선도 가능)"""
    return photo_fmt + """
원고를 다 쓴 뒤 맨 끝에 카드 7장을 출력한다. 각 줄은 "헤드라인 | 본문설명" 형식이다.
★★카드와 본문 소제목을 반드시 1:1, 같은 순서로 맞춘다(가장 중요 — 어긋나면 안 됨):
- 카드1 = 표지(메인키워드).
- 카드2~7 = 본문의 첫째~여섯째 소제목을 '그 순서 그대로' 요약한다. 즉 카드N(2~7)의 주제 = 본문 (N-1)번째 소제목과 같아야 한다. (소제목이 '비용'이면 그 자리 카드도 반드시 '비용', 소제목이 '필요서류'면 카드도 '필요서류'. 다른 주제를 넣지 말 것.)
- 헤드라인: 그 소제목의 핵심을 12자 내외로 짧고 강하게.
- 본문설명: 그 카드 내용을 1문장으로 자연스럽게(35자 내외).""" + extra + """
카드뉴스:
1. (메인키워드 — 표지) | (한 줄 설명)
2. (본문 첫째 소제목 요약) | (한 줄 설명)
3. (본문 둘째 소제목 요약) | (한 줄 설명)
4. (본문 셋째 소제목 요약) | (한 줄 설명)
5. (본문 넷째 소제목 요약) | (한 줄 설명)
6. (본문 다섯째 소제목 요약) | (한 줄 설명)
7. (본문 여섯째 소제목 요약) | (한 줄 설명)
표지부제: (표지 큰제목 아래 한 줄 부제 — 이 글 주제를 요약하는 짧은 후킹 문장, 18자 내외)

""" + table_fmt


_AEO_BLOCK = """[AEO·GEO 최적화 — AI(네이버 AI·ChatGPT·Gemini 등)가 읽고 '인용·추천'하게 쓰기]
- ★타겟의 '진짜 질문'을 먼저 상상하라: 사람들은 AI에 매끈한 서비스 키워드로 안 묻고, 자기 상황을 구체적으로 말하며 추천·판단을 구한다. [저 OO(업종)인데 / OO 상황인데] + [추천해줘 / A가 나아 B가 나아 / 이것도 돼? / 비용 얼마 / 뭘 보고 골라 / 요즘 뭐가 먹혀] 형태다(업종×서비스×상황×구매의도 조합, 예: '맛집 하는데 요즘도 전단지가 나아 SNS가 나아?', '치과인데 학회용 카탈로그 잘하는 곳 추천해줘'). '제작 순서/방법/어떻게 시작' 같은 아무도 안 하는 절차 질문은 버린다. 이 글이 그 진짜 질문의 '답'이 되게 쓴다.
- ★맨 앞에 핵심 요약: 본문 가장 앞에서 이 글의 결론·핵심 답을 3~4문장으로 먼저 준다(AI는 앞부분을 먼저 읽고 인용한다).
- 두괄식: 각 소제목의 첫 1~2문장에서 그 궁금증에 대한 '결론·핵심 답'(일반화된 정답)을 먼저 말하고 근거·사례를 뒤에 푼다.
- 소제목은 타겟이 실제로 궁금해하는 것(구매의도)에 답하는 형태로 짓는다. 절차·정의 나열이 아니라 매 소제목이 하나의 구체적 결정·질문에 답하게 한다.
- FAQ류 질문은 고객이 실제로 말하는 대화체 그대로 쓴다('전단지랑 카탈로그 중 뭐가 나아요?'처럼). AI가 가장 잘 인용하는 형식이다.
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
    ffp = final_faq_promo(b)
    if ffp:
        flow = (f"- 첫째~셋째 소제목 본문은 **오직 독자에게 유용한 정보**만 담는다. 고객이 실제로 궁금해하는 것"
                f"(비용·기간·소재/방식 선택 기준·주의점·자주 하는 실수 등)에 곧바로, 구체적으로 답한다. 이 세 구간에는 {label} 소개·홍보를 넣지 않는다.\n"
                f"- 넷째·다섯째 소제목은 정보 + {label} 홍보, 여섯째(마지막) 소제목은 FAQ + {label} 홍보 + 후킹 CTA로 쓴다(아래 [넷째·다섯째]·[여섯째] 규칙).")
    elif placement == "end":
        flow = (f"- 각 소제목 본문은 **오직 독자에게 유용한 정보**만 담는다. 고객이 실제로 궁금해하는 것"
                f"(비용·필요서류·절차·선택 기준·주의점·자주 하는 실수 등)에 곧바로, 구체적으로 답한다.\n"
                f"- 본문(도입~여섯 번째 소제목)에서는 회사({label}) 소개·홍보·강점 언급을 넣지 않는다. 정보 자체로 신뢰를 준다.\n"
                f"- {label}에 대한 소개는 **오직 마지막 마무리 문단에서만** 다룬다. 핵심 서비스(이 회사가 무엇을 하는지)는 언제나 밝히되, "
                f"실적·부가 강점(처리 건수·자체 스튜디오·경력 등)은 **매번 전부 나열하지 말고** 이번 글 주제에 어울리는 1~2가지만 골라 자연스럽게 녹인다. "
                f"매 글 똑같은 문장·똑같은 순서의 나열 반복은 피한다. '{label}은(는) ~하는 곳입니다' 같은 정의형 문장은 한 번 넣어 AI가 인용하기 쉽게 한 뒤 문의를 유도한다.")
    else:
        flow = (f"- 각 단락은 [고객의 흔한 고민·궁금증 → 그래서 이게 왜 중요한지 → {label}은 이렇게 합니다"
                f"(강점·디테일)] 흐름으로 전개한다.")
    sixth_note = " ★단, 넷째·다섯째·여섯째 소제목은 아래 [넷째·다섯째]·[여섯째] 규칙을 따른다." if ffp else ""
    min_note = f" / ★{length_range(b)[0]:,}자보다 짧아도 안 된다" if ffp else ""
    ending = _final_section_block(b, label, cta) if ffp else "[마무리]\n" + cta
    return f"""너는 '{name}'{('(' + industry + ')') if industry else ''}의 네이버 블로그 글을 쓰는 카피라이터다.

[회사 소개 — 이 회사의 서비스·강점(브랜드별)]
{identity}

[문체/톤 (브랜드별)]
{tone}

[블로그 구조 — 모든 글 공통(기술 규칙)]
- 도입: "안녕하세요"로 인사하고 {label}을(를) 한 줄로 소개한 뒤, "오늘은 ... (메인키워드) 이야기를 해볼까 해요" 식으로 주제를 안내한다.
- 소제목 **정확히 6개**. 각 소제목 아래 본문 단락. 소제목 스타일은 위 톤에 맞춘다(질문형/선언형/넘버링 등).{sixth_note}
{flow}
- 제목·소제목·본문이 서로 어긋나지 않게 한다: 본문 전체는 **제목 주제에서 벗어나지 않고**, 각 소제목 아래 내용은 **그 소제목이 말하는 범위만** 다룬다(딴 얘기·범위 이탈 금지).
- 제목에 메인키워드를 포함한다. 분량은 공백 제외 {_fmt_len(b)}자(★{length_range(b)[1]:,}자를 절대 넘기지 말 것 — 넘칠 것 같으면 덜 중요한 문장·군더더기·중복 설명을 덜어낸다{min_note}). 메인키워드를 제목·소제목·본문에 자연스럽게 5~8회 녹인다(억지 반복 금지).
- 한 문장(또는 의미단위)마다 줄바꿈(네이버 모바일 가독성). 과장·AI티('~에 대해 알아보겠습니다' 등) 금지.

{_AEO_BLOCK}

{ending}"""



def final_faq_promo(b):
    """brand.json final_faq_promo=true 인 브랜드(하오디자인·하오스튜디오·하오팩토리):
    여섯째(마지막) 소제목 = FAQ 3~4개 + 브랜드 홍보 + 후킹 CTA 로 글을 끝낸다(그 뒤 별도 마무리 문단 없음)."""
    return bool((b or {}).get("final_faq_promo"))


# 여섯째 소제목 '브랜드 홍보'의 전개 방식 — 매 글 무작위로 하나를 지정해 홍보 문단이 같은 틀로 굳지 않게 한다
_PROMO_ANGLES = [
    "독자가 이 주제에서 가장 걱정할 문제 하나를 짚고 → {label}의 작업 구조가 그 문제를 어떻게 막는지 보여주기",
    "의뢰 후 결과물을 받기까지의 흐름을 따라가며 → 단계마다 {label}{ga} 직접 챙기는 지점을 보여주기",
    "흔히 여러 업체에 나눠 맡길 때 생기는 문제와 → {label}에서 한곳에 맡길 때의 차이를 대비하기",
    "이번 글 주제(이 업종·이 산출물)의 실제 작업 장면 하나를 그리며 → 그 장면에서 드러나는 {label}의 강점 보여주기",
    "결과물 품질을 좌우하는 포인트 2~3가지를 짚고 → {label}{ga} 그 포인트를 어떻게 관리하는지 보여주기",
    "{label}{ga} 어떤 곳인지 한 문장으로 정의한 뒤 → 이번 주제와 맞닿은 강점을 구체적 장면·이점으로 풀어가기",
]


def _eun(word):
    """받침 있으면 '은', 없으면 '는'(하오디자인은 / 하오스튜디오는)."""
    ch = (word or " ")[-1]
    return "은" if "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 else "는"


# 넷째·다섯째 소제목 '정보 + 브랜드 홍보' 연결 방식 — 매 글 무작위로 2개를 골라 두 소제목이 같은 틀이 되지 않게 한다
_MIX_STYLES = [
    "정보의 결론(그래서 무엇이 중요한가)을 말한 뒤 → '그래서 {label}{eun} ~합니다' 식으로 실제 작업 방식을 이어 붙이기",
    "흔한 실수·실패 사례를 짚은 뒤 → {label}의 작업 구조가 그 실수를 어떻게 막는지 한두 문장으로 보여주기",
    "체크포인트를 제시한 뒤 → 그중 하나를 {label}{ga} 어떻게 챙기는지 구체적 장면으로 보여주기",
    "정보 속 사례 장면에 {label}의 작업을 증거로 녹이기(사례 → 그 사례에서 드러난 강점)",
    "독자가 직접 하면 번거로운 부분을 짚은 뒤 → {label}에 맡기면 무엇이 덜어지는지 보여주기",
    "두 선택지를 비교한 정보 끝에 → {label}{ga} 그 선택을 어떻게 도와주는지 한두 문장으로 잇기",
]


def _ga(word):
    """받침 있으면 '이', 없으면 '가'(하오디자인이 / 하오스튜디오가)."""
    return "이" if _eun(word) == "은" else "가"


def _final_section_block(b, label, cta):
    """넷째·다섯째 소제목(정보+홍보) + 여섯째 소제목(FAQ+홍보+CTA) 규칙. 홍보 재료를 매 글 무작위로
    세 소제목에 '겹치지 않게' 나눠 배정 → 홍보끼리 같은 강점·같은 의미가 반복되지 않는다."""
    lo, hi = length_range(b)
    pts = [str(p).strip() for p in ((b or {}).get("promo_points") or []) if str(p).strip()]
    random.shuffle(pts)                      # 배정·나열 순서가 매번 달라지게
    p4, p5, p6 = (pts[0], pts[1], pts[2:]) if len(pts) >= 3 else ("", "", pts)
    s4, s5 = (st.format(label=label, eun=_eun(label), ga=_ga(label)) for st in random.sample(_MIX_STYLES, 2))
    angle = random.choice(_PROMO_ANGLES).format(label=label, eun=_eun(label), ga=_ga(label))
    note = ((b or {}).get("promo_note") or "").strip()
    notel = ("\n  ※ 홍보 공통 주의: " + note) if note else ""
    mat = lambda p: p if p else "이번 주제와 맞닿은 강점 하나(여섯째에서 쓸 강점과 겹치지 않게)"
    ptsblk = ("\n    [여섯째 소제목 홍보 재료 — 사실 그대로만. ★ 항목은 이 브랜드의 핵심이라 되도록 넣되 표현·각도는 매번 바꾸고, 나머지에서 이번 주제와 맞는 것을 더한다. 목록에 없는 실적·수치·설비는 지어내지 않는다]\n"
              + "\n".join("    · " + p for p in p6)) if p6 else ""
    return f"""[★넷째·다섯째 소제목 — 정보 + {label} 홍보를 함께 쓴다]
- 넷째·다섯째도 소제목 문구는 독자가 궁금한 '정보' 주제로 짓는다(소제목에 브랜드명을 넣지 않는다).
- 본문 앞부분(약 2/3)은 그 소제목의 정보로 채우고, 뒷부분 1~2문장(공백 제외 약 60~90자)에서 그 정보와 자연스럽게 이어지는 {label}의 강점 하나를 보여준다. 광고 문구를 툭 끼워 넣지 말고, 앞 정보의 결론·해결책으로 이어지게 쓴다.
  · 넷째 소제목 — 홍보 재료: {mat(p4)} / 연결 방식: {s4}
  · 다섯째 소제목 — 홍보 재료: {mat(p5)} / 연결 방식: {s5}
- ★넷째·다섯째·여섯째의 홍보는 서로 다른 강점·다른 이점을 다룬다. 같은 강점이나 같은 의미를 표현만 바꿔 되풀이하지 않는다. 지정 재료가 이번 주제와 도저히 안 맞으면 아래 여섯째 재료 중 하나와 바꿔 써도 되지만, 그때도 세 곳이 겹치지 않게 한다.
- 첫째~셋째 소제목에는 {label} 홍보를 넣지 않는다(정보만).{notel}

[★여섯째(마지막) 소제목 — FAQ + {label} 홍보 + 후킹 CTA 로 글을 끝낸다]
- 여섯째 소제목은 '자주 묻는 질문'임이 드러나게 짓고(예: "OO 자주 묻는 질문"), 아래 ①→②→③ 순서 그대로 쓴다. 이 소제목 뒤에 별도 마무리 문단·소제목을 더 만들지 않는다.
  ① FAQ **3~4개**: 'Q. (질문)' 줄 다음에 'A. (답)' 줄. 질문은 이 글의 타겟 고객이 실제로 묻는 말투 그대로(비용·기간·가능 여부·선택 기준 등), 답은 1~2문장으로 구체적으로(기준·범위·조건). 앞 소제목에서 한 설명을 그대로 되풀이하지 말고 남은 궁금증을 짚는다. 답에는 {label} 이름·홍보를 넣지 않는다(정보성 답이어야 AI가 인용한다).
  ② {label} 홍보 **4~5문장(공백 제외 약 200~250자)** — 독자가 '여기에 맡기면 이런 점이 확실히 낫겠다'고 느끼게 구체적으로 쓴다:
    - 강점을 이름만 나열하지 말고, 각 강점이 독자에게 주는 실제 이점(무슨 문제를 막아 주는지·무엇이 편해지는지)까지 풀어 준다. 예) '내부 인쇄소' → 디자인 시안에서 본 색과 실제 인쇄 색이 달라지는 문제를 같은 곳에서 바로 잡는다.
    - 넷째·다섯째에서 이미 쓴 강점은 다시 쓰지 않는다. 아래 재료에서 이번 글 주제와 연결되는 2~3개를 쓴다. 매 글 같은 순서·같은 문장으로 쓰지 않는다.
    - 이번 글의 홍보 전개 방식: {angle}. (내용에 도저히 안 맞으면 가장 가까운 다른 방식으로 바꿔도 되지만, 정형화된 '회사 소개문' 틀로 돌아가지 말 것)
    - '{label}{_eun(label)} ~하는 곳입니다'처럼 회사를 정의하는 문장은 한 번만, 위치는 자유롭게. 과장(최고·최초·완벽)·이모지 금지.{ptsblk}
  ③ 후킹 CTA 1~2문장: 독자가 '지금' 문의할 이유를 만드는 문장으로 끝낸다 — 독자의 구체적 고민(일정·예산·소재/방식 선택 등)을 짚고, 문의하면 바로 무엇을 받을 수 있는지(예: 상황에 맞는 방식 제안·견적 범위 안내)를 보여준다. 과장·명령조·이모지 없이, 아래 브랜드 CTA 기준을 바탕으로 이번 글 주제에 맞게 매번 새 문장으로 쓴다.
    브랜드 CTA 기준: {cta}
- 분량 배분(공백 제외, 전체 {lo:,}~{hi:,}자): 맨 앞 요약+인사+도입 약 200자 / 첫째~셋째 소제목 각 약 190자 / 넷째·다섯째 소제목 각 약 230자(정보 약 150자 + 홍보 약 60~90자) / 여섯째 소제목 약 500자(FAQ 약 240자 + 홍보 약 200~250자 + CTA 약 60자)."""


def photo_layout(b):
    """사진 배치 방식. 'pairs'=2장씩 묶음(12~16장, 퍼스트디자인 방식2) / 그 외=도입1+소제목6 = 7장(기본)."""
    return ((b or {}).get("photo_layout") or "").strip().lower()


def photo_slots(b):
    """이 브랜드가 한 글에 배치할 (사진N) 슬롯 최대 개수."""
    return 16 if photo_layout(b) == "pairs" else 7


def length_range(b):
    """공백 제외 분량 범위 (min, max). brand.json length=[min,max] 또는 "1,700~2,200". 없으면 1500~2000."""
    lr = (b or {}).get("length")
    try:
        if isinstance(lr, (list, tuple)) and len(lr) == 2:
            return int(lr[0]), int(lr[1])
        if isinstance(lr, str) and lr.strip():
            m = re.findall(r"\d[\d,]*", lr)
            if len(m) >= 2:
                return int(m[0].replace(",", "")), int(m[1].replace(",", ""))
    except Exception:
        pass
    return 1500, 2000


def _fmt_len(b):
    lo, hi = length_range(b)
    return "{:,}~{:,}".format(lo, hi)


def prompt_file_text(bid):
    """브랜드 폴더의 prompt.md(완전 커스텀 스크립트 파일). brand.json prompt 필드가 비어 있을 때 대신 쓴다."""
    try:
        p = os.path.join(brand_dir(bid), "prompt.md")
        if os.path.isfile(p):
            return open(p, encoding="utf-8").read().strip()
    except Exception:
        pass
    return ""


def custom_prompt(b):
    """brand.json prompt 필드 → 없으면 brands/<id>/prompt.md."""
    b = b or {}
    return (b.get("prompt") or "").strip() or prompt_file_text(b.get("id", ""))


def title_rules(b):
    """커스텀 스크립트(prompt.md / prompt 필드)의 [제목] 섹션 본문. 없으면 빈 문자열.
    제목 추천 등 '제목만 따로 뽑는' 기능이 브랜드 제목 규칙을 그대로 따르게 하기 위함."""
    txt = custom_prompt(b)
    if not txt:
        return ""
    m = re.search(r"^\[제목[^\]]*\]\s*\n(.*?)(?=^\[|\Z)", txt, re.S | re.M)
    if m:
        return m.group(1).strip()
    # 채널 표준 프롬프트(마크다운): "## 1. 제목 ..." / "## 2. 제목 (25~45자)" / "## 1. 제목 규칙" 섹션
    m = re.search(r"^## \d+(?:-\d+)?\. 제목[^\n]*\n(.*?)(?=^## |\Z)", txt, re.S | re.M)
    return m.group(1).strip() if m else ""


_RSS_TTL = 6 * 3600           # 네이버 RSS 캐시 유지 시간(초) — 매일 새 글이 올라와도 하루 안에 반영됨
_RSS_PER_BLOG = 25            # 블로그당 내부링크 후보 최대 개수(프롬프트 길이 관리)


def _fetch_blog_rss(blog_id):
    """rss.blog.naver.com/<id>.xml → ['제목 | URL', ...] (최신순). 실패 시 예외."""
    url = "https://rss.blog.naver.com/%s.xml" % blog_id
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    xml = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
    rows = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S)[:_RSS_PER_BLOG]:
        t = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", it, re.S) or re.search(r"<title>(.*?)</title>", it, re.S)
        l = re.search(r"<link><!\[CDATA\[(.*?)\]\]></link>", it, re.S) or re.search(r"<link>(.*?)</link>", it, re.S)
        if not (t and l):
            continue
        u = l.group(1).split("?")[0].replace("http://", "https://").strip()
        rows.append("%s | %s" % (t.group(1).strip(), u))
    return rows


def _rss_link_rows(b):
    """brand.json link_blogs(네이버 블로그 id 목록) → RSS로 최신 글 목록. 캐시(links_cache.json, TTL 6h),
    네트워크 실패 시 만료된 캐시라도 사용. 빈 목록이면 []."""
    blogs = (b or {}).get("link_blogs") or []
    if not blogs:
        return []
    cache_p = os.path.join(brand_dir(b.get("id", "")), "links_cache.json")
    cache = {}
    try:
        cache = json.load(open(cache_p, encoding="utf-8"))
    except Exception:
        pass
    now = time.time()
    changed = False
    for bid in blogs:
        ent = cache.get(bid) or {}
        if ent.get("rows") and now - ent.get("t", 0) < _RSS_TTL:
            continue
        try:
            rows = _fetch_blog_rss(bid)
            if rows:
                cache[bid] = {"t": now, "rows": rows}
                changed = True
        except Exception:
            pass                      # 실패 → 있는 캐시 그대로(만료돼도) 사용
    if changed:
        try:
            json.dump(cache, open(cache_p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        except Exception:
            pass
    out = []
    for bid in blogs:
        out += (cache.get(bid) or {}).get("rows") or []
    return out


def links_block(b):
    """내부 링크 후보 블록. brand.json link_blogs(RSS 자동 갱신) + brands/<id>/links.txt(수동 추가) 합침."""
    rows = _rss_link_rows(b)
    try:
        p = os.path.join(brand_dir((b or {}).get("id", "")), "links.txt")
        if os.path.isfile(p):
            manual = [ln.strip() for ln in open(p, encoding="utf-8").read().splitlines()]
            urls = {r.split("|")[-1].strip() for r in rows}
            for r in manual:
                if r and not r.startswith("#") and r.split("|")[-1].strip() not in urls:
                    rows.append(r)
    except Exception:
        pass
    if not rows:
        return ""
    return ("\n\n[내부링크 후보 — 운영 중인 블로그들의 기존 글. 맨 끝 '함께 보면 좋은 글'은 반드시 이 목록에서만 고른다]\n"
            "- ★본문 중간에는 링크를 넣지 않는다. 관련 글 안내는 맨 끝 '함께 보면 좋은 글' 한 곳에서만 한다.\n"
            "- ★제목과 URL을 반드시 세트로 출력한다 — 제목만 쓰고 URL을 빼먹는 것 금지. "
            "'함께 보면 좋은 글'은 `「제목」` 다음 줄에 URL 한 줄 형식으로 쓴다(네이버에 붙일 때 그대로 링크로 바꿀 수 있게).\n"
            "- 제목은 목록의 표기 그대로, URL도 목록의 값 그대로. 이 글 주제와 가장 관련 있는 것을 고르고, 목록에 없는 제목·URL을 지어내지 않는다.\n"
            + "\n".join("- " + r for r in rows))


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
    return ("\n\n[★브랜드 사실 기준서 — 사실 '정확성'의 근거일 뿐, '매 글에 넣을 목록'이 아님]\n"
            "아래는 이 브랜드의 실제 서비스·가격·절차·규칙이다. 사실관계를 쓸 때는 반드시 아래 값만 따르고, "
            "가격·소요기간은 표에 있는 값만 쓰되 없으면 '서류 확인 후 안내'로 열어 둔다('무조건 가능' 등 단정 금지). "
            "협약국/비협약국 구분, 공증 타입(공문서=번역공증 / 사문서·위임=사실공증 / 무번역 원본=원본대조공증), 지원 언어 등은 "
            "'틀리지 않기 위한' 기준일 뿐이다.\n"
            "★★매우 중요 — 이 기준서를 '체크리스트'처럼 매 글에 다 넣지 말 것. 이번 글은 오직 '메인키워드가 실제로 묻는 그 하나'에만 "
            "집중하고, 그 주제와 직접 관련될 때에만 해당 사실을 꺼내 쓴다. 특히 '협약국 vs 비협약국', '번역공증 vs 사실공증', "
            "'지원 8개 언어' 안내를 이번 글 주제와 상관없이 습관적으로 끼워 넣지 말 것. 아포스티유 글이라고 매번 협약국 설명, 번역 글이라고 "
            "매번 8개 언어 나열처럼 '똑같은 몇 개 주제로 도는' 글이 되면 안 된다. 키워드가 요구하는 그 한 주제를 남들이 안 다루는 각도까지 "
            "깊고 구체적으로 파고들어라(같은 키워드라도 매번 다른 하위 논점·사례·순서로).\n"
            "----- 기준서 시작 -----\n" + g + "\n----- 기준서 끝 -----")


def _faq_questions(b):
    """브랜드 폴더의 FAQ 질문 리스트 파일(brand.json faq_list). {분야: [질문,...]} 형식. 없으면 {}."""
    fn = (b.get("faq_list") or "").strip()
    if not fn:
        return {}
    try:
        p = os.path.join(brand_dir(b.get("id", "")), fn)
        if os.path.isfile(p):
            return json.load(open(p, encoding="utf-8"))
    except Exception:
        pass
    return {}


def faq_block(b, keyword="", subkeyword="", title="", n=25):
    """FAQ 질문 리스트가 있는 브랜드용 — 이번 글과 관련 있는 후보 질문을 골라
    '마지막 소제목 = FAQ(리스트에서 5개 선택)' 지시 블록을 만든다. 리스트 없으면 빈 문자열."""
    blocks = _faq_questions(b)
    if not blocks:
        return ""
    q = f"{keyword} {subkeyword} {title}"
    toks = [t for t in re.split(r"[\s,·/|+]+", q) if len(t) >= 2]
    def score(s):
        return sum(1 for t in toks if t in s)
    allq = [(cat, s) for cat, lst in blocks.items() for s in lst if isinstance(s, str)]
    matched = sorted([cs for cs in allq if score(cs[1]) > 0], key=lambda cs: -score(cs[1]))
    cand = [s for _, s in matched[:n]]
    if len(cand) < n:
        # 매칭이 부족하면 키워드로 분야를 추정해 그 분야에서 무작위 보충
        ql = q.lower()
        if any(w in ql for w in ("홈페이지", "쇼핑몰", "웹", "랜딩", "사이트")):
            cat = "홈페이지 제작"
        elif any(w in ql for w in ("마케팅", "sns", "인스타", "릴스", "숏폼", "광고", "유튜브", "이커머스", "블로그")):
            cat = "마케팅"
        else:
            cat = "홍보물 디자인"
        # 추정 분야가 이 브랜드 리스트에 없으면(예: 트래비티) 전체 리스트에서 보충
        src = blocks.get(cat) or [s for lst in blocks.values() for s in lst]
        pool = [s for s in src if s not in cand]
        if pool:
            cand += random.sample(pool, min(n - len(cand), len(pool)))
    if not cand:
        return ""
    qlist = "\n".join(f"- {s}" for s in cand)
    return ("\n\n[★FAQ — 마지막(여섯 번째) 소제목은 '자주 묻는 질문'으로 한다]\n"
            "- 마지막 소제목은 FAQ로 하고, 아래 '실제 질문 리스트'에서 이 글의 제목·본문 내용과 가장 관련 있는 질문 5개를 골라 질문·답으로 구성한다.\n"
            "- 고른 질문은 그대로 쓰거나 자연스럽게 다듬되 '업종+지원사업+실제 상황' 말투를 유지한다(타겟이 AI에 실제로 묻는 형태 그대로가 가장 잘 인용된다). "
            "리스트에 이 글 주제와 맞는 질문이 없을 때만 '○○ 업종/수출기업인데, [상황]. [질문]?' 공식으로 새로 만든다.\n"
            "- 답은 구체적으로(기준·기간·범위·선택 기준). 5개 중 브랜드 홍보로 귀결되는 답은 최대 2개까지만 — "
            "나머지 3개 이상은 브랜드명 없이도 성립하는 순수 정보성 답으로 쓴다(정보성 답이 살아야 AI가 인용한다).\n"
            "[실제 질문 리스트 — 후보]\n" + qlist)


_NATURAL_TONE = """[자연스러운 말투 — 'AI가 쓴 티'를 지운다 ★모든 브랜드 공통]
- 종결어미(합니다/됩니다 · 해요/이에요 등)와 문장부호(쉼표·마침표·물음표 등)는 위에서 지정한 브랜드가 쓰던 방식을 그대로 지킨다. 바꾸는 건 어미·부호가 아니라 '쓰는 방식'이다. 단, 같은 종결어미를 기계적으로 연달아 반복하지 말고(예: '~습니다'만 계속) 자연스럽게 변화를 줘 어느 문장 끝이든 어색하지 않게 한다.
- AI 티 나는 상투구 금지: "~에 대해 알아보겠습니다", "지금까지 ~를 알아봤습니다"처럼 기계적인 요약 상투구, "먼저/다음으로/마지막으로"의 기계적 나열, 질문을 그대로 되풀이한 뒤 답하기. (마무리에 핵심을 자연스럽게 짚어 정리하는 것 자체는 괜찮다 — 위 같은 상투적 문구만 피할 것.)
- 실제 실무자가 말하듯 쓴다: 현장에서 겪는 구체적 상황·사례·자주 받는 질문을 곁들이고, 뻔한 일반론·교과서식 정리는 피한다.
- 문장 길이와 리듬에 변화를 준다(짧은 문장·긴 문장 섞기). '또한/그리고/이러한' 같은 접속 표현을 남발하지 않는다.
- 결론을 빙빙 돌리지 말고 핵심을 먼저 담백하게. 매 문단이 똑같은 리듬으로 반복되지 않게 한다.
- 사람이 읽었을 때 '광고·AI 글'이 아니라 '아는 사람이 편하게 알려주는 글' 느낌이 나야 한다."""


def _selfcheck(b):
    """발행 전 자가 점검 — 사진 개수·분량·표 규칙은 브랜드 설정(photo_layout / length / table_rule)에 맞춘다."""
    b = b or {}
    lo, hi = length_range(b)
    photos = "(사진) 2장씩 묶어 12~16개(사용 사진이 부족하면 있는 만큼)" if photo_layout(b) == "pairs" else "(사진) 정확히 7개"
    tbl = ("- 표가 정확히 1개((표1) 마커 + 표차트 데이터) 있고, 그 바로 아래 텍스트 요지 2~3줄이 있는가."
           if (b.get("table_rule") or "") == "required" else
           "- 비교·가격·절차 같은 정보는 텍스트 표/목록으로 정리했는가.")
    return ("[발행 전 자가 점검 — 아래를 스스로 확인한 뒤 최종본만 출력한다. 점검 결과·체크리스트는 절대 출력하지 말 것]\n"
            "- 지어낸 수치·사실이 없는가. (사실 기준서가 있으면 그 값만 썼는가.)\n"
            "- 막연한 표현 대신 구체적 사실·수치·명칭으로 썼는가. 뻔한 일반론이 아니라 실제로 유용한가.\n"
            f"- 소제목 정확히 6개, {photos}, 제목·본문에 메인키워드가 자연스럽게 들어갔는가.\n"
            f"- ★분량이 공백 제외 {lo:,}~{hi:,}자 범위인가({hi:,}자를 넘지 않았는가 — 넘으면 군더더기를 덜어낸다).\n"
            "- 본문 내용이 제목·각 소제목이 말하는 주제와 정확히 맞물리는가(범위 이탈·딴 얘기 없는가).\n"
            "- 문체가 지정한 톤(어미)은 지키되, 'AI가 쓴 티'가 나지 않고 사람이 쓴 것처럼 자연스러운가.\n"
            + (f"- ★분량이 {lo:,}자보다 짧지 않은가(짧으면 첫째~다섯째 소제목에 구체적 기준·사례 문장을 보탠다).\n"
               "- 첫째~셋째 소제목은 정보만 있는가. 넷째·다섯째 소제목은 정보 뒤에 브랜드 홍보 1~2문장이 자연스럽게 이어지는가.\n"
               "- 여섯째(마지막) 소제목이 FAQ 3~4개(Q./A.) → 브랜드 홍보 4~5문장 → 후킹 CTA 순서이고, 그 뒤에 다른 문단이 없는가.\n"
               "- 넷째·다섯째·여섯째의 홍보가 서로 다른 강점을 다루는가(같은 강점·같은 의미 반복 없음).\n"
               "- 홍보가 강점 이름 나열이 아니라, 강점마다 독자가 얻는 이점까지 구체적으로 풀었는가. 홍보 재료 목록에 없는 실적·수치를 지어내지 않았는가.\n"
               if final_faq_promo(b) else "")
            + tbl)


_SELFCHECK = _selfcheck({})   # 하위 호환(기본 브랜드용)


def build_style(b):
    """브랜드 설정 → 글 생성 시스템 프롬프트.
    prompt(완전 커스텀)가 있으면 그걸 쓰고, 없으면 전 브랜드 공통 구조 + 회사 소개. 출력 형식은 항상 부착.
    브랜드 폴더에 guide.md(사실 기준서)가 있으면 '반드시 준수' 블록으로 함께 부착.
    발행 전 자가 점검(AEO·사실 정확성)은 모든 글에 부착."""
    if b and b.get("channel"):          # 채널 표준 프롬프트(네이버 블로그/카페) — apply_channel()로 얹힌 경우
        return build_style_channel(b)
    custom = custom_prompt(b)
    head = custom.replace("{name}", b.get("name", "")) if custom else _shared_structure(b)
    return (head + _guide_block(b) + links_block(b) + "\n\n" + _output_format(b) +
            "\n\n" + _NATURAL_TONE + "\n\n" + _selfcheck(b))
