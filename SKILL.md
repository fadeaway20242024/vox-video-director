---
name: vox-video-director
description: >
  Create a Vox-style paper-collage video through a controlled, human-in-the-loop workflow:
  topic to creative concepts, template choice, beat map, GPT ImageGen still prompts, and
  Google Omni image-to-video prompts. After the user returns rendered clips, use local FFmpeg
  plus Volcengine/Doubao narration and SRT captions to deliver a clean voice-and-subtitle
  master. Offer either open-license music research or Suno music prompts; do not auto-run
  Atlas, Agnes, or remote video generation.
---

# Vox Video Director

Use this skill for Vox-style paper-collage explainers, historical shorts, product ads, and
motion-collage films. The standard is intentionally human-in-the-loop: the agent owns the
creative development, prompt package, narration, captions, and final local assembly; the user
chooses the concept/template and generates the video clips in Google Omni.

## Non-negotiable pipeline

```text
topic / brief
  → 3 creative concepts
  → user chooses concept
  → 2–3 visual template options
  → user chooses template
  → approved beat map / shot list
  → GPT ImageGen still-image prompts + Google Omni video prompts
  → user generates clips in Omni and returns them
  → Volcengine/Doubao narration (one consistent voice)
  → local FFmpeg: concat + voice + SRT subtitles
  → clean master: narration + subtitles, no music by default
```

The standard path does **not** call Atlas, Agnes, imgw.cc, ChatCut, or any remote video
generator. Do not silently fall back to those systems. The old provider scripts may remain in
the repository for historical compatibility, but they are not part of this workflow.

## Stage 1 — turn the topic into concepts

Before writing shot prompts, clarify only what materially changes the film: topic, audience,
duration, aspect ratio, product/brand facts, language, and the desired VOX tone. If details are
missing, make a reasonable assumption and label it.

Return **three distinct concepts**, not three wordings of one idea. Each concept contains:

- `concept_name` and a one-sentence promise;
- target audience and the emotional arc;
- recommended narrative arc (`hook_payoff`, `timeline`, `how_it_works`, `pas`, `bab`,
  `aida`, `origin`, or `myth_buster`);
- the visual hook and one representative opening frame;
- a pacing profile (calm / rising / punchy / restrained payoff);
- a short audio direction, without committing to a music track.

For a 30-second piece, prefer a clear hook in the first 2–3 seconds, a rising middle, and a
single payoff line at the end. Ask the user to select one concept before drafting the full shot
package.

## Stage 2 — let the user choose a template

“Template” means a repeatable visual grammar, not a video model. Offer 2–3 options and explain
the trade-off in one line each. Choose from the existing theme vocabulary in
`references/prompt-guide.md`: `newsprint-editorial`, `chinese-ink`, `wpa-propaganda`,
`swiss-modern`, `punk-zine`, `american-retro`, `atomic-age`, `soviet-constructivist`, or a
custom mix of medium, era, palette, typography, and print finish.

Every template choice must specify:

- medium and era (paper collage, photomontage, risograph, woodcut, etc.);
- composition and depth (flat-lay, modular grid, diagonal, radial, negative space);
- limited palette and paper/ink texture;
- headline typography treatment;
- motion character (subtle parallax, page-turn, sliding cut-outs, restrained push-in, etc.).

Do not generate all templates in full. Show the options first; after the user picks one, lock the
style block and reuse it verbatim across all image prompts.

## Stage 3 — build and approve the beat map

Read `references/beat-layer.md` for arc and pacing choices. For a 30-second film use 6–8 beats
or 8–12 shots, normally 2.5–5 seconds per shot. A beat may have a wide and a detail shot. Keep
adjacent shots visually varied, but never ask one shot to contain multiple scene changes.

Each shot record should include:

```json
{
  "id": "01A",
  "time": "0.0–2.5",
  "purpose": "hook",
  "narration": "这一镜要说的旁白",
  "on_screen_text": "可选，尽量短",
  "shot_size": "EST_WIDE | WIDE | MEDIUM | CLOSE | DETAIL",
  "scene": "静态画面中必须出现的主体和分层元素",
  "palette": "本镜 2–3 个主色",
  "camera_move": "one safe move",
  "element_motion": "one coherent motion idea",
  "image_prompt": "待生成",
  "omni_prompt": "待生成"
}
```

This is the **approval gate**. Show the user the concept, template, shot order, narration,
timings, and intended audio mode before producing the final prompt package. If the user changes
the last line, update the narration timing and captions together.

## Stage 4 — write the GPT ImageGen prompts

Read `references/prompt-guide.md` and the Image Generation skill when generating or normalizing
these prompts. The image prompt is a **single still keyframe**; it must not describe a timeline
or ask the image model to animate.

Use this copy-paste structure for each shot:

```text
Use case: illustration-story or historical-scene
Asset type: 16:9 VOX collage keyframe
Primary request: <this shot's static visual idea>
Scene/backdrop: <one bold paper background and the environment>
Subject: <main subject and 2–4 clearly separated cut-out elements>
Style/medium: mixed-media hand-cut paper collage, editorial print design, torn edges,
  tape corners, halftone dots, newspaper clippings, paper-stencil shapes, real paper shadows,
  printed texture, flat 2D scanned artwork
Composition/framing: <shot size, layer order, negative space, subject placement>
Lighting/mood: flat even scanned light, <beat emotion>
Color palette: <limited 2–3 color palette>
Materials/textures: <kraft/newsprint/cardstock/ink grain>
Text (verbatim): "<exact short headline>" (omit this line when no text is needed)
Constraints: clean separable edges, stable layout, generous readable space, no watermark
```

