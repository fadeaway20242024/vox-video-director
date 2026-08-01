#!/usr/bin/env python3
"""Export the human-in-the-loop ImageGen + Google Omni prompt package.

Codex imagegen is a host-side tool, not a Python API. This script therefore
does not call any image or video model. It writes still-image prompts and
Google Omni image-to-video prompts into beats.json and exports manifests:

  <project>/keyframes/imagegen_prompts.json
  <project>/keyframes/imagegen_prompts.md
  <project>/keyframes/omni_prompts.json
  <project>/keyframes/omni_prompts.md

The user generates the stills and video clips outside this script, then returns
the rendered clips for scripts/local_assemble.py.

Usage: python3 keyframes.py <project_dir>   (default: out/tang-30s)
"""
import json
import os
import sys

from styles import compose_keyframe_prompt, compose_collage_prompt, resolve_theme

IMAGE_MODEL = "codex/imagegen"


def compose_omni_prompt(shot, beat):
    camera = shot.get("camera_move") or "subtle layer parallax"
    motion = shot.get("element_motion") or "paper cut-out layers drift gently and settle"
    feel = shot.get("feel") or beat.get("feel") or "editorial and restrained"
    palette = shot.get("palette") or beat.get("bg") or "the still's limited palette"
    return (
        "Animate the attached still image into a flat 2D paper-collage motion graphic. "
        f"Camera: one continuous {camera}, eye-level and parallel to the artwork, "
        "very subtle motion amplitude. "
        f"Action: {motion}; the named paper layers keep visible paper-shadow parallax and "
        "then settle naturally. "
        "Look: preserve the exact paper grain, torn edges, tape, halftone, ink colors, "
        "layer order, and flat 2D dimensionality of the attached still. "
        f"Mood and color: {feel}; preserve {palette}. "
        "Stability: keep every headline, logo, face, map, and printed letter sharp, legible, "
        "and in the same layout for the entire shot; do not redraw or re-letter them. "
        "Shot structure: one single continuous shot, no scene change, no internal cut, "
        "no sudden zoom snap, and end with the elements settled in place."
    )


def shots_of(beat):
    """Yield (shot_dict, shot_key) for a beat; synthesize one shot if none."""
    if beat.get("shots"):
        for s in beat["shots"]:
            yield s, f"{beat['id']}{s.get('id','')}"
    else:
        yield beat, f"{beat['id']}"   # beat acts as its own single shot


def run(project_dir):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath) as f:
        doc = json.load(f)
    aspect = doc.get("aspect", "16:9")
    doc["image_model"] = doc.get("image_model", IMAGE_MODEL)
    doc["video_handoff"] = "google-omni-image-to-video"
    style = doc.get("style", "painterly")
    theme = resolve_theme(doc.get("theme")) or {}   # theme preset -> full look bundle
    collage_style = theme.get("idiom") or doc.get("collage_style", "american-retro")
    # a registered theme wins; a custom (unregistered) theme may set these at doc level
    t_palette = theme.get("palette") or doc.get("palette")
    t_type = theme.get("type_style") or doc.get("type_style")
    t_finish = theme.get("finish") or doc.get("finish")
    era = doc.get("era")            # only needed for the painterly (per-dynasty) style
    kf_dir = os.path.join(project_dir, "keyframes")
    os.makedirs(kf_dir, exist_ok=True)

    prompts = []
    for beat in doc["beats"]:
        for shot, key in shots_of(beat):
            scene = shot["scene"]
            if style == "collage":
                prompt = compose_collage_prompt(scene, beat["title_cn"], beat["title_en"],
                                                beat.get("bg", "warm ochre"), aspect,
                                                with_title=shot.get("title", True),
                                                style=collage_style, palette=t_palette,
                                                type_style=t_type, finish=t_finish)
            else:
                prompt = compose_keyframe_prompt(era, scene, beat["title_cn"],
                                                 beat["title_en"], aspect)
            shot["keyframe_prompt"] = prompt
            shot["image_prompt"] = prompt
            shot["omni_prompt"] = compose_omni_prompt(shot, beat)
            expected_path = os.path.join(kf_dir, f"kf_{key}.png")
            shot["keyframe_expected_path"] = expected_path
            prompts.append({
                "key": key,
                "beat_id": beat["id"],
                "shot_id": shot.get("id", ""),
                "aspect": aspect,
                "expected_path": expected_path,
                "image_prompt": prompt,
                "prompt": prompt,
                "omni_prompt": shot["omni_prompt"],
            })

    with open(bpath, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    manifest_json = os.path.join(kf_dir, "imagegen_prompts.json")
    with open(manifest_json, "w") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

    omni_json = os.path.join(kf_dir, "omni_prompts.json")
    with open(omni_json, "w") as f:
        json.dump([
            {key: item[key] for key in ("key", "beat_id", "shot_id", "aspect", "omni_prompt")}
            for item in prompts
        ], f, ensure_ascii=False, indent=2)

    manifest_md = os.path.join(kf_dir, "imagegen_prompts.md")
    with open(manifest_md, "w") as f:
        f.write("# Codex imagegen keyframe prompts\n\n")
        for item in prompts:
            f.write(f"## {item['key']} → `{item['expected_path']}`\n\n")
            f.write(f"Aspect: `{item['aspect']}`\n\n")
            f.write("### ImageGen prompt\n\n" + item["image_prompt"].strip() + "\n\n")

    omni_md = os.path.join(kf_dir, "omni_prompts.md")
    with open(omni_md, "w") as f:
        f.write("# Google Omni image-to-video prompts\n\n")
        for item in prompts:
            f.write(f"## {item['key']}\n\n")
            f.write(item["omni_prompt"].strip() + "\n\n")

    print("updated", bpath)
    print("PROMPTS_JSON:", manifest_json)
    print("PROMPTS_MD:", manifest_md)
    print("OMNI_JSON:", omni_json)
    print("OMNI_MD:", omni_md)
    print(f"NEXT: generate {len(prompts)} still(s) with Codex imagegen, then use the matching Omni prompt for each returned still.")


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "out", "tang-30s")
    run(os.path.abspath(proj))
