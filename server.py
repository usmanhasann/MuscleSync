#!/usr/bin/env python3
from __future__ import annotations

"""
IronSync Local Server & Offline YouTube Video Downloader.

Usage:
  1) Start app + video downloader server:
       python3 server.py
     Then open http://localhost:8765 in Chrome or Safari.

  2) Or download a YouTube video directly from CLI:
       python3 server.py --download "https://www.youtube.com/watch?v=..." --id incline-db-curl

  3) Repair videos that freeze on iPhone (picture stops, timer keeps running):
       python3 server.py --fix-videos
"""

import argparse
import base64
import time
import http.server
import json
import os
import re
import shutil
import socketserver
import struct
import subprocess
import sys
import tempfile
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
    # No yt-dlp binary: use whichever Python on this Mac has the yt_dlp module
    # (the server may be running on Apple's Python 3.9, which usually doesn't).
    pythons = [sys.executable, "/usr/local/bin/python3", "/opt/homebrew/bin/python3",
               *sorted(map(str, Path("/Library/Frameworks/Python.framework/Versions").glob("*/bin/python3")), reverse=True)]
    for py in dict.fromkeys(pythons):
        if Path(py).exists():
            try:
                if subprocess.run([py, "-c", "import yt_dlp"], capture_output=True, timeout=20).returncode == 0:
                    return [py, "-m", "yt_dlp"]
            except Exception:
                pass
    return [sys.executable, "-m", "yt_dlp"]


VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}


# Several videos per exercise: <id>.mp4, <id>--2.mp4, <id>--3.mp4 ...
def _video_owner(p: Path) -> str | None:
    if not p.is_file() or p.suffix.lower() not in VIDEO_EXTS or re.search(r"\.f\d+$", p.stem):
        return None
    return p.stem.split("--")[0]


def videos_for(exercise_id: str) -> list[Path]:
    VIDEOS_DIR.mkdir(exist_ok=True)
    return sorted((p for p in VIDEOS_DIR.iterdir() if _video_owner(p) == exercise_id), key=lambda p: (p.stat().st_mtime, p.name))


def list_local_videos() -> dict[str, list[str]]:
    VIDEOS_DIR.mkdir(exist_ok=True)
    result: dict[str, list[Path]] = {}
    for p in VIDEOS_DIR.iterdir():
        owner = _video_owner(p)
        if owner:
            result.setdefault(owner, []).append(p)
    return {k: [f"./videos/{p.name}" for p in sorted(v, key=lambda p: (p.stat().st_mtime, p.name))] for k, v in result.items()}


def _next_video_stem(ex_id: str) -> str:
    taken = {p.stem for p in VIDEOS_DIR.iterdir() if p.is_file()}
    if ex_id not in taken:
        return ex_id
    n = 2
    while f"{ex_id}--{n}" in taken:
        n += 1
    return f"{ex_id}--{n}"


def update_exercises_json_video(exercise_id: str, rel_path: str | None = None) -> None:
    """Keep exercises.json in sync with what's in videos/ ("video" = first, "videos" = all)."""
    if not EXERCISES_JSON.exists():
        return
    paths = [f"./videos/{p.name}" for p in videos_for(exercise_id)]
    try:
        data = json.loads(EXERCISES_JSON.read_text(encoding="utf-8"))
        changed = False
        for ex in data.get("exercises", []):
            if ex.get("id") == exercise_id:
                if paths:
                    ex["video"] = paths[0]
                    ex["videos"] = paths
                else:
                    ex.pop("video", None)
                    ex.pop("videos", None)
                changed = True
                break
        if changed:
            EXERCISES_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass


# ---------- Favourite YouTube channels (channels.json is committed, so they show on every device) ----------
CHANNELS_JSON = ROOT_DIR / "channels.json"
_CHANNEL_URL = re.compile(r"^https://www\.youtube\.com/(@[^/\s\"<>]+|channel/[^/\s\"<>]+|c/[^/\s\"<>]+|user/[^/\s\"<>]+)$")


