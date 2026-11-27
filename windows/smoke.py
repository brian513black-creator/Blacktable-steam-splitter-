"""Smoke-test a packaged Windows install, or an existing local server."""
import argparse
import io
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import time
from urllib.request import Request, urlopen
import wave
from zipfile import ZipFile


def request(url, **kwargs):
    with urlopen(Request(url, **kwargs), timeout=10) as response:
        return response.read()


def wait_for(check, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(.5)
    raise TimeoutError(f"Timed out after {timeout} seconds.")


def wav_fixture(seconds):
    sample = io.BytesIO()
    tone = b"".join(struct.pack("<hh", int(10000 * math.sin(i / 20)),
                                int(7000 * math.sin(i / 32))) for i in range(44100))
    with wave.open(sample, "wb") as wav:
        wav.setparams((2, 2, 44100, 0, "NONE", "not compressed"))
        for _ in range(seconds):
            wav.writeframesraw(tone)
        wav.writeframes(b"")
    return sample.getvalue()


def split(url, sample, mode, preview=False):
    headers = {"X-Blacktable": "upload", "X-Split-Mode": mode, "X-File-Name": "Test%20track.wav"}
    if preview:
        headers["X-Preview"] = "1"
    submitted = json.loads(request(f"{url}/api/jobs", data=sample, headers=headers))

    def completed():
        for job in json.loads(request(f"{url}/api/jobs")):
            if job["id"] == submitted["id"] and job["status"] in {"done", "failed"}:
                return job
        return None

    return wait_for(completed, 600)


def test_audio(url, modes):
    assert b"Blacktable Studio by Brian" in request(url)
    empty = split(url, wav_fixture(0), "quick")
    assert empty["status"] == "failed" and "no audio samples" in empty["error"], empty
    print("Empty audio correctly rejected", flush=True)

    duration = 180
    sample = wav_fixture(duration)
    for mode, preview in [(mode, False) for mode in modes] + [("quick", True)]:
        stems = {
            "quick": {"center.wav", "sides.wav"},
            "four": {"vocals.wav", "drums.wav", "bass.wav", "other.wav"},
            "two": {"vocals.wav", "no_vocals.wav"},
        }[mode]
        result = split(url, sample, mode, preview)
        assert result["status"] == "done", result
        assert result["preview"] == preview, result
        assert set(result["stems"]) == stems, result
        seconds = 30 if preview else duration
        archive = request(f"{url}/files/{result['id']}/stems.zip")
        with ZipFile(io.BytesIO(archive)) as zipped:
            assert set(zipped.namelist()) == stems
            for stem in stems:
                with wave.open(io.BytesIO(zipped.read(stem)), "rb") as wav:
                    assert (wav.getnchannels(), wav.getframerate(), wav.getnframes()) == (2, 44100, 44100 * seconds)
        print(f"{mode} passed with {seconds}-second stems", flush=True)


def test_installer(installer, modes):
    local = Path(os.environ["LOCALAPPDATA"])
    installed = local / "Programs" / "Blacktable Studio"
    log = local / "Blacktable Studio" / "blacktable.log"
    if installed.exists() or log.exists():
        raise RuntimeError("Run the installer smoke test on a clean Windows test account.")
    subprocess.run([installer.resolve(), "/S"], check=True, timeout=240)
    launcher = subprocess.Popen([installed / "Blacktable Studio.exe"], cwd=installed)
    try:
        def ready():
            if launcher.poll() is not None:
                raise RuntimeError(f"Launcher exited with code {launcher.returncode}")
            if log.exists():
                match = re.search(r"http://127\.0\.0\.1:\d+", log.read_text(encoding="utf-8"))
                if match:
                    return match.group()
            return None

        test_audio(wait_for(ready, 45), modes)
    finally:
        if launcher.poll() is None:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(launcher.pid)], timeout=20)
            launcher.wait(timeout=20)
        if log.exists():
            print(log.read_text(encoding="utf-8"), flush=True)
        subprocess.run([installed / "Uninstall.exe", "/S"], check=True, timeout=180)
        wait_for(lambda: not (installed / "Blacktable Studio.exe").exists(), 60)
    print("Installer, launcher, audio exports and uninstaller passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--installer", type=Path)
    target.add_argument("--url")
    parser.add_argument("--ai", action="store_true", help="Run both AI modes using the official model.")
    args = parser.parse_args()
    modes = ("quick", "four", "two") if args.ai else ("quick",)
    if args.installer:
        test_installer(args.installer, modes)
    else:
        test_audio(args.url, modes)


if __name__ == "__main__":
    main()
