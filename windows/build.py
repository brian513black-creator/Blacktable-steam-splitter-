"""Build the Windows x64 installer with Python, Zig and NSIS."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERSION = "0.1.1"
PYTHON_URL = "https://api.nuget.org/v3-flatcontainer/python/3.13.17/python.3.13.17.nupkg"
FFMPEG_RELEASE = "https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/autobuild-2026-11-26-12-56"
FFMPEG_PACKAGE = "ffmpeg-n8.1.3-41-ga8029b6528-win64-lgpl-shared-8.1"
WHEELS = (
    "https://download-r2.pytorch.org/whl/cpu/torch-2.8.0%2Bcpu-cp313-cp313-win_amd64.whl"
    "#sha256=e1ee1b2346ade3ea90306dfbec7e8ff17bc220d344109d189ae09078333b0856",
    "https://download-r2.pytorch.org/whl/cpu/torchaudio-2.8.0%2Bcpu-cp313-cp313-win_amd64.whl"
    "#sha256=0c2d081e24204768e636cbf05e1377c8a6964b8ed6fa3aa5092ba9af9bbc19c5",
)


def run(*command, **kwargs):
    subprocess.run(command, check=True, **kwargs)


def download(url, target, sha256):
    if not target.exists():
        run("curl", "--fail", "--silent", "--show-error", "--location", "--retry", "2",
            "--output", target, url)
    with target.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != sha256:
        raise ValueError(f"Checksum mismatch for {target}. Remove it to download it again.")
    return target


def extract(archive, prefix, target, keep):
    with ZipFile(archive) as source:
        for name in source.namelist():
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = Path(name.removeprefix(prefix))
            if relative.is_absolute() or relative.anchor or ".." in relative.parts:
                raise ValueError(f"Unexpected archive path {name}")
            if keep(relative):
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                with source.open(name) as contents, output.open("wb") as destination:
                    shutil.copyfileobj(contents, destination)


def main():
    dist = ROOT / "dist"
    cache = Path(os.environ.get("BLACKTABLE_BUILD_CACHE", dist / "downloads")).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    python_zip = download(PYTHON_URL, cache / "python-3.13.17.zip",
                          "dce409744b088f94c6e37ba41f8100c384c27e029e843237364c602d30d475e5")
    ffmpeg_zip = download(f"{FFMPEG_RELEASE}/{FFMPEG_PACKAGE}.zip", cache / "ffmpeg.zip",
                          "372016b1248544b4ffc290ae41c9c57e6441bd0da32068ea18032a25b7b36e08")
    pip = (sys.executable, "-m", "pip", "--disable-pip-version-check", "--no-cache-dir")
    wheel_dir = cache / "wheels"
    run(*pip, "wheel", "--no-deps", "--wheel-dir", wheel_dir, "demucs==4.0.1")

    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="blacktable-build-", dir=dist) as temporary:
        payload = Path(temporary) / "payload"
        runtime = payload / "runtime"
        extract(python_zip, "tools/", runtime,
                lambda path: path.parts[0] not in ("include", "libs", "Scripts")
                and "site-packages" not in path.parts and path.name != "pythonw.exe")
        extract(ffmpeg_zip, f"{FFMPEG_PACKAGE}/", payload / "ffmpeg",
                lambda path: path.name == "LICENSE.txt"
                or (path.parts[0] == "bin" and path.name != "ffplay.exe"))
        run(*pip, "install", "--platform", "win_amd64", "--python-version", "3.13",
            "--only-binary", ":all:", "--no-deps", "--no-compile",
            "--target", runtime / "Lib" / "site-packages", "--find-links", wheel_dir,
            "-r", HERE / "requirements.lock", *WHEELS)
        # The Windows torch wheel also contains several GB of link-time files for developers.
        for library in (runtime / "Lib" / "site-packages" / "torch" / "lib").glob("*.lib"):
            library.unlink()
        shutil.copy2(ROOT / "app.py", payload)
        shutil.copytree(ROOT / "web", payload / "web")
        shutil.copy2(HERE / "Third-party notices.txt", payload)
        resource = Path(temporary) / "launcher.res"
        run(sys.executable, "-m", "ziglang", "rc", "/x", "/fo", resource, "launcher.rc", cwd=HERE)
        run(sys.executable, "-m", "ziglang", "cc", "-target", "x86_64-windows-gnu",
            "-municode", "-Wl,--subsystem,windows", "-Oz", "-s", "launcher.c", resource, "-luser32",
            "-o", payload / "Blacktable Studio.exe", cwd=HERE)
        if not re.fullmatch(r"\d+\.\d+\.\d+", VERSION):
            raise ValueError("Installer version must contain three numbers.")
        makensis = os.environ.get("MAKENSIS", "makensis")
        output = dist / f"Blacktable-Studio-{VERSION}-Windows-x64-Setup.exe"
        define = "/D" if os.name == "nt" else "-D"
        run(makensis, f"{define}OUTPUT={output}", f"{define}PAYLOAD={payload}",
            f"{define}VERSION={VERSION}", "installer.nsi", cwd=HERE)
    with output.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    output.with_suffix(".exe.sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(output)


if __name__ == "__main__":
    main()
