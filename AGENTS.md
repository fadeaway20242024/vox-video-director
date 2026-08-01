# Vox Video Director — Agent Guide

This repository is an **agent skill**: a self-contained, human-in-the-loop workflow that turns
one topic into a Vox-style paper-collage video package (creative concepts → template → beat map
→ GPT ImageGen still prompts → Google Omni motion prompts → local narration/captions assembly).
It is not tied to any single assistant — any coding agent that can read instructions and run
scripts can drive it.

## How to use it (for the agent)

1. Read **`SKILL.md`** — it contains the concept/template and beat-map approval gates.
   (`SKILL.zh.md` is the same in Chinese.)
2. Before writing prompts, read `references/beat-layer.md` and
   `references/prompt-guide.md`.
3. Work one project at a time under `out/<project>/`, driven by a beat map and an explicit
   handoff package. The user generates video clips in Google Omni and returns them; then use
   `scripts/local_assemble.py` with `local_edit.json` for the final voice-and-caption master.

## Requirements

- `ffmpeg` + `ffprobe`
- Python 3
- Volcengine/Doubao credentials only when generating narration locally (never log them)

## Agent notes

- **Claude Code** auto-loads this as a skill from `SKILL.md`'s frontmatter — just
  ask for a "vox video".
- **Codex / other agents**: follow `SKILL.md` as your instructions; this
  `AGENTS.md` is your entry point.
