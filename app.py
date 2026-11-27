"""Blacktable Studio by Brian, a local audio workstation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from threading import Lock, Thread
import traceback
from urllib.parse import unquote, urlsplit
from uuid import uuid4
import wave
import webbrowser
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "spleeter_engine.py"
MAX_BYTES = 250 * 1024 * 1024
MAX_JOBS = 100
STEMS = {
    "quick": {"center.wav", "sides.wav"},
    "four": {"vocals.wav", "drums.wav", "bass.wav", "other.wav"},
    "two": {"vocals.wav", "no_vocals.wav"},
}
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
CHECK_LOG = "Check the Blacktable log or launcher console for details."
DESKTOP_MUTEX = r"Local\BlacktableStudioWorkstation"
ERROR_ALREADY_EXISTS = 183


class StudioServer(ThreadingHTTPServer):
    closing = False

    def handle_error(self, request, client_address):
        if not isinstance(sys.exception(), (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            super().handle_error(request, client_address)


def run(*args, failure_message=None):
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(args, capture_output=True, text=True, errors="replace",
                            timeout=3600, creationflags=flags)
    if result.returncode:
        print(result.stderr[-4000:], file=sys.stderr)
        if args[:2] == (sys.executable, str(ENGINE)):
            if "checkpoint is missing or damaged" in result.stderr:
                raise RuntimeError("The Spleeter model is missing or damaged. Run Blacktable setup again.")
            if sys.platform == "win32" and any(
                marker in result.stderr for marker in ("DLL load failed", "WinError 126")
            ):
                raise RuntimeError("The AI engine could not load a Windows library. Install Microsoft's "
                                   "latest Visual C++ Redistributable (x64) and retry.")
        raise RuntimeError(failure_message or f"Processing failed. {CHECK_LOG}")


def process(job, folder, source):
    with LOCK:
        job["status"] = "running"
    try:
        mix = folder / "mix.wav"
        limit = ("-t", "30") if job["preview"] else ()
        run("ffmpeg", "-nostdin", "-v", "error", "-xerror", "-protocol_whitelist", "file",
            "-format_whitelist", AUDIO_FORMATS, "-i", str(source), "-map", "0:a:0",
            *limit, "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(mix),
            failure_message="Could not decode the audio. Try a complete copy in a supported format.")
        try:
            with wave.open(str(mix), "rb") as audio:
                if not audio.getnframes():
                    raise RuntimeError("This file contains no audio samples.")
        except (wave.Error, EOFError) as error:
            raise RuntimeError("The decoded audio could not be read.") from error
        if job["mode"] == "quick":
            channels = {
                "center": "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1",
                "sides": "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c1-0.5*c0",
            }
            for name, audio_filter in channels.items():
                run("ffmpeg", "-nostdin", "-v", "error", "-i", str(mix),
                    "-af", audio_filter, str(folder / f"{name}.wav"))
        else:
            model = ROOT / "model"
            if not model.is_dir():
                model = ROOT / ".models" / "spleeter-4stems"
            run(sys.executable, str(ENGINE), "split", str(model), str(mix), str(folder), job["mode"])
        stems = sorted(file.name for file in folder.glob("*.wav") if file != mix)
        if set(stems) != STEMS[job["mode"]]:
            raise RuntimeError("The separator returned an incomplete set of stems.")
        with ZipFile(folder / "stems.zip", "w") as archive:
            for stem in stems:
                archive.write(folder / stem, stem)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        shutil.rmtree(folder, ignore_errors=True)
        with LOCK:
            job.update(status="failed", error=str(error) if isinstance(error, RuntimeError)
                       else f"Could not finish processing. {CHECK_LOG}")
        if not isinstance(error, RuntimeError):
            print(error, file=sys.stderr)
    else:
        for temporary in (source, mix):
            try:
                temporary.unlink(missing_ok=True)
            except OSError as error:
                print(error, file=sys.stderr)
        with LOCK:
            job.update(status="done", stems=stems)


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
                except FileNotFoundError:
                    self.send_error(404)
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
        if not 0 < size <= MAX_BYTES or mode not in STEMS:
            self.send_json({"error": "Choose an audio file up to 250 MB and a split mode."}, 400)
            return
        job_id = self.headers.get("X-Job-Id")
        if job_id is None:
            job_id = uuid4().hex
        elif not re.fullmatch(r"[a-f0-9]{32}", job_id):
            self.send_json({"error": "Invalid upload identifier."}, 400)
            return
        name = unquote(self.headers.get("X-File-Name", "Audio"))[:180]
        job = dict(id=job_id, name=name, mode=mode, size=size, status="uploading",
                   preview=self.headers.get("X-Preview") == "1")
        rejection = None
        with LOCK:
            existing = JOBS.get(job_id)
            if self.server.closing:
                rejection = (503, "Blacktable is closing. Open it again to start a new split.")
            elif existing is None and len(JOBS) >= MAX_JOBS:
                rejection = (429, "Session limit reached. Save your files and restart Blacktable.")
            elif existing is None:
                JOBS[job_id] = job
        if rejection is not None or existing is not None:
            # Browsers can lose the response when the connection closes with unread request bytes.
            try:
                for _ in self.upload_chunks(size):
                    pass
            except OSError:
                self.send_json({"error": "The upload was interrupted."}, 400)
                return
            if rejection is not None:
                status, message = rejection
                self.send_json({"error": message}, status)
            else:
                self.reply_to_replay(job)
            return
        folder = self.server.storage / job_id
        source = folder / "upload"
        try:
            folder.mkdir()
            with source.open("wb") as stream:
                for block in self.upload_chunks(size):
                    stream.write(block)
        except OSError:
            self.discard_upload(job_id, folder)
            self.send_json({"error": "The upload could not be saved."}, 400)
            return
        try:
            with LOCK:
                self.server.worker.submit(process, job, folder, source)
                job["status"] = "queued"
        except RuntimeError:
            self.discard_upload(job_id, folder)
            self.send_json({"error": "Blacktable is closing. Open it again to start a new split."}, 503)
            return
        self.send_json({"id": job_id}, 202)

    def upload_chunks(self, remaining):
        self.connection.settimeout(60)
        while remaining:
            block = self.rfile.read(min(remaining, 1024 * 1024))
            if not block:
                raise OSError("Upload interrupted")
            remaining -= len(block)
            yield block

    def reply_to_replay(self, job):
        with LOCK:
            existing = JOBS.get(job["id"])
            if existing is None or existing["status"] == "uploading":
                payload = {"error": "The original upload is pending or was interrupted. Check the queue before retrying."}
                status = 409
            elif any(existing[key] != job[key] for key in ("name", "mode", "size", "preview")):
                payload = {"error": "That upload identifier is already in use."}
                status = 409
            else:
                payload = {"id": job["id"]}
                status = 202
        self.send_json(payload, status)

    def discard_upload(self, job_id, folder):
        shutil.rmtree(folder, ignore_errors=True)
        with LOCK:
            JOBS.pop(job_id, None)


def serve(args):
    bundled_ffmpeg = ROOT / "ffmpeg" / "bin"
    if bundled_ffmpeg.is_dir():
        os.environ["PATH"] = str(bundled_ffmpeg) + os.pathsep + os.environ.get("PATH", "")
    if not all(shutil.which(tool) for tool in ("ffmpeg", "ffprobe")):
        raise RuntimeError("FFmpeg and ffprobe are required and must be on PATH.")
    with tempfile.TemporaryDirectory(prefix="blacktable-", ignore_cleanup_errors=True) as storage:
        with ThreadPoolExecutor(max_workers=1) as worker:
            with StudioServer(("127.0.0.1", args.port), Handler) as server:
                server.storage = Path(storage)
                server.worker = worker
                url = f"http://127.0.0.1:{server.server_port}"
                print(f"Blacktable Studio by Brian is running at {url}", flush=True)
                if args.desktop:
                    thread = Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    try:
                        if not webbrowser.open(url):
                            message_box(f"Open this address in your browser:\n\n{url}")
                        wait_for_desktop_close(server)
                    finally:
                        server.shutdown()
                        thread.join()
                        worker.shutdown(cancel_futures=True)
                    return
                if args.open:
                    webbrowser.open(url)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    worker.shutdown(cancel_futures=True)


def wait_for_desktop_close(server):
    prompt = "Blacktable is running in your browser.\n\nSave your stems, then click OK to close Blacktable."
    while True:
        message_box(prompt)
        with LOCK:
            if all(job["status"] in {"done", "failed"} for job in JOBS.values()):
                server.closing = True
                return
        prompt = ("Blacktable is still uploading or splitting audio.\n\n"
                  "Wait for the jobs to finish, save your stems, then click OK to close Blacktable.")


def message_box(text, flags=0x40):
    from ctypes import windll

    windll.user32.MessageBoxW(None, text, "Blacktable Studio by Brian", flags)


@contextmanager
def desktop_lock():
    from ctypes import WinDLL, WinError, get_last_error, set_last_error, wintypes

    kernel32 = WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    create_mutex.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    set_last_error(0)
    handle = create_mutex(None, False, DESKTOP_MUTEX)
    error = get_last_error()
    if not handle:
        raise WinError(error)
    try:
        yield error != ERROR_ALREADY_EXISTS
    finally:
        close_handle(handle)


def run_desktop(args):
    with desktop_lock() as available:
        if not available:
            message_box("Blacktable is already open, or setup is in progress. "
                        "Return to the original browser tab or wait for setup to finish.")
            return
        data = Path(os.environ["LOCALAPPDATA"]) / "Blacktable Studio"
        data.mkdir(parents=True, exist_ok=True)
        with (data / "blacktable.log").open("w", encoding="utf-8", buffering=1) as log:
            stdout, stderr = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = log
            try:
                serve(args)
            except Exception:
                traceback.print_exc()
                raise
            finally:
                sys.stdout, sys.stderr = stdout, stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the workstation in your browser.")
    parser.add_argument("--desktop", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.desktop:
        serve(args)
        return 0
    if sys.platform != "win32":
        parser.error("Desktop mode requires Windows.")

    try:
        run_desktop(args)
    except Exception:
        message_box("Blacktable could not start. Check blacktable.log in "
                    "%LOCALAPPDATA%\\Blacktable Studio for details.", flags=0x10)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
