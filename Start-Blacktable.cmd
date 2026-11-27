@echo off
setlocal
title Blacktable Studio by Brian
cd /d "%~dp0"
where ffmpeg.exe >nul 2>&1 || goto ffmpeg_missing
where ffprobe.exe >nul 2>&1 || goto ffmpeg_missing

if exist ".venv\Scripts\python.exe" goto check_deps
py -3.12 -m venv .venv || goto python_missing

:check_deps
".venv\Scripts\python.exe" -c "from importlib.metadata import version; assert version('tensorflow-cpu') == '2.20.0'; assert version('numpy') == '2.5.5'" >nul 2>&1
if not errorlevel 1 goto start_app
echo Installing Blacktable audio components. This can take a few minutes.
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt || goto failed
".venv\Scripts\python.exe" -m pip check || goto failed

:start_app
".venv\Scripts\python.exe" spleeter_engine.py prepare .models\spleeter-4stems .models\downloads || goto failed
".venv\Scripts\python.exe" app.py --open --port 0
if errorlevel 1 goto failed
exit /b 0

:ffmpeg_missing
echo Install FFmpeg and ffprobe, then open a new window and try again.
echo Windows Package Manager: winget install --id Gyan.FFmpeg --exact
goto failed

:python_missing
echo Install 64-bit Python 3.12 with the Windows Python launcher enabled.
goto failed

:failed
echo Blacktable could not start. Review the message above.
pause
exit /b 1
