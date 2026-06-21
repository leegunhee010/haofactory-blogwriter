# -*- coding: utf-8 -*-
"""
배포 패키지 빌더 (owner 전용)
=================================
사용법:
  python release.py            → 패치(0.0.1) 올리고 update.zip 만듦
  python release.py 1.3.0      → 버전 직접 지정
  python release.py --bundle   → 버전 안 올리고 app_bundle.zip 만 갱신(exe 빌드 직전)

만드는 것:
  - app_bundle.zip   : exe 안에 넣을 '최초 설치용' 번들 (BlogWriter.spec 이 참조)
  - dist_update/update.zip + version.json : GitHub repo(main)에 올릴 업데이트 파일

배포 흐름:
  1) python release.py 1.1.0           (버전 올리고 zip 생성)
  2) version.json + dist_update/update.zip 을 GitHub repo(leegunhee010/haofactory-blogwriter)에 push
  3) 팀원이 프로그램 켜면 → 새 버전 감지 → 업데이트 팝업 → 자동 패치
"""
import os, sys, json, zipfile
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
# 배포 패키지에 포함할 것 (사용자 데이터·캐시·빌드산출물 제외)
INCLUDE_FILES = ["작성기앱.py", "cardnews_pil.py", "brands.py", "version.json"]
INCLUDE_DIRS = ["brands", "assets"]          # 브랜드 설정·카드 템플릿·폰트
SKIP_EXT = (".pyc",)
SKIP_NAMES = {"__pycache__", "cards.json"}    # cards.json은 생성물(브랜드 cards 폴더엔 없음)


def _add_dir(z, d):
    base = os.path.join(HERE, d)
    if not os.path.isdir(base):
        return
    for root, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if x not in SKIP_NAMES]
        for f in files:
            if f.endswith(SKIP_EXT) or f in SKIP_NAMES:
                continue
            full = os.path.join(root, f)
            arc = os.path.relpath(full, HERE).replace(os.sep, "/")
            z.write(full, arc)


def build_zip(path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in INCLUDE_FILES:
            if os.path.exists(os.path.join(HERE, f)):
                z.write(os.path.join(HERE, f), f)
        for d in INCLUDE_DIRS:
            _add_dir(z, d)


def bump(v, part="patch"):
    a = (list(_v(v)) + [0, 0, 0])[:3]
    a[2 if part == "patch" else 1 if part == "minor" else 0] += 1
    return ".".join(map(str, a))


def _v(s):
    try:
        return tuple(int(x) for x in str(s).split("."))
    except Exception:
        return (1, 0, 0)


def main():
    args = sys.argv[1:]
    bundle_only = "--bundle" in args
    args = [a for a in args if not a.startswith("--")]
    vfile = os.path.join(HERE, "version.json")
    cur = json.load(open(vfile, encoding="utf-8")).get("version", "1.0.0") if os.path.exists(vfile) else "1.0.0"

    if bundle_only:
        build_zip(os.path.join(HERE, "app_bundle.zip"))
        print("app_bundle.zip 생성 완료 (현재 버전 %s) — 이제 PyInstaller 빌드하세요." % cur)
        return

    newv = args[0] if args else bump(cur, "patch")
    json.dump({"version": newv}, open(vfile, "w", encoding="utf-8"), ensure_ascii=False)
    os.makedirs(os.path.join(HERE, "dist_update"), exist_ok=True)
    build_zip(os.path.join(HERE, "app_bundle.zip"))                  # exe 재빌드용
    build_zip(os.path.join(HERE, "dist_update", "update.zip"))       # GitHub 업로드용
    print("=" * 56)
    print("버전 %s → %s" % (cur, newv))
    print("생성: app_bundle.zip, dist_update/update.zip, version.json")
    print("다음: version.json 과 dist_update/update.zip 을")
    print("      GitHub repo(%s) main 브랜치에 push" % "leegunhee010/haofactory-blogwriter")
    print("=" * 56)


if __name__ == "__main__":
    main()
