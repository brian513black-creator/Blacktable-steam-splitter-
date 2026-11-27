"""Blacktable Studio by Brian, a local audio workstation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from threading import Lock
from urllib.parse import unquote, urlsplit
from uuid import uuid4
import webbrowser
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 250 * 1024 * 1024
MAX_JOBS = 100
MODES = {"quick", "four", "two"}
AUDIO_FORMATS = "aac,ac3,aiff,ape,asf,flac,matroska,mov,mp3,ogg,w64,wav,webm"
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/blacktable-icon.png": ("blacktable-icon.png", "image/png"),
    "/instrument-serif.ttf": ("instrument-serif.ttf", "font/ttf"),
    "/gold-wave.webp": ("gold-wave.webp", "image/webp"),
}
JOBS = {}
LOCK = Lock()


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=3600)
    if result.returncode:
        print(result.stderr[-4000:], file=sys.stderr)
        if args[:3] == (sys.executable, "-m", "demucs") and "Downloading:" in result.stdout:
            if "URLError" in result.stderr or "HTTPError" in result.stderr:
                raise RuntimeError("The AI model could not download. Check your connection "
                                   "to dl.fbaipublicfiles.com and try again.")
        raise RuntimeError("Processing failed. Check the launcher console for details.")


def process(job, folder, source):
    with LOCK:
        job["status"] = "running"
    try:
        mix = folder / "mix.wav"
        limit = ("-t", "30") if job["preview"] else ()
        run("ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file",
            "-format_whitelist", AUDIO_FORMATS, "-i", str(source), "-map", "0:a:0",
            *limit, "-ar", "44100", "-ac", "2", str(mix))
        if job["mode"] == "quick":
            channels = {
                "center": "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1",
                "sides": "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c1-0.5*c0",
            }
            for name, audio_filter in channels.items():
                run("ffmpeg", "-nostdin", "-v", "error", "-i", str(mix),
                    "-af", audio_filter, str(folder / f"{name}.wav"))
        else:
            two = ("--two-stems", "vocals") if job["mode"] == "two" else ()
            run(sys.executable, "-m", "demucs", "-n", "htdemucs", "-d", "cpu",
                "--shifts", "0", "--out", str(folder), *two, str(mix))
            for stem in (folder / "htdemucs" / "mix").glob("*.wav"):
                stem.replace(folder / stem.name)
        stems = sorted(file.name for file in folder.glob("*.wav") if file != mix)
        if len(stems) != (4 if job["mode"] == "four" else 2):
            raise RuntimeError("The separator returned an incomplete set of stems.")
        with ZipFile(folder / "stems.zip", "w") as archive:
            for stem in stems:
                archive.write(folder / stem, stem)
        with LOCK:
            job.update(status="done", stems=stems)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        with LOCK:
            job.update(status="failed", error=str(error) if isinstance(error, RuntimeError)
                       else "Could not finish processing. Check the launcher console.")
        if not isinstance(error, RuntimeError):
            print(error, file=sys.stderr)
    finally:
        source.unlink(missing_ok=True)
        (folder / "mix.wav").unlink(missing_ok=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def trusted(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.send_error(403)
            return False
        return True

    def send_data(self, data, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, data, status=200):
        self.send_data(json.dumps(data).encode(), "application/json", status)

    def send_file(self, file):
        with file.open("rb") as stream:
            size = os.fstat(stream.fileno()).st_size
            start, end = 0, size - 1
            byte_range = self.headers.get("Range")
            if byte_range:
                match = re.fullmatch(r"bytes=(\d{0,15})-(\d{0,15})", byte_range)
                if match and any(match.groups()):
                    first, last = match.groups()
                    start = int(first) if first else max(0, size - int(last))
                    end = min(int(last), end) if first and last else end
                if not match or not any(match.groups()) or not 0 <= start <= end < size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
            self.send_response(206 if byte_range else 200)
            self.send_header("Accept-Ranges", "bytes")
            if byte_range:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Type", "audio/wav" if file.suffix == ".wav"
                             else "application/zip")
            self.send_header("X-Content-Type-Options", "nosniff")
            remaining = end - start + 1
            self.send_header("Content-Length", str(remaining))
            self.end_headers()
            stream.seek(start)
            while remaining:
                block = stream.read(min(remaining, 1024 * 1024))
                if not block:
                    break
                self.wfile.write(block)
                remaining -= len(block)

    def do_GET(self):
        if not self.trusted():
            return
        path = urlsplit(self.path).path
        if path in ASSETS:
            filename, content_type = ASSETS[path]
            self.send_data((ROOT / "web" / filename).read_bytes(), content_type)
            return
        if path == "/api/jobs":
            with LOCK:
                jobs = list(reversed([dict(job) for job in JOBS.values()]))
            self.send_json(jobs)
            return
        match = re.fullmatch(r"/files/([a-f0-9]{32})/([a-z_]+\.(?:wav|zip))", path)
        if match:
            job_id, filename = match.groups()
            with LOCK:
                job = JOBS.get(job_id, {})
                allowed = job.get("status") == "done" and (
                    filename in job["stems"] or filename == "stems.zip")
            if allowed:
                file = self.server.storage / job_id / filename
                try:
                    self.send_file(file)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
        self.send_error(404)

    def do_POST(self):
        if not self.trusted():
            return
        if self.path != "/api/jobs" or self.headers.get("X-Blacktable") != "upload":
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        mode = self.headers.get("X-Split-Mode")
        if not 0 < size <= MAX_BYTES or mode not in MODES:
            self.send_json({"error": "Choose an audio file up to 250 MB and a split mode."}, 400)
            return
        job_id = uuid4().hex
        name = unquote(self.headers.get("X-File-Name", "Audio"))[:180]
        job = dict(id=job_id, name=name, mode=mode, status="uploading",
                   preview=self.headers.get("X-Preview") == "1")
        with LOCK:
            if len(JOBS) >= MAX_JOBS:
                self.send_json({"error": "Session limit reached. Save your files and restart Blacktable."}, 429)
                return
            JOBS[job_id] = job
        folder = self.server.storage / job_id
        source = folder / "upload"
        try:
            folder.mkdir()
            with source.open("wb") as stream:
                remaining = size
                self.connection.settimeout(60)
                while remaining:
                    block = self.rfile.read(min(remaining, 1024 * 1024))
                    if not block:
                        raise OSError("Upload interrupted")
                    stream.write(block)
                    remaining -= len(block)
        except OSError:
            shutil.rmtree(folder, ignore_errors=True)
            with LOCK:
                JOBS.pop(job_id, None)
            self.send_json({"error": "The upload could not be saved."}, 400)
            return
        with LOCK:
            job["status"] = "queued"
        self.server.worker.submit(process, job, folder, source)
        self.send_json({"id": job_id}, 202)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the workstation in your browser.")
    args = parser.parse_args()
    if not all(shutil.which(tool) for tool in ("ffmpeg", "ffprobe")):
        parser.error("FFmpeg and ffprobe are required and must be on PATH.")
    os.environ.setdefault("TORCH_HOME", str(ROOT / ".models"))
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    with tempfile.TemporaryDirectory(prefix="blacktable-") as storage:
        with ThreadPoolExecutor(max_workers=1) as worker:
            with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
                server.storage = Path(storage)
                server.worker = worker
                url = f"http://127.0.0.1:{server.server_port}"
                print(f"Blacktable Studio by Brian is running at {url}", flush=True)
                if args.open:
                    webbrowser.open(url)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    worker.shutdown(cancel_futures=True)


if __name__ == "__main__":
    main()
