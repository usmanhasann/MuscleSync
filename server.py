#!/usr/bin/env python3
"""
IronSync Local Server & Offline YouTube Video Downloader.

Usage:
  1) Start app + video downloader server:
       python3 server.py
     Then open http://localhost:8765 in Chrome or Safari.

  2) Or download a YouTube video directly from CLI:
       python3 server.py --download "https://www.youtube.com/watch?v=..." --id incline-db-curl
"""

import argparse
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = ROOT_DIR / "videos"
EXERCISES_JSON = ROOT_DIR / "exercises.json"


def sanitize_id(raw_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", raw_id or "")
    if not cleaned:
        raise ValueError("Invalid exerciseId")
    return cleaned


def find_yt_dlp() -> list[str]:
    yt_bin = shutil.which("yt-dlp")
    if yt_bin and Path(yt_bin).exists():
        return [yt_bin]
    candidates = [
        Path("/opt/homebrew/bin/yt-dlp"),
        Path("/usr/local/bin/yt-dlp"),
        *sorted((Path.home() / "Library" / "Python").glob("*/bin/yt-dlp"), reverse=True),
    ]
    for c in candidates:
        if c.exists():
            return [str(c)]
    return [sys.executable, "-m", "yt_dlp"]


def list_local_videos() -> dict[str, str]:
    VIDEOS_DIR.mkdir(exist_ok=True)
    result = {}
    for p in VIDEOS_DIR.iterdir():
        if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".webm", ".m4v"}:
            result[p.stem] = f"./videos/{p.name}"
    return result


def update_exercises_json_video(exercise_id: str, rel_path: str | None) -> None:
    if not EXERCISES_JSON.exists():
        return
    try:
        data = json.loads(EXERCISES_JSON.read_text(encoding="utf-8"))
        changed = False
        for ex in data.get("exercises", []):
            if ex.get("id") == exercise_id:
                if rel_path:
                    ex["video"] = rel_path
                else:
                    ex.pop("video", None)
                changed = True
                break
        if changed:
            EXERCISES_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass


def download_youtube_video(url: str, exercise_id: str) -> dict:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Please provide a valid http(s) YouTube URL.")

    ex_id = sanitize_id(exercise_id)
    VIDEOS_DIR.mkdir(exist_ok=True)

    # Remove any old video with the same stem first so fresh format replaces cleanly
    for old in VIDEOS_DIR.glob(f"{ex_id}.*"):
        old.unlink(missing_ok=True)

    out_template = str(VIDEOS_DIR / f"{ex_id}.%(ext)s")
    cmd = find_yt_dlp() + [
        "--no-playlist",
        "--no-warnings",
        "-f",
        "bv*[ext=mp4][vcodec^=avc1][height<=720]+ba[ext=m4a]/b[ext=mp4][height<=720]/b[ext=mp4]/best",
        "--merge-output-format",
        "mp4",
        "-o",
        out_template,
        url.strip(),
    ]

    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"

    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "yt-dlp failed").strip()
        if "No module named yt_dlp" in err or "No such file" in err:
            raise RuntimeError("yt-dlp is not installed. Run: brew install yt-dlp")
        raise RuntimeError(err.splitlines()[-1] if err else "Download failed")

    matches = sorted(VIDEOS_DIR.glob(f"{ex_id}.*"))
    if not matches:
        raise RuntimeError("Download finished but no output file was found.")

    rel_path = f"./videos/{matches[0].name}"
    update_exercises_json_video(ex_id, rel_path)
    return {"ok": True, "exerciseId": ex_id, "path": rel_path}


class IronSyncHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_json(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/videos":
            self.send_json(200, {"ok": True, "videos": list_local_videos()})
            return

        # Support Byte-Range requests for smooth MP4 playback/scrubbing in Safari & Chrome
        range_header = self.headers.get("Range")
        path = self.translate_path(self.path)
        if range_header and os.path.isfile(path):
            m = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if m:
                file_size = os.path.getsize(path)
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else file_size - 1
                end = min(end, file_size - 1)
                if start <= end < file_size:
                    length = end - start + 1
                    self.send_response(206)
                    self.send_header("Content-Type", self.guess_type(path))
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.end_headers()
                    with open(path, "rb") as f:
                        f.seek(start)
                        self.wfile.write(f.read(length))
                    return

        super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        if self.path == "/api/download-video":
            try:
                res = download_youtube_video(data.get("url", ""), data.get("exerciseId", ""))
                self.send_json(200, res)
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if self.path == "/api/delete-video":
            try:
                ex_id = sanitize_id(data.get("exerciseId", ""))
                for old in VIDEOS_DIR.glob(f"{ex_id}.*"):
                    old.unlink(missing_ok=True)
                update_exercises_json_video(ex_id, None)
                self.send_json(200, {"ok": True})
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        self.send_json(404, {"ok": False, "error": "Unknown endpoint"})


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="IronSync Local Server & YouTube Video Downloader")
    parser.add_argument("--port", type=int, default=8765, help="Server port (default: 8765)")
    parser.add_argument("--download", help="YouTube URL to download directly via CLI")
    parser.add_argument("--id", help="Exercise ID for --download (e.g. incline-db-curl)")
    args = parser.parse_args()

    if args.download:
        if not args.id:
            print("Error: --id is required with --download", file=sys.stderr)
            sys.exit(1)
        res = download_youtube_video(args.download, args.id)
        print(f"Downloaded: {res['path']}")
        return

    VIDEOS_DIR.mkdir(exist_ok=True)
    with ReusableTCPServer(("0.0.0.0", args.port), IronSyncHandler) as httpd:
        print(f"IronSync server running at http://localhost:{args.port}")
        print(f"Videos folder: {VIDEOS_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")


if __name__ == "__main__":
    main()
