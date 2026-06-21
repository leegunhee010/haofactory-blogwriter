@echo off
chcp 65001 >/dev/null
cd /d "%~dp0"
echo 블로그 작성기 시작...
python "작성기앱.py"
pause
