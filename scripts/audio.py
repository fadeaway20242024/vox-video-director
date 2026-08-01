#!/usr/bin/env python3
"""Audio stage for the no-Atlas workflow.

This script generates missing per-beat narration with ElevenLabs, validates
local narration/music files, and records durations in beats.json for assemble.py.

Supported inputs:
  1) One full narration track:
       "narration_audio": "path/to/voice.mp3"
     or "voice_path": "path/to/voice.mp3"

  2) Per-beat narration tracks:
       beat["narration_audio"] = "path/to/beat_1.mp3"

  3) Generated per-beat narration:
       beat["narration"] = "text to speak"
     Requires ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID.

  Optional music:
       "bgm_path": "path/to/music.mp3"
     or "music_path": "path/to/music.mp3"

Usage: python3 audio.py <project_dir>   (default: out/tang-30s)
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


ELEVENLABS_BASE = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io").rstrip("/")
DEFAULT_MODEL = "eleven_multilingual_v2"
DEFAULT_FORMAT = "mp3_44100_128"


def _load_dotenv():
    """Load simple KEY=VALUE pairs from likely .env locations without overriding env."""
    candidates = []
    cur = os.getcwd()
    for _ in range(6):
        candidates.append(os.path.join(cur, ".env"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

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
                    os.environ[key] = value.strip().strip('"').strip("'")
        except OSError:
            continue


_load_dotenv()


def probe_dur(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


def _abs(project_dir, path):
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(project_dir, path))


def _require_file(label, path):
    if not path:
        raise SystemExit(f"missing {label}")
    if not os.path.exists(path):
        raise SystemExit(f"{label} does not exist: {path}")
    if os.path.getsize(path) == 0:
        raise SystemExit(f"{label} is empty: {path}")
    return path


def _eleven_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("missing ELEVENLABS_API_KEY; cannot generate narration")
    return key


def _eleven_voice_id(doc):
    voice_cfg = doc.get("voice", {}) if isinstance(doc.get("voice"), dict) else {}
    voice_id = (
        voice_cfg.get("elevenlabs_voice_id")
        or doc.get("elevenlabs_voice_id")
        or os.environ.get("ELEVENLABS_VOICE_ID")
    )
    if not voice_id:
        raise SystemExit("missing ELEVENLABS_VOICE_ID; cannot generate narration")
    return voice_id


def _eleven_model(doc):
    voice_cfg = doc.get("voice", {}) if isinstance(doc.get("voice"), dict) else {}
    return (
        voice_cfg.get("elevenlabs_model_id")
        or doc.get("elevenlabs_model_id")
        or os.environ.get("ELEVENLABS_MODEL_ID")
        or DEFAULT_MODEL
    )


def _eleven_output_format(doc):
    voice_cfg = doc.get("voice", {}) if isinstance(doc.get("voice"), dict) else {}
    return (
        voice_cfg.get("elevenlabs_output_format")
        or doc.get("elevenlabs_output_format")
        or os.environ.get("ELEVENLABS_OUTPUT_FORMAT")
        or DEFAULT_FORMAT
    )


def _eleven_voice_settings(doc):
    voice_cfg = doc.get("voice", {}) if isinstance(doc.get("voice"), dict) else {}
    settings = voice_cfg.get("settings") or doc.get("elevenlabs_voice_settings")
    if isinstance(settings, dict):
        return settings
    return {
        "stability": float(os.environ.get("ELEVENLABS_STABILITY", "0.45")),
        "similarity_boost": float(os.environ.get("ELEVENLABS_SIMILARITY_BOOST", "0.85")),
        "style": float(os.environ.get("ELEVENLABS_STYLE", "0.2")),
        "use_speaker_boost": os.environ.get("ELEVENLABS_USE_SPEAKER_BOOST", "true").lower() != "false",
    }


def generate_elevenlabs(text, dest, *, voice_id, model_id, output_format, voice_settings):
    """Generate one narration mp3 with ElevenLabs."""
    if not text or not text.strip():
        raise SystemExit(f"empty narration text for {dest}")
    query = urllib.parse.urlencode({"output_format": output_format})
    url = f"{ELEVENLABS_BASE}/v1/text-to-speech/{urllib.parse.quote(voice_id)}?{query}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "xi-api-key": _eleven_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "User-Agent": "vox-director-elevenlabs/0.1",
        },
        method="POST",
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"ElevenLabs TTS failed for {dest}: HTTP {e.code}: {body[:500]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"ElevenLabs TTS failed for {dest}: {e}") from e
    with open(dest, "wb") as f:
        f.write(data)
    _require_file("ElevenLabs output", dest)
    return dest


def run(project_dir: str):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath) as f:
        doc = json.load(f)

    full_narr = _abs(project_dir, doc.get("narration_audio") or doc.get("voice_path"))
    if full_narr:
        _require_file("narration_audio", full_narr)
        doc["narration_audio"] = full_narr
        doc["narration_dur"] = round(probe_dur(full_narr), 2)
        print(f"[narration] {doc['narration_dur']}s -> {full_narr}")
    else:
        adir = os.path.join(project_dir, "audio")
        voice_id = _eleven_voice_id(doc)
        model_id = _eleven_model(doc)
        output_format = _eleven_output_format(doc)
        voice_settings = _eleven_voice_settings(doc)
        doc["audio_provider"] = "elevenlabs"
        doc["elevenlabs_model_id"] = model_id
        doc["elevenlabs_output_format"] = output_format
        for beat in doc["beats"]:
            narr = _abs(project_dir, beat.get("narration_audio"))
            if narr and os.path.exists(narr) and os.path.getsize(narr) > 0:
                print(f"[narr {beat['id']}] reuse {narr}")
            else:
                narr = os.path.join(adir, f"narr_{beat['id']}.mp3")
                generate_elevenlabs(
                    beat.get("narration") or beat.get("text") or "",
                    narr,
                    voice_id=voice_id,
                    model_id=model_id,
                    output_format=output_format,
                    voice_settings=voice_settings,
                )
                print(f"[narr {beat['id']}] generated with ElevenLabs -> {narr}")
            _require_file(f"beat {beat['id']} narration_audio", narr)
            beat["narration_audio"] = narr
            beat["narration_dur"] = round(probe_dur(narr), 2)
            print(f"[narr {beat['id']}] {beat['narration_dur']}s -> {narr}")

    bgm = _abs(project_dir, doc.get("bgm_path") or doc.get("music_path"))
    if bgm:
        _require_file("bgm_path/music_path", bgm)
        doc["bgm_path"] = bgm
        doc["bgm_dur"] = round(probe_dur(bgm), 2)
        print(f"[bgm] {doc['bgm_dur']}s -> {bgm}")
    else:
        doc.pop("bgm_path", None)
        doc.pop("bgm_dur", None)
        print("[bgm] none; assemble.py will render narration-only audio")

    with open(bpath, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("updated", bpath)


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "out", "tang-30s")
    run(os.path.abspath(proj))
