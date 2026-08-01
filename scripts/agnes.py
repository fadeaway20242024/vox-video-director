#!/usr/bin/env python3
"""
Agnes API client for vox-director's video stage.

This backend is intentionally video-first. Codex imagegen is a host-side tool,
not a Python API, so this module uploads the generated local keyframes to a
public image host before Agnes animates them.

Env:
  AGNES_API_KEY             required, or VIDEO_API_KEY as a compatibility alias
  AGNES_API_BASE            optional, default https://apihub.agnes-ai.com
  IMGW_API_KEY              optional, enables local image upload through imgw.cc
  IMGW_API_URL              optional, default https://www.imgw.cc/api/1/upload
  IMGW_SOURCE_FIELD         optional, default source
  IMGW_AUTH_HEADER          optional, default X-API-Key
"""
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request


def _load_dotenv():
    """Load simple KEY=VALUE pairs from likely .env locations without overriding env."""
    here = os.path.abspath(os.path.dirname(__file__))
    candidates = []
    cur = os.getcwd()
    for _ in range(6):
        candidates.append(os.path.join(cur, ".env"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    candidates.append(os.path.join(os.path.dirname(here), ".env"))

    seen = set()
    for path in candidates:
        if path in seen or not os.path.exists(path):
            continue
        seen.add(path)
        try:
            with open(path, encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    if not key or key in os.environ:
                        continue
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        except OSError:
            continue


_load_dotenv()

API_BASE = os.environ.get("AGNES_API_BASE", "https://apihub.agnes-ai.com").rstrip("/")
IMGW_API_URL = os.environ.get("IMGW_API_URL", "https://www.imgw.cc/api/1/upload")
UA = "vox-director-agnes/0.1"


class AgnesError(RuntimeError):
    pass


def _key() -> str:
    k = os.environ.get("AGNES_API_KEY") or os.environ.get("VIDEO_API_KEY")
    if not k:
        raise AgnesError("AGNES_API_KEY is not set. VIDEO_API_KEY is also accepted as a compatibility alias.")
    return k


def _headers(json_body: bool = True) -> dict:
    h = {"Authorization": f"Bearer {_key()}", "User-Agent": UA}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def _post(path: str, payload: dict, timeout: int = 90) -> dict:
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise AgnesError(f"POST {path} -> {e.code}: {body[:500]}") from e
    except urllib.error.URLError as e:
        raise AgnesError(f"POST {path} failed: {e}") from e


def _get(path: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(API_BASE + path, headers=_headers(json_body=False))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise AgnesError(f"GET {path} -> {e.code}: {body[:500]}") from e
    except urllib.error.URLError as e:
        raise AgnesError(f"GET {path} failed: {e}") from e


def _frames_for_duration(seconds, fps=24):
    """Agnes requires num_frames <= 441 and 8n+1.

    Pick the closest valid frame count for the requested shot duration.
    """
    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        seconds = 5.0
    raw = max(1, round(seconds * fps))
    raw = min(raw, 441)
    n = max(1, round((raw - 1) / 8))
    return min(441, 8 * n + 1), fps


def _size_for_aspect(aspect, resolution="720p"):
    """Return width/height that Agnes will normalize predictably."""
    tiers = {
        "480p": {"16:9": (832, 448), "9:16": (448, 832), "1:1": (640, 640), "4:3": (640, 480), "3:4": (480, 640)},
        "720p": {"16:9": (1152, 768), "9:16": (768, 1152), "1:1": (1024, 1024), "4:3": (1024, 768), "3:4": (768, 1024)},
        "1080p": {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1536, 1536), "4:3": (1440, 1080), "3:4": (1080, 1440)},
    }
    return tiers.get(str(resolution), tiers["720p"]).get(str(aspect), tiers["720p"]["16:9"])


def _find_image_url(obj):
    """Best-effort extraction for Chevereto-like image-host responses."""
    if isinstance(obj, str):
        if obj.startswith(("https://", "http://")):
            return obj.strip()
        return None
    if isinstance(obj, list):
        for item in obj:
            found = _find_image_url(item)
            if found:
                return found
        return None
    if not isinstance(obj, dict):
        return None

    preferred = (
        "url",
        "display_url",
        "image_url",
        "pictureUrl",
        "medium",
        "original",
    )
    for key in preferred:
        value = obj.get(key)
        if isinstance(value, str) and value.startswith(("https://", "http://")):
            return value

    for key in ("image", "data", "links", "rows", "result", "success"):
        if key in obj:
            found = _find_image_url(obj[key])
            if found:
                return found

    for value in obj.values():
        found = _find_image_url(value)
        if found:
            return found
    return None


def upload_imgw(path: str) -> str:
    """Upload a local image to imgw.cc and return a public URL."""
    key = os.environ.get("IMGW_API_KEY")
    if not key:
        raise AgnesError("IMGW_API_KEY is not set; cannot upload local keyframe to imgw.cc.")
    if not os.path.exists(path):
        raise AgnesError(f"local keyframe does not exist: {path}")

    source_field = os.environ.get("IMGW_SOURCE_FIELD", "source")
    auth_header = os.environ.get("IMGW_AUTH_HEADER", "X-API-Key")
    cmd = [
        "/usr/bin/curl",
        "--fail-with-body",
        "-sS",
        "-X",
        "POST",
        "-H",
        f"{auth_header}: {key}",
        "-F",
        f"{source_field}=@{path}",
        "-F",
        "format=json",
        IMGW_API_URL,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # Do not include the command line because it contains the API key.
        raise AgnesError(f"imgw.cc upload failed ({proc.returncode}): {(proc.stderr or proc.stdout)[:500]}")

    body = proc.stdout.strip()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        url = _find_image_url(body)
        if url:
            return url
        raise AgnesError(f"imgw.cc upload returned non-JSON response: {body[:500]}")

    url = _find_image_url(data)
    if not url:
        raise AgnesError(f"imgw.cc upload response did not contain a public URL: {json.dumps(data)[:500]}")
    if not url.startswith("https://"):
        raise AgnesError(f"imgw.cc returned a non-HTTPS URL, Agnes may reject it: {url}")
    return url


def submit_video(model: str, prompt: str, **params) -> str:
    """Submit an Agnes image-to-video/text-to-video task; return video_id."""
    model = model or "agnes-video-v2.0"
    image = params.get("image")
    aspect = params.get("aspect_ratio") or params.get("ratio") or "16:9"
    resolution = params.get("resolution", "720p")
    width, height = _size_for_aspect(aspect, resolution)
    frames, fps = _frames_for_duration(params.get("duration", 5), params.get("frame_rate", 24))

    body = {
        "model": model,
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_frames": params.get("num_frames", frames),
        "frame_rate": params.get("frame_rate", fps),
    }
    if image:
        body["image"] = image
        body["mode"] = params.get("mode", "ti2vid")
    if params.get("negative_prompt"):
        body["negative_prompt"] = params["negative_prompt"]
    if params.get("seed") is not None:
        body["seed"] = params["seed"]

    data = _post("/v1/videos", body)
    video_id = data.get("video_id") or data.get("id") or data.get("task_id")
    if not video_id:
        raise AgnesError(f"video submit returned no id: {json.dumps(data)[:500]}")
    return video_id


def get_status(video_id: str) -> dict:
    """Normalize Agnes status to provider.py's status contract."""
    q = urllib.parse.urlencode({"video_id": video_id, "model_name": "agnes-video-v2.0"})
    try:
        d = _get(f"/agnesapi?{q}")
    except AgnesError as e:
        return {"status": "failed", "output": None, "error": str(e)}

    status = d.get("status")
    if status == "completed":
        meta = d.get("metadata") or {}
        url = meta.get("url") or d.get("url") or d.get("output")
        return {"status": "completed", "output": url, "error": None}
    if status == "failed":
        return {"status": "failed", "output": None, "error": json.dumps(d.get("error") or d)[:500]}
    if status in ("queued", "in_progress", "pending", None):
        return {"status": "pending", "output": None, "error": None}
    return {"status": "pending", "output": None, "error": None}


def upload(path: str) -> str:
    """Agnes image-to-video requires a public image URL.

    This function accepts an existing URL or uploads a local file to imgw.cc
    when IMGW_API_KEY is available.
    """
    if path.startswith(("http://", "https://")):
        return path
    return upload_imgw(path)


def download(url: str, dest: str) -> str:
    subprocess.run(["/usr/bin/curl", "-L", "-s", "--retry", "3", "-o", dest, url], check=True)
    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        raise AgnesError(f"download produced empty file: {url}")
    return dest
