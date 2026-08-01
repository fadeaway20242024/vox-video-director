#!/usr/bin/env python3
"""Assemble an existing VOX-style clip sequence with local FFmpeg.

This is the local source-clip path: it keeps clip audio when requested, mixes
delayed narration, optionally ducks a local music track, burns an SRT, and can
apply a narrow time-bounded color repair.

Usage: python3 local_assemble.py <project_dir>
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from typing import Any


DEFAULT_CAPTION_STYLE = (
    "FontName=Hiragino Sans GB W3,FontSize=20,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&HCC000000,"
    "BackColour=&H88000000,BorderStyle=3,Outline=1,Shadow=0,"
    "Alignment=2,MarginV=36"
)


def _abs(project: str, path: str | None) -> str | None:
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(project, path))


def _require(label: str, path: str | None) -> str:
    if not path:
        raise SystemExit(f"missing {label}")
    if not os.path.isfile(path):
        raise SystemExit(f"{label} does not exist: {path}")
    if os.path.getsize(path) == 0:
        raise SystemExit(f"{label} is empty: {path}")
    return path


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _filter_quote(path: str) -> str:
    """Escape a filesystem path for the FFmpeg subtitles filter."""
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _run(args: list[str]) -> None:
    print("$", shlex.join(args))
    subprocess.run(args, check=True)


def _load(project: str) -> dict[str, Any]:
    cfg_path = os.path.join(project, "local_edit.json")
    if not os.path.isfile(cfg_path):
        raise SystemExit(f"missing config: {cfg_path}")
    with open(cfg_path, encoding="utf-8") as handle:
        doc = json.load(handle)
    if not isinstance(doc, dict):
        raise SystemExit("local_edit.json must contain a JSON object")
    return doc


def build_command(project: str, doc: dict[str, Any]) -> tuple[list[str], str, float]:
    width = int(doc.get("width", 1280))
    height = int(doc.get("height", 720))
    fps = int(doc.get("fps", 24))
    default_clip_duration = _number(doc.get("clip_duration"), 2.5)
    # Clean master is the default; explicitly opt in to source SFX.
    source_audio = bool(doc.get("source_audio", False))
    voice_volume = _number(doc.get("voice_volume"), 1.25)
    source_audio_volume = _number(doc.get("source_audio_volume"), 0.85)
    music_volume = _number(doc.get("music_volume"), 0.20)

    raw_clips = doc.get("clips")
    if not isinstance(raw_clips, list) or not raw_clips:
        raise SystemExit("local_edit.json needs a non-empty clips array")
    clips: list[tuple[str, float]] = []
    for index, item in enumerate(raw_clips, 1):
        if isinstance(item, str):
            path, duration = item, default_clip_duration
        elif isinstance(item, dict):
            path = item.get("path")
            duration = _number(item.get("duration"), default_clip_duration)
        else:
            raise SystemExit(f"clips[{index}] must be a path or object")
        clips.append((_require(f"clips[{index}]", _abs(project, path)), duration))
    total = _number(doc.get("duration"), sum(duration for _, duration in clips))
    if total <= 0:
        raise SystemExit("timeline duration must be positive")

    narration = doc.get("narration") or []
    if not isinstance(narration, list):
        raise SystemExit("narration must be an array")
    narration_files: list[tuple[str, float]] = []
    for index, item in enumerate(narration, 1):
        if isinstance(item, str):
            path, start = item, 0.0
        elif isinstance(item, dict):
            path, start = item.get("path"), _number(item.get("at"), 0.0)
        else:
            raise SystemExit(f"narration[{index}] must be a path or object")
        narration_files.append((_require(f"narration[{index}]", _abs(project, path)), start))

    music = _abs(project, doc.get("music_path") or doc.get("bgm_path"))
    if music:
        _require("music_path", music)
    captions = _abs(project, doc.get("captions_path") or doc.get("srt_path"))
    if captions:
        _require("captions_path", captions)

    inputs: list[str] = []
    for path, _ in clips:
        inputs += ["-i", path]
    for path, _ in narration_files:
        inputs += ["-i", path]
    music_index = None
    if music:
        music_index = len(clips) + len(narration_files)
        inputs += ["-i", music]

    filters: list[str] = []
    video_labels: list[str] = []
    sfx_labels: list[str] = []
    for index, (_, duration) in enumerate(clips):
        vlabel = f"vclip{index}"
        filters.append(
            f"[{index}:v]fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
            f"trim=duration={duration:.3f},setpts=PTS-STARTPTS[{vlabel}]"
        )
        video_labels.append(f"[{vlabel}]")
        if source_audio:
            alabel = f"sfx{index}"
            filters.append(
                f"[{index}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,"
                f"atrim=duration={duration:.3f},asetpts=PTS-STARTPTS[{alabel}]"
            )
            sfx_labels.append(f"[{alabel}]")

    if source_audio:
        concat_inputs = "".join(
            f"[{video_labels[index][1:-1]}][{sfx_labels[index][1:-1]}]"
            for index in range(len(clips))
        )
        filters.append(
            f"{concat_inputs}concat=n={len(clips)}:v=1:a=1[vcat][sfxcat]"
        )
    else:
        filters.append(f"{''.join(video_labels)}concat=n={len(clips)}:v=1:a=0[vcat]")

    current_video = "vcat"
    correction = doc.get("color_correction")
    if isinstance(correction, dict) and correction.get("filter"):
        start = _number(correction.get("start"), 0.0)
        end = _number(correction.get("end"), total)
        correction_filter = str(correction["filter"]).replace("'", "\\'")
        filters.append(
            f"[{current_video}]eq={correction_filter}:enable='between(t,{start:.3f},{end:.3f})'[vcolor]"
        )
        current_video = "vcolor"

    if captions:
        style = str(doc.get("caption_style") or DEFAULT_CAPTION_STYLE).replace("'", "\\'")
        filters.append(
            f"[{current_video}]subtitles='{_filter_quote(captions)}':force_style='{style}'[vout]"
        )
        current_video = "vout"
    else:
        filters.append(f"[{current_video}]null[vout]")

    audio_labels: list[str] = []
    voice_side: list[str] = []
    if narration_files:
        narr_labels: list[str] = []
        narr_offset = len(clips)
        for index, (_, start) in enumerate(narration_files):
            label = f"narr{index}"
            delay = max(0, int(round(start * 1000)))
            filters.append(
                f"[{narr_offset + index}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,"
                f"adelay=delays={delay}:all=1[{label}]"
            )
            narr_labels.append(f"[{label}]")
        filters.append(
            f"{''.join(narr_labels)}amix=inputs={len(narr_labels)}:duration=longest:"
            f"dropout_transition=0:normalize=0,volume={voice_volume:.3f},apad,atrim=0:{total:.3f}[voice]"
        )
        duck_count = (1 if source_audio else 0) + (1 if music_index is not None else 0)
        split_labels = ["voiceMix"] + [f"voiceSide{i}" for i in range(duck_count)]
        if duck_count:
            filters.append(f"[voice]asplit={len(split_labels)}" + "".join(f"[{label}]" for label in split_labels))
            voice_side = split_labels[1:]
        else:
            filters.append("[voice]anull[voiceMix]")
        audio_labels.append("[voiceMix]")

    if source_audio:
        filters.append(f"[sfxcat]volume={source_audio_volume:.3f}[sfxBase]")
        if voice_side:
            filters.append(
                f"[sfxBase][{voice_side.pop(0)}]sidechaincompress=threshold=0.025:ratio=3.5:"
                "attack=20:release=300:makeup=1[sfxDuck]"
            )
            audio_labels.append("[sfxDuck]")
        else:
            audio_labels.append("[sfxBase]")

    if music_index is not None:
        filters.append(
            f"[{music_index}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={music_volume:.3f}[musicBase]"
        )
        if voice_side:
            filters.append(
                f"[musicBase][{voice_side.pop(0)}]sidechaincompress=threshold=0.025:ratio=5:"
                "attack=15:release=350:makeup=1[musicDuck]"
            )
            audio_labels.append("[musicDuck]")
        else:
            audio_labels.append("[musicBase]")

    if audio_labels:
        filters.append(
            f"{''.join(audio_labels)}amix=inputs={len(audio_labels)}:duration=longest:"
            "dropout_transition=0:normalize=0,alimiter=limit=0.97[aout]"
        )

    output = _abs(project, doc.get("output") or "final-local.mp4")
    assert output is not None
    os.makedirs(os.path.dirname(output), exist_ok=True)
    command = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[vout]"]
    if audio_labels:
        command += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    else:
        command += ["-an"]
    command += [
        "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", str(doc.get("preset", "medium")),
        "-crf", str(doc.get("crf", 18)), "-pix_fmt", "yuv420p", "-r", str(fps),
        "-movflags", "+faststart", output,
    ]
    return command, output, total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="directory containing local_edit.json")
    args = parser.parse_args()
    project = os.path.abspath(args.project)
    doc = _load(project)
    command, output, total = build_command(project, doc)
    _run(command)
    print(f"FINAL: {output} (~{total:.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
