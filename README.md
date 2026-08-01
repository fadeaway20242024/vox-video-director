<p align="right"><b>English</b> · <a href="README.zh.md">简体中文</a></p>

# 🎬 Vox Video Director

**Turn one topic into a controlled Vox-style paper-collage video package — concepts, template,
ImageGen still prompts, Google Omni motion prompts, Volcengine/Doubao narration, captions and
local assembly.**

An **agent skill** for a human-in-the-loop workflow. The user generates the Omni video clips and
returns them; the skill creates the clean voice-and-subtitle master with local `ffmpeg`. It is
usable by any coding agent (Claude Code, Codex, etc.).

![License: MIT](https://img.shields.io/badge/License-MIT-black.svg) ![Google Omni handoff](https://img.shields.io/badge/video-Google%20Omni-black.svg) ![Agent Skill](https://img.shields.io/badge/Agent-Skill-d97757.svg)

<div align="center">

https://github.com/user-attachments/assets/ed08d230-7bcb-4b48-a17d-23c079208f9f

<b>▶ "The evolution of Chinese civilization" · 30s</b>

</div>

<table>
  <tr>
    <td width="25%"><a href="https://github.com/user-attachments/assets/216cd62f-6314-456c-94cf-1090b8559a22"><img src="assets/thumbs/football.jpg" width="100%" alt="How football conquered the world"></a></td>
    <td width="25%"><a href="https://github.com/user-attachments/assets/561788b1-5615-4828-b3f8-b24ae5ad7bcd"><img src="assets/thumbs/mexican.jpg" width="100%" alt="Mexican street food"></a></td>
    <td width="25%"><a href="https://github.com/user-attachments/assets/f69f072f-f50a-41ba-9e66-7ed0aae4ddc0"><img src="assets/thumbs/money.jpg" width="100%" alt="A brief history of money"></a></td>
    <td width="25%"><a href="https://github.com/user-attachments/assets/b9ff526f-577f-4acb-aafe-a2519a9b7c1c"><img src="assets/thumbs/silicon-valley.jpg" width="100%" alt="A brief history of Silicon Valley"></a></td>
  </tr>
  <tr>
    <td align="center"><sub>Football history · 60s</sub></td>
    <td align="center"><sub>Mexican street food · 60s</sub></td>
    <td align="center"><sub>A brief history of money · 60s</sub></td>
    <td align="center"><sub>Silicon Valley history · 60s</sub></td>
  </tr>
</table>

<p align="center"><sub><em>▶ more films — click any thumbnail to play</em></sub></p>

---

## What it is

The look is the modern editorial **paper-collage** popularized by Vox explainers: hand-cut paper cut-outs, torn edges, tape, halftone dots, newspaper clippings, bold flat color per beat, big cut-out headlines — brought to life with motion, a narrator, music and captions.

## How it works

One topic flows through one script per stage, all driven by a single `beats.json` per project:

```
topic
  │
  ├─ 1. concepts        draft 3 creative directions                     ◀── GATE 1: pick one
  ├─ 2. template        present 2–3 visual grammars                   ◀── GATE 2: pick the look
  ├─ 3. beat map        write shots, narration and timing              ◀── GATE 3: approve
  ├─ 4. prompt package  GPT ImageGen still prompts + Google Omni prompts
  ├─ 5. user renders    generate Omni clips and return them
  ├─ 6. voice + captions Volcengine/Doubao narration + SRT
  ├─ 7. assemble        local ffmpeg: concat and burn captions (no music by default)
  └─ clean-master.mp4
```

That flow is **B-roll** — a topic in, everything generated. Two more input modalities reuse the same engine:

- **A-roll — legacy/disabled in this fork.** It needs a separate STT/video-edit refactor before use.
- **C-roll — legacy/disabled in this fork.** Use the standard B-roll imagegen prompt path unless anchored-photo generation is refactored manually.

Two ideas make or break the result, and the skill is built around both:

1. **The look is born in the image step.** Each beat is a finished collage *poster*. All the collage DNA (torn paper, cut-outs, halftone, headline text) lives in that image — if the poster isn't a rich collage, nothing downstream saves it.
2. **The motion is added after.** By default an AI video model animates the whole poster (the "living poster" path). For dramatic *piece-by-piece* assembly, an optional local keyframe engine cuts the poster into parts and drives them frame-by-frame (no content filters, pixel-exact — great for real people).

Three human decision gates keep you in control (pick the concept, pick the template, approve
the beat map); Omni rendering and final narration/assembly then follow the approved package.

## Handoff and finishing

| Job | Standard choice |
|---|---|
| Keyframe / collage poster | Codex built-in `imagegen` |
| Image-to-video | User-run Google Omni |
| Narration | Volcengine/Doubao, one consistent voice |
| Captions | Local SRT burned with FFmpeg |
| Music | Optional open-license research or Suno prompt |

## Install

This is an **agent skill** — it works with any coding agent that can read a workflow and run scripts (Claude Code, Codex, …). Claude Code auto-discovers it as a skill; other agents read [`AGENTS.md`](AGENTS.md) → [`SKILL.md`](SKILL.md).

**Option A — from this repo:**
```bash
git clone https://github.com/Alisa0808/vox-director.git ~/.claude/skills/vox-video-director
```

**Option B — from the packaged skill:** download [`vox-video-director.skill`](vox-video-director.skill) and install it via your Claude skills UI.

If narration is generated locally, set the Volcengine/Doubao variables in your private
environment (never commit them):
```bash
export DOUBAO_SPEECH_API_KEY="..."
export DOUBAO_SPEECH_VOICE_TYPE="..."
export DOUBAO_SPEECH_RESOURCE_ID="..."
```

## Quick start

Just ask your coding agent, with the skill installed:

> *"Make me a Vox-style collage video introducing Mexican street food — English, 16:9, 15 seconds."*

The agent will draft 3 concepts and 2–3 templates, then output the approved beat map, GPT
ImageGen still prompts, and Google Omni prompts. You generate the Omni clips and return them;
the agent then creates the Volcengine/Doubao voice-and-subtitle clean master locally.

## Requirements

- A **coding agent** — Claude Code, Codex, or similar
- **ffmpeg** + **ffprobe** (`brew install ffmpeg`)
- **Python 3**
- Volcengine/Doubao credentials only when local TTS is needed

## What's in the box

```
SKILL.md              the skill (English) — the workflow the agent follows
SKILL.zh.md           the same skill in Chinese
AGENTS.md             entry point for non-Claude agents (Codex, …)
references/           the creative engine
  prompt-guide.md       the LOOK layer — prompt structures, vocab & 9 theme presets
  beat-layer.md         14 narrative arcs + hook/pacing + shot patterns
  voices.md             legacy voice notes
  models-and-gotchas.md legacy provider notes (not standard)
  local-edit.md          local FFmpeg JSON schema and verification
  local-engine.md       the advanced element-level motion engine
scripts/              one script per pipeline stage
examples/             ready-to-run beats.json examples
assets/               the showcase film
```

## Credits

Built by **[@alisaqqt](https://x.com/alisaqqt)** — follow for more agent-skill experiments.

Inspired by the collage-ad workflows of **[Stav Zilber](https://x.com/StavZilber)**, **[rom1trs](https://x.com/rom1trs)** and **[Higgsfield](https://x.com/higgsfield_ai)**, and by **[Vox](https://www.vox.com)**'s explainer visual language.

This local fork is configured for a controlled ImageGen → Google Omni handoff, then local
Volcengine/Doubao + FFmpeg finishing. Atlas, Agnes, imgw.cc, and automatic remote video
generation are not part of the standard workflow.

## License

[MIT](LICENSE)
