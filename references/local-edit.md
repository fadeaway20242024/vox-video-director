# Local source-clip editing

Use this mode when the user already has rendered video clips. It is the preferred path for
re-cutting an existing VOX-style sequence: do not regenerate images or call a remote video
provider unless the user asks for new motion.

## Configuration

Create `<project>/local_edit.json`:

```json
{
  "width": 1280,
  "height": 720,
  "fps": 24,
  "clip_duration": 2.5,
  "source_audio": false,
  "voice_volume": 1.25,
  "source_audio_volume": 0.85,
  "music_volume": 0.20,
  "clips": [
    {"path": "/absolute/path/clip-01.mp4"},
    {"path": "/absolute/path/clip-02.mp4"}
  ],
  "narration": [
    {"path": "audio/narr_01.mp3", "at": 0.0},
    {"path": "audio/narr_02.mp3", "at": 5.0}
  ],
  "captions_path": "captions.srt",
  "color_correction": {
    "start": 7.5,
    "end": 10.0,
    "filter": "contrast=1.02:saturation=0.78:brightness=0.01"
  },
  "output": "final-local.mp4"
}
```

Paths inside the project directory may be relative; source clips may be absolute paths. Each
clip is normalized to the project canvas and trimmed to `clip_duration` (default 2.5 seconds).
The timeline duration is the sum of clip durations unless `duration` is set explicitly.

Run:

```bash
python3 scripts/local_assemble.py <project>
```

## Audio modes

- **Narration only:** set `source_audio: false` and omit `music_path`.
- **Narration + source SFX:** keep `source_audio: true` and omit `music_path`. Original clip
  audio is retained and ducked beneath the voice.
- **Narration + source SFX + music:** keep `source_audio: true` and set `music_path`.
  Music is ducked under the narration; `music_volume` should normally be 0.15–0.25.
- **Narration + music, no SFX:** set `source_audio: false` and set `music_path`.

The standard clean-master configuration omits `music_path`; add it only after the user chooses
to include music. Narration tracks are delayed by their `at` values and mixed into one voice
bus. Use one voice throughout a film when the user asks for a consistent narrator. For
Doubao/Volcengine, generate
the local files first with the configured voice, then point `narration[].path` at those files;
never place API keys in `local_edit.json`.

## Captions and color repair

Use an SRT file with timings aligned to the narration. Burn it in with the local script. On
macOS, the default Chinese font is `Hiragino Sans GB W3`; if it is unavailable, choose another
installed CJK font explicitly. Verify at least the first, middle, and final caption frames.

For a clip with a color jump, apply a narrow time-bounded correction in `color_correction`.
Do not grade the entire film to repair one segment. A typical repair is a small reduction in
saturation plus a slight contrast lift; inspect before/after frames before claiming the issue is
fixed.

## Music licensing

For open music, prefer CC0 or CC BY tracks. CC BY allows commercial use and remixing with
attribution; CC BY-ND is not suitable for syncing to video without additional permission. Save
the track page and attribution text alongside the project. FMA does not own the uploaded music's
copyright, so the track-level license is authoritative.

## Verification checklist

1. `ffprobe` reports the intended duration, canvas, frame rate, and audio channels.
2. Extract frames at the first, repaired segment, middle, and final caption; inspect pixels.
3. Listen for voice clarity, source SFX presence, and music ducking if music is enabled.
4. Check that the final sentence's audio and subtitle end together.
5. Keep the no-music/no-audio variants when the user may want alternate deliverables.
