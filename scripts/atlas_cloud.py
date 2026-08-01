#!/usr/bin/env python3
"""Disabled legacy media client.

This local vox-director fork is configured for the no-Atlas pipeline:
Codex imagegen → imgw.cc → Agnes → local audio → ffmpeg.

This module is intentionally kept only as a compatibility stub so older imports
fail loudly instead of silently calling the retired backend.
"""


class DisabledBackendError(RuntimeError):
    pass


def _disabled(*_args, **_kwargs):
    raise DisabledBackendError(
        "The legacy media backend is disabled in this no-Atlas vox-director fork. "
        "Use Codex imagegen for keyframes, imgw.cc for upload, Agnes for video, "
        "and local audio files for assembly."
    )


submit_image = _disabled
submit_video = _disabled
submit_media = _disabled
transcribe = _disabled
poll = _disabled
image = _disabled
video = _disabled
upload = _disabled
download = _disabled
chat = _disabled
