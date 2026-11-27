@echo off
setlocal
title Blacktable Studio by Brian
cd /d "%~dp0"
where ffmpeg.exe >nul 2>&1 || goto ffmpeg_missing
where ffprobe.exe >nul 2>&1 || goto ffmpeg_missing

if exist ".venv\Scripts\python.exe" goto check_deps
py -3.12 -m venv .venv || goto python_missing

:check_deps
".venv\Scripts\python.exe" -c "from importlib.metadata import version; assert version('torch').split('+')[0] == '2.8.0'; assert version('torchaudio').split('+')[0] == '2.8.0'; assert version('demucs') == '4.0.1'; assert version('soundfile') == '0.13.1'" >nul 2>&1
if not errorlevel 1 goto start_app
echo Installing Blacktable audio components. This can take a few minutes.
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --index-url https://download.pytorch.org/whl/cpu torch==2.8.0 torchaudio==2.8.0 || goto failed
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt || goto failed
".venv\Scripts\python.exe" -m pip check || goto failed

:start_app
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
