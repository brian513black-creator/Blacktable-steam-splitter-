#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir \
  --index-url https://download.pytorch.org/whl/cpu torch==2.8.0 torchaudio==2.8.0
.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
.venv/bin/python -m pip check
