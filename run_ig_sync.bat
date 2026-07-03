@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d C:\dev\SNS
if not exist output mkdir output
python scripts\ig_bq_sync.py >> output\ig_sync.log 2>&1
