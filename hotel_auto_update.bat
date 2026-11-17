@echo off
cd /d "%~dp0"
echo ホテル情報を自動調査しています...
python "%~dp0hotel_auto_update.py"
echo.
echo 完了。hotel_check_report.md を確認してください。
pause
