#!/usr/bin/env python3
"""
Style bake-off prompt export for the no-Atlas workflow.

Exports ONE representative beat in several candidate collage styles as Codex imagegen
prompts so the agent/user can generate comparison stills manually before committing
the whole film.

Hybrid selection: Claude reads the topic and chooses which idioms to try (names from
styles.STYLE_LIBRARY, or a custom idiom string), matching the topic's era/culture/tone —
don't default to Chinese motifs for a Western topic. Then the human picks by eye.

Usage:
  python3 style_bakeoff.py <project_dir> [style1,style2,...] [beat_index]
Defaults: the 4 Western library styles, beat 0.
Output -> <project>/style-bakeoff/imagegen_style_prompts.json + .md
Then set  "collage_style": "<pick>"  in beats.json, clear old keyframe_url/path, re-run keyframes.
"""
import json
import os
import sys

from styles import compose_collage_prompt, STYLE_LIBRARY, resolve_theme

# candidates are THEME names (full look bundles); Claude picks topic-fitting ones
DEFAULT_CANDIDATES = ["american-retro", "swiss-modern", "punk-zine", "atomic-age"]


def first_shot(beat):
    return beat["shots"][0] if beat.get("shots") else beat


def run(project_dir, styles=None, beat_index=0):
    styles = styles or DEFAULT_CANDIDATES
    with open(os.path.join(project_dir, "beats.json")) as f:
        doc = json.load(f)
    aspect = doc.get("aspect", "16:9")
    beat = doc["beats"][beat_index]
    shot = first_shot(beat)
    scene, bg = shot["scene"], beat.get("bg", "warm ochre")
    tcn, ten = beat.get("title_cn", ""), beat.get("title_en", "")
    out = os.path.join(project_dir, "style-bakeoff"); os.makedirs(out, exist_ok=True)

    prompts = []
    for name in styles:
        tp = resolve_theme(name) or {}              # theme name -> full look bundle
        prompt = compose_collage_prompt(scene, tcn, ten, bg, aspect,
                                        style=tp.get("idiom", name), palette=tp.get("palette"),
                                        type_style=tp.get("type_style"), finish=tp.get("finish"))
        prompts.append({"style": name, "aspect": aspect, "prompt": prompt,
                        "expected_path": os.path.join(out, f"{name}.png")})
        tag = "library" if name in STYLE_LIBRARY else "custom"
        print(f"[{name}] ({tag}) prompt exported")

    manifest_json = os.path.join(out, "imagegen_style_prompts.json")
    with open(manifest_json, "w") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

    manifest_md = os.path.join(out, "imagegen_style_prompts.md")
    with open(manifest_md, "w") as f:
        f.write("# Codex imagegen style bake-off prompts\n\n")
        for item in prompts:
            f.write(f"## {item['style']} → `{item['expected_path']}`\n\n")
            f.write(f"Aspect: `{item['aspect']}`\n\n")
            f.write(item["prompt"].strip() + "\n\n")

    print(f"\nsaved prompt candidates to {out} — generate them with imagegen, review, then set \"collage_style\" in beats.json.")


if __name__ == "__main__":
    proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                           os.path.join(os.path.dirname(__file__), "..", "out", "money-60s"))
    styles = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    bi = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    run(proj, styles, bi)