def save_channels(channels: list) -> list:
    if not isinstance(channels, list):
        raise ValueError("channels must be a list")
    clean, seen = [], set()
    for c in channels[:200]:
        if not isinstance(c, dict):
            continue
        url = str(c.get("url", "")).strip()
        if not _CHANNEL_URL.match(url) or url.lower() in seen:
            continue
        seen.add(url.lower())
        clean.append({"url": url, "label": str(c.get("label", ""))[:100], "name": str(c.get("name", ""))[:100]})
    CHANNELS_JSON.write_text(json.dumps({"channels": clean}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return clean


# ---------- Real muscle photos (parts.json + images/parts/, committed so every device gets them) ----------
PARTS_JSON = ROOT_DIR / "parts.json"
PARTS_DIR = ROOT_DIR / "images" / "parts"
_TARGET = re.compile(r"^[a-z0-9_]{1,40}$")


def _load_parts() -> dict:
    try:
        data = json.loads(PARTS_JSON.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("images"), list):
            return data
    except Exception:
        pass
    return {"images": []}


def _save_parts(data: dict) -> None:
    PARTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_part_photo(targets: list, data_url: str) -> dict:
    targets = [t for t in (targets or []) if isinstance(t, str) and _TARGET.match(t)][:40]
    if not targets:
        raise ValueError("No muscle part given")
    m = re.match(r"^data:image/(jpeg|jpg|png|webp);base64,(.+)$", data_url or "", re.S)
    if not m:
        raise ValueError("Expected a JPEG/PNG/WebP image")
    raw = base64.b64decode(m.group(2))
    if len(raw) > 15 * 1024 * 1024:
        raise ValueError("Image is larger than 15 MB")
    ext = "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{targets[0]}-{int(time.time() * 1000)}.{ext}"
    (PARTS_DIR / name).write_bytes(raw)
    data = _load_parts()
    entry = {"file": f"images/parts/{name}", "targets": targets, "ts": int(time.time())}
    data["images"].append(entry)
    _save_parts(data)
    return entry


def delete_part_photo(file: str) -> None:
    name = Path(str(file or "")).name
    data = _load_parts()
    data["images"] = [e for e in data["images"] if Path(e.get("file", "")).name != name]
    _save_parts(data)
    if name:
        (PARTS_DIR / name).unlink(missing_ok=True)


# ---------- iPhone-friendly MP4 ----------
# Without ffmpeg, yt-dlp saves YouTube's DASH stream as a *fragmented* MP4 (moof/mdat chunks, empty
# sample tables, bogus last-frame duration). Chrome plays it, but iOS (Safari and Photos) freezes the
# picture part-way while the timer keeps counting. Rewriting it as a normal MP4 fixes that. No re-encode.

def _boxes(data: bytes, start: int, end: int):
    pos = start
    while pos + 8 <= end:
        size, typ = struct.unpack(">I4s", data[pos:pos + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - pos
        if size < hdr:
            return
        yield typ, pos, pos + hdr, pos + size
        pos += size


def _is_fragmented(path: Path) -> bool:
    data = path.read_bytes()
    return any(t == b"moof" for t, *_ in _boxes(data, 0, len(data)))


def _fix_last_frame_duration(path: Path) -> bool:
    """YouTube's last video frame often claims to last ~the whole clip. Set it to a normal frame length."""
    data = bytearray(path.read_bytes())
    changed = False
    for t, _, b, e in _boxes(data, 0, len(data)):
        if t != b"moov":
            continue
        for t2, _, b2, e2 in _boxes(data, b, e):
            if t2 != b"trak":
                continue
            for t3, _, b3, e3 in _boxes(data, b2, e2):
                if t3 != b"mdia":
                    continue
                kids = {k: (bb, ee) for k, _, bb, ee in _boxes(data, b3, e3)}
                if b"hdlr" not in kids or data[kids[b"hdlr"][0] + 8:kids[b"hdlr"][0] + 12] != b"vide":
                    continue
                mdhd = kids.get(b"mdhd")
                stts = None
                for t4, _, b4, e4 in _boxes(data, *kids.get(b"minf", (0, 0))):
                    if t4 == b"stbl":
                        for t5, _, b5, e5 in _boxes(data, b4, e4):
                            if t5 == b"stts":
                                stts = b5
                if stts is None or mdhd is None:
                    continue
                n = struct.unpack(">I", data[stts + 4:stts + 8])[0]
                ents = [list(struct.unpack(">II", data[stts + 8 + 8 * i:stts + 16 + 8 * i])) for i in range(n)]
                if len(ents) < 2 or ents[-1][0] != 1:
                    continue
                normal = max(ents[:-1], key=lambda x: x[0])[1]
                if normal and ents[-1][1] > normal * 4:
                    ents[-1][1] = normal
                    struct.pack_into(">II", data, stts + 8 + 8 * (n - 1), *ents[-1])
                    total = sum(c * d for c, d in ents)
                    v = data[mdhd[0]]
                    if v == 1:
                        struct.pack_into(">Q", data, mdhd[0] + 24, total)
                    else:
                        struct.pack_into(">I", data, mdhd[0] + 16, total)
                    changed = True
    if changed:
        path.write_bytes(bytes(data))
    return changed


def make_phone_friendly(path: Path, env: dict | None = None) -> str:
    """Rewrite a video as a standard, fast-start MP4. Returns a short status."""
    env = env or os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
    if path.suffix.lower() not in {".mp4", ".m4v", ".mov"}:
        return "skipped (not mp4)"
    status = "ok"
    if _is_fragmented(path):
        tmp = Path(tempfile.mkstemp(suffix=".mp4", dir=str(path.parent))[1])
        tmp.unlink(missing_ok=True)
        ffmpeg = shutil.which("ffmpeg", path=env["PATH"])
        if ffmpeg:
            cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(path), "-c", "copy", "-movflags", "+faststart", str(tmp)]
        elif shutil.which("avconvert"):  # built into macOS
            cmd = ["avconvert", "-s", str(path), "-p", "PresetPassthrough", "-o", str(tmp), "--replace"]
        else:
            return "fragmented, but no ffmpeg/avconvert to repair it"
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
        if proc.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
            tmp.unlink(missing_ok=True)
            return "repair failed: " + (proc.stderr or proc.stdout or "").strip()[-200:]
        tmp.replace(path)
        status = "repaired"
    if _fix_last_frame_duration(path):
        status = "repaired"
    return status


def download_youtube_video(url: str, exercise_id: str) -> dict:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Please provide a valid http(s) YouTube URL.")

    ex_id = sanitize_id(exercise_id)
    VIDEOS_DIR.mkdir(exist_ok=True)

    # Each download is added next to the existing videos (never replaces them)
    stem = _next_video_stem(ex_id)
    out_template = str(VIDEOS_DIR / f"{stem}.%(ext)s")
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
    # Apple's bundled Python 3.9 has no CA bundle -> CERTIFICATE_VERIFY_FAILED. Point it at one.
    if not env.get("SSL_CERT_FILE"):
        try:
            import certifi  # type: ignore
            env["SSL_CERT_FILE"] = certifi.where()
        except Exception:
            if Path("/etc/ssl/cert.pem").exists():
                env["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"

    # Separate video+audio streams need ffmpeg to merge. Without it, grab a single ready-made mp4
    # (otherwise yt-dlp leaves half files like name.f134.mp4 + name.f140.m4a behind).
    has_ffmpeg = shutil.which("ffmpeg", path=env["PATH"]) is not None
    if has_ffmpeg:
        fmt_args = ["-f", "bv*[ext=mp4][vcodec^=avc1][height<=720]+ba[ext=m4a]/b[ext=mp4][height<=720]/b[ext=mp4]/best",
                    "--merge-output-format", "mp4"]
    else:
        # Single file with sound if YouTube offers one, else a silent H.264 mp4 (plays on every phone).
        # Install ffmpeg (brew install ffmpeg) to get sound on videos like Shorts.
        fmt_args = ["-f", "b[ext=mp4][height<=720]/bv*[ext=mp4][vcodec^=avc1][height<=720]/bv*[ext=mp4][vcodec^=avc1]/b"]

    cmd = find_yt_dlp() + ["--no-playlist", "--no-warnings", *fmt_args, "-o", out_template, url.strip()]

    try:
        proc = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Download took longer than 5 minutes and was stopped.")
    # Clean up any intermediate stream files (name.f134.mp4, name.f140.m4a, .part)
    for leftover in VIDEOS_DIR.glob(f"{stem}.*"):
        if re.search(r"\.f\d+\.|\.part$|\.ytdl$", leftover.name):
            leftover.unlink(missing_ok=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "yt-dlp failed").strip()
        if "No module named yt_dlp" in err or "No such file" in err:
            raise RuntimeError("yt-dlp is not installed. Run: brew install yt-dlp")
        raise RuntimeError(err.splitlines()[-1] if err else "Download failed")

    matches = sorted(p for p in VIDEOS_DIR.glob(f"{stem}.*") if p.suffix.lower() in VIDEO_EXTS)
    if not matches:
        raise RuntimeError("Download finished but no output file was found.")

    try:
        make_phone_friendly(matches[0], env)
    except Exception as exc:  # never fail the download because of the repair step
        print(f"Warning: could not make {matches[0].name} iPhone-friendly: {exc}", file=sys.stderr)

    rel_path = f"./videos/{matches[0].name}"
    update_exercises_json_video(ex_id)
    note = "" if has_ffmpeg else "Saved without sound — run 'brew install ffmpeg' for audio."
    return {"ok": True, "exerciseId": ex_id, "path": rel_path, "note": note}


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

        if self.path == "/api/part-photo":
            try:
                self.send_json(200, {"ok": True, "image": add_part_photo(data.get("targets"), data.get("dataUrl", ""))})
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if self.path == "/api/part-photo-delete":
            try:
                delete_part_photo(data.get("file", ""))
                self.send_json(200, {"ok": True})
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if self.path == "/api/channels":
            try:
                self.send_json(200, {"ok": True, "channels": save_channels(data.get("channels", []))})
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if self.path == "/api/delete-video":
            try:
                ex_id = sanitize_id(data.get("exerciseId", ""))
                name = Path(str(data.get("file", ""))).name  # delete just this one video
                for old in videos_for(ex_id):
                    if not name or old.name == name:
                        old.unlink(missing_ok=True)
                update_exercises_json_video(ex_id)
                self.send_json(200, {"ok": True})
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if self.path == "/api/reveal-video":
            try:
                VIDEOS_DIR.mkdir(exist_ok=True)
                if data.get("all"):
                    if sys.platform == "darwin":
                        subprocess.Popen(["open", str(VIDEOS_DIR)])
                    elif sys.platform.startswith("win"):
                        os.startfile(str(VIDEOS_DIR))
                    else:
                        subprocess.Popen(["xdg-open", str(VIDEOS_DIR)])
                    self.send_json(200, {"ok": True, "path": str(VIDEOS_DIR)})
                    return
                name = Path(str(data.get("file", ""))).name
                if not name:
                    raise ValueError("Missing file name")
                target = (VIDEOS_DIR / name).resolve()
                if target.parent != VIDEOS_DIR.resolve() or not target.exists():
                    raise FileNotFoundError(f"Video not found: {name}")
                if sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", str(target)])
                elif sys.platform.startswith("win"):
                    subprocess.Popen(["explorer", "/select,", str(target)])
                else:
                    subprocess.Popen(["xdg-open", str(VIDEOS_DIR)])
                self.send_json(200, {"ok": True, "path": str(target)})
            except Exception as e:
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if self.path == "/api/airdrop-video":
            try:
                if sys.platform != "darwin":
                    raise RuntimeError("AirDrop is only available on macOS")
                VIDEOS_DIR.mkdir(exist_ok=True)
                airdrop_app = "/System/Library/CoreServices/Finder.app/Contents/Applications/AirDrop.app"
                if data.get("all"):
                    subprocess.Popen(["open", airdrop_app])
                    subprocess.Popen(["open", str(VIDEOS_DIR)])
                    self.send_json(200, {"ok": True, "path": str(VIDEOS_DIR)})
                    return
                name = Path(str(data.get("file", ""))).name
                if not name:
                    raise ValueError("Missing file name")
                target = (VIDEOS_DIR / name).resolve()
                if target.parent != VIDEOS_DIR.resolve() or not target.exists():
                    raise FileNotFoundError(f"Video not found: {name}")
                subprocess.Popen(["open", airdrop_app])
                subprocess.Popen(["open", "-R", str(target)])
                self.send_json(200, {"ok": True, "path": str(target)})
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
    parser.add_argument("--fix-videos", action="store_true", help="Repair videos in videos/ that freeze on iPhone")
    args = parser.parse_args()

    if args.fix_videos:
        for vid in sorted(VIDEOS_DIR.glob("*")):
            if vid.suffix.lower() in {".mp4", ".m4v", ".mov"} and not re.search(r"\.f\d+\.", vid.name):
                print(f"{vid.name}: {make_phone_friendly(vid)}")
        return

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
