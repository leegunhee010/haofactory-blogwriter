# 블로그 작성기 — 배포 & 자동 업데이트 가이드

exe 는 **파이썬·Flask·PIL·docx·pptx 런타임을 품은 껍데기**이고,
실제 로직·브랜드·카드 디자인(`작성기앱.py`·`cardnews_pil.py`·`brands.py`·`brands/`·`assets/`)은
exe 옆에 풀려서 **GitHub로 갱신**됩니다. 그래서 업데이트 시 큰 exe 재다운로드 없이 작은 zip만 받습니다.

구성: `launcher.py`(진입점) · `version.json`(버전) · `release.py`(배포 빌더) · `BlogWriter.spec`(PyInstaller)

---

## 0. 최초 1회 — GitHub 저장소 만들기
1. GitHub에 저장소 생성: **`leegunhee010/haofactory-blogwriter`** (공개)
   - 다른 이름으로 할 거면 `launcher.py` 와 `release.py` 의 `REPO` 값을 같이 바꾸세요.
2. 저장소에 `version.json` 1개만 먼저 올려둠 (`{"version":"1.0.0"}`).

## 1. 최초 빌드 — exe 만들기 (owner PC)
```
pip install pyinstaller
python release.py --bundle        # app_bundle.zip 생성(최초 설치용 번들)
pyinstaller BlogWriter.spec       # dist/BlogWriter/ 폴더 생성
```
→ 결과: `dist/BlogWriter/블로그작성기.exe` (+ 옆 런타임 파일들)
→ `dist/BlogWriter` 폴더 통째로 압축해서 팀원에게 전달 (또는 설치 위치에 복사).

## 2. 팀원 사용
- `블로그작성기.exe` 실행 → 최초 실행 시 앱 파일이 자동으로 풀림 → 브라우저로 열림
- 각자 **자기 Claude 구독으로 로그인**(앱 안 🔑 버튼) — API 종량제 아님
- 켤 때마다 새 버전 있으면 **"업데이트?" 팝업** → 예 → 자동 패치 후 실행

## 3. 업데이트 배포 (owner) — 코드·브랜드·카드 디자인 바꿨을 때
```
python release.py 1.1.0           # 버전 지정 (생략하면 patch 자동 +1)
```
→ `version.json` 갱신 + `dist_update/update.zip` 생성.
그 다음 **GitHub repo(main)에 2개 파일 push**:
- `version.json`
- `dist_update/update.zip`  → 저장소 루트에 `update.zip` 으로 올림

git으로 한 번에:
```
git add version.json && cp dist_update/update.zip update.zip && git add update.zip
git commit -m "v1.1.0" && git push
```
→ 팀원이 다음 실행 때 자동 업데이트 됩니다. (exe 재배포 불필요!)

> exe 자체(런타임)를 바꿀 일(파이썬 버전·새 라이브러리 추가)이 아니면 **1번은 다시 안 해도 됨.**
> 평소 업데이트는 **3번만** 반복하면 끝.

---

## 보존되는 사용자 데이터 (업데이트해도 안 지워짐)
- `출력/` — 생성한 원고·카드
- `작성기_설정.json` — 로컬 설정(모델 등)

## 참고 — 통검 글감추천(📝 추천)
브랜드 설정의 `tonggeom` 경로는 owner PC 기준이라, 팀원 PC엔 그 폴더가 없으면 추천이 비어 나옵니다
(키워드 직접 입력은 정상). 팀원도 추천을 쓰려면: 통검체크 프로그램을 같이 깔고 브랜드 `tonggeom` 경로를
각자 PC 기준으로 맞추거나, 통검 데이터를 공유 위치(예: Supabase/공유폴더)로 두는 방식이 필요합니다. (추후 과제)
