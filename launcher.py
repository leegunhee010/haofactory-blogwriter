# -*- coding: utf-8 -*-
"""
블로그 작성기 — 런처 (exe 진입점)
===================================
1) 최초 실행: exe 안에 번들된 app_bundle.zip 을 exe 옆에 풀어둠
2) GitHub version.json 확인 → 새 버전이면 "업데이트?" 팝업 → update.zip 받아 덮어씀
   (사용자 데이터 '출력/'·'작성기_설정.json'·'brands/'는 보존)
3) exe 옆의 작성기앱.py(앱 본체)를 로드해 실행
exe는 파이썬+Flask+PIL+numpy+docx+pptx 런타임을 품은 껍데기이고,
실제 로직/디자인(작성기앱.py·cardnews_pil.py·brands.py·brands/·assets/)은 바깥에 있어 GitHub로 갱신됩니다.
"""
import os, sys, io, json, zipfile, importlib.util, urllib.request, ctypes
# ↓ 동적 로드되는 앱이 쓰는 라이브러리 — PyInstaller가 exe에 포함하도록 여기서 import
import flask                       # noqa
import numpy                       # noqa
import PIL.Image, PIL.ImageDraw, PIL.ImageFont, PIL.ImageOps, PIL.ImageEnhance, PIL.ImageFilter  # noqa
import docx                        # noqa  (python-docx)
import pptx                        # noqa  (python-pptx)

FROZEN = getattr(sys, "frozen", False)
HERE = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.abspath(__file__))
MEI = getattr(sys, "_MEIPASS", HERE)

REPO = "leegunhee010/haofactory-blogwriter"   # ← 배포용 GitHub 저장소 (owner가 생성)
RAW = "https://raw.githubusercontent.com/%s/main/" % REPO
APP = "작성기앱.py"
PRESERVE = ("출력", "작성기_설정.json", "accounts", "accounts.json")   # 업데이트 시 덮어쓰지 않을 사용자 데이터(생성물·로컬설정·Claude 계정 자격증명)
# brands/(브랜드 설정·카드 템플릿)·assets/·코드는 owner가 배포·갱신하는 공유 콘텐츠라 업데이트 대상


def _box(msg, title, flags):
    try:
        return ctypes.windll.user32.MessageBoxW(0, str(msg), title, flags)
    except Exception:
        print(title, "-", msg)
        return 0


def _vt(s):
    try:
        return tuple(int(x) for x in str(s).split("."))
    except Exception:
        return (0,)


def local_version():
    try:
        return json.load(open(os.path.join(HERE, "version.json"), encoding="utf-8")).get("version", "0")
    except Exception:
        return "0"


def _extract(zbytes, skip_preserve):
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    for name in z.namelist():
        if name.endswith("/"):
            continue
        top = name.split("/")[0]
        if skip_preserve and top in PRESERVE:
            continue
        dst = os.path.join(HERE, name.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with z.open(name) as src, open(dst, "wb") as out:
            out.write(src.read())


def ensure_files():
    # 최초 실행 — exe 옆에 앱 본체가 없으면 번들 zip 을 풀어둠
    if os.path.exists(os.path.join(HERE, APP)):
        return
    bundle = os.path.join(MEI, "app_bundle.zip")
    if os.path.exists(bundle):
        try:
            _extract(open(bundle, "rb").read(), skip_preserve=False)
        except Exception as e:
            _box("초기 설치 실패: %s" % e, "블로그 작성기", 0x30)


def check_update():
    try:
        req = urllib.request.Request(RAW + "version.json", headers={"Cache-Control": "no-cache"})
        remote = json.loads(urllib.request.urlopen(req, timeout=6).read().decode("utf-8"))
        rv = remote.get("version", "0")
    except Exception:
        return                       # 인터넷/저장소 없으면 조용히 그냥 실행
    if _vt(rv) <= _vt(local_version()):
        return
    if _box("새 버전 %s 이(가) 있습니다. (현재 %s)\n\n지금 업데이트할까요?" % (rv, local_version()),
            "블로그 작성기 업데이트", 0x44) != 6:    # MB_YESNO|INFO, 6=예
        return
    try:
        zurl = remote.get("zip") or (RAW + "update.zip")
        data = urllib.request.urlopen(zurl, timeout=180).read()
        _extract(data, skip_preserve=True)
        json.dump({"version": rv}, open(os.path.join(HERE, "version.json"), "w", encoding="utf-8"), ensure_ascii=False)
        _box("업데이트 완료! (버전 %s)" % rv, "블로그 작성기", 0x40)
    except Exception as e:
        _box("업데이트 실패: %s\n기존 버전으로 실행합니다." % (str(e)[:150]), "블로그 작성기", 0x30)


def run_app():
    sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location("blogapp", os.path.join(HERE, APP))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.main()


if __name__ == "__main__":
    ensure_files()
    check_update()
    run_app()