ImageGen rules:

- Write positive, concrete descriptions. Keep one consistent style block across the film and
  change only scene, palette, headline, and shot composition.
- Describe foreground/midground/background as separate paper pieces with visible edges and
  shadows so Omni can infer layers later.
- Keep baked text short and exact; for critical subtitles, plan to add them in post instead.
- Do not put camera choreography, sound, duration, or a second scene in the image prompt.
- Use the built-in ImageGen tool for actual image generation when the user asks Codex to create
  the keyframes. Save project-bound images in the project, not only in the default generated
  image cache.

When a `beats.json` is ready, `python3 scripts/keyframes.py <project>` can persist these fields
and export `keyframes/imagegen_prompts.*` plus `keyframes/omni_prompts.*`. It only writes prompt
manifests; it does not call an image or video model.

## Stage 5 — write Google Omni video prompts

The Omni prompt is image-to-video and should describe **motion only**, assuming the still image is
already attached. Use one camera move and one dominant action per shot. Keep the motion
physically plausible, continuous, and small enough that text and collage edges remain stable.

Copy-paste structure:

```text
Animate the attached still image into a flat 2D paper-collage motion graphic.
Camera: one continuous <slow push-in / slow pull-out / lateral pan / vertical tilt /
  subtle layer parallax>, eye-level and parallel to the artwork, <very subtle or moderate>
motion amplitude.
Action: <one coherent action>; the named paper cut-out layers <drift / slide / flutter /
  pivot / bob / settle> with visible paper-shadow parallax, then settle naturally.
Look: preserve the exact paper grain, torn edges, tape, halftone, ink colors, layer order,
  and flat 2D dimensionality of the attached still.
Mood and color: <beat emotion>; preserve the still's limited palette and contrast.
Stability: keep the headline, logo, faces, maps, and all printed lettering sharp, legible,
  and in the same layout for the entire shot; do not redraw or re-letter them.
Shot structure: one single continuous shot, no scene change, no internal cut, no sudden
  zoom snap, and end with the elements settled in place.
```

Omni prompt rules:

- Do not restate the whole scene or ask Omni to invent a new object; the attached still is the
  source of truth.
- Avoid stacking camera moves. Use one move plus one main element action; richer motion comes
  from layered paper pieces moving together, not from a complicated camera path.
- Prefer `static`, `slow push-in`, `slow pull-out`, `slow pan`, `slow tilt`, or `subtle
  parallax`. Use orbit, roll, whip, or dolly-zoom only when the user explicitly wants an
  experimental take and is willing to re-roll.
- Never use “snap”, “slam”, “explosive zoom”, or a sequence of per-second instructions; those
  often create internal jump-cuts and text warping.
- State the endpoint (“then settles”) so the shot reads as one-way motion instead of a loop.
- Treat critical titles and subtitles as post-production graphics. If Omni distorts them, keep
  the clip and rely on the final SRT overlay.

## Stage 6 — receive clips and make the clean master

When the user returns the Omni-rendered clips, switch to the local source-clip path. Read
[`references/local-edit.md`](references/local-edit.md), create `local_edit.json`, and run:

```bash
python3 scripts/local_assemble.py <project>
```

The verified 30-second default is 12 clips × 2.5 seconds, 1280×720, 24 fps. Use the user's
actual order and durations when provided. The default deliverable is **voice + burned-in SRT
captions, with no music**. Preserve source SFX only when the user requests it; otherwise mute
the clip audio. Available explicit modes are:

- narration only;
- narration + preserved source SFX;
- narration + source SFX + ducked music (only when requested);
- narration + music, no source SFX (only when requested).

Generate narration locally through Volcengine/Doubao, use one voice throughout, and keep API
credentials in environment variables such as `DOUBAO_SPEECH_API_KEY`,
`DOUBAO_SPEECH_VOICE_TYPE`, and `DOUBAO_SPEECH_RESOURCE_ID`. The JSON should reference only
the resulting local audio files. When the final line changes, regenerate that line and update
the SRT in the same pass.

For a localized color mismatch, use a narrow `color_correction` time range; do not globally
grade the film. On macOS, use an installed CJK font such as `Hiragino Sans GB W3` for the SRT.

## Stage 7 — music choices, not automatic mixing

Give the user one of these choices after the clean master is ready:

1. **Open music research:** search the bundled/open-source music sources, return track page,
   license, attribution text, and a suggested in/out point. Prefer CC0 or CC BY. CC BY requires
   attribution; CC BY-ND is not suitable for syncing into video without extra permission.
2. **Suno handoff:** provide a copy-paste Suno prompt describing genre, period, instrumentation,
   tempo, arc, dynamics, and the exact 30-second edit shape. Do not call Suno or mix the track
   into the clean master unless the user explicitly asks.

## Verification and handoff

Before claiming completion:

1. Use `ffprobe` to check duration, canvas, frame rate, and audio channels.
2. Extract and inspect the first frame, a middle frame, the final caption frame, and any repaired
   color segment.
3. Listen for clean narration, correct source-SFX behavior, and no accidental music.
4. Confirm the last narrated sentence and its subtitle end together.
5. Return the clean master path, the selected narration voice/model, the SRT path, and—if asked—
   the separate music research or Suno prompt.

Do not expose API keys or `.env` values in logs, prompts, or the final response.

## References

- `references/beat-layer.md` — arcs, hook timing, shot sizes, and pacing.
- `references/prompt-guide.md` — collage style vocabulary and image/video prompt building
  blocks.
- `references/local-edit.md` — `local_edit.json`, audio modes, captions, color repair, and
  FFmpeg verification.
