#!/usr/bin/env python3
"""Disabled legacy A-roll video-edit stage.

A-roll needs a separate non-Atlas STT/video-edit implementation. The active
no-Atlas workflow is B-roll:

  keyframes.py → Codex imagegen → clips.py (Agnes) → audio.py → assemble.py
"""
import sys


def run(*_args, **_kwargs):
    raise SystemExit(
        "aroll_clips.py is disabled in the no-Atlas workflow. Use the standard B-roll "
        "imagegen → Agnes path, or refactor A-roll to a non-Atlas backend first."
    )


if __name__ == "__main__":
    run(*sys.argv[1:])
