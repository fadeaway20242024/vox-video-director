# Voice notes — ElevenLabs no-Atlas fork

This fork uses ElevenLabs for generated narration.

Environment:

```bash
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
```

If a local narration file is already present, it is reused:

```json
{
  "narration_audio": "out/project/audio/voice.mp3",
  "bgm_path": "out/project/audio/bgm.mp3"
}
```

or per-beat local narration:

```json
{
  "beats": [
    {"id": 1, "narration_audio": "out/project/audio/narr_1.mp3"}
  ]
}
```

Then run:

```bash
python3 scripts/audio.py out/project
python3 scripts/assemble.py out/project
```

If no local narration is present, `audio.py` generates per-beat files from `beat["narration"]`:

```text
out/project/audio/narr_1.mp3
out/project/audio/narr_2.mp3
```

BGM/music remains local through `bgm_path` or `music_path`.
