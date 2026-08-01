---
name: vox-video-director
description: >
  按可控的人在回路流程制作 Vox 风格纸片拼贴视频：主题→创意→模板→分镜→GPT
  ImageGen 图片提示词→Google Omni 视频提示词。用户返回视频片段后，用火山/豆包旁白、
  SRT 字幕和本地 FFmpeg 输出纯净版；配乐只提供开源音乐方案或 Suno 提示词，不自动调用
  Atlas、Agnes 或远程视频生成。
---

# Vox Video Director（标准中文流程）

这个技能负责创意、模板、分镜、提示词、旁白、字幕和最终本地合成。视频动效片段由用户
拿着提示词去 Google Omni 生成，再回传给技能完成成片。

## 标准流程

```text
主题 / brief
→ 3 个创意方案
→ 用户选择创意
→ 2–3 个模板类型
→ 用户选择模板
→ 分镜头脚本与节奏确认
→ GPT ImageGen 图片提示词 + Google Omni 视频提示词
→ 用户在 Omni 生成片段并回传
→ 火山/豆包统一配音
→ 本地 FFmpeg 拼接、混音、烧录 SRT
→ 旁白 + 字幕的纯净版视频
```

标准路径不调用 Atlas、Agnes、imgw.cc、ChatCut，也不自动调用任何远程视频生成器。
仓库中旧的 provider 脚本只保留作历史兼容，不属于当前流程。

## 1. 主题 → 创意方案

先确认会改变创作方向的信息：主题、受众、时长、画幅、语言、品牌事实和希望的 VOX
气质。信息不足时做合理假设并标明。

输出三个真正不同的方案，每个包含：方案名、核心承诺、受众、情绪弧线、推荐叙事结构
（如 `hook_payoff`、`timeline`、`how_it_works`、`pas`、`bab`、`aida`、`origin`）、视觉钩子、
开场画面和节奏/声音方向。30 秒片优先保证前 2–3 秒有钩子，中段递进，最后只有一个清晰
的收束句。等用户选择后再继续。

## 2. 选择模板类型

模板是视觉语法，不是视频模型。给出 2–3 个选项并说明取舍。可从
`references/prompt-guide.md` 的 `newsprint-editorial`、`chinese-ink`、`wpa-propaganda`、
`swiss-modern`、`punk-zine`、`american-retro`、`atomic-age`、`soviet-constructivist` 中选，
也可以自定义混合。

每个模板要说明：媒介与年代、构图与层次、2–3 个主色、字体/标题处理、动效气质。用户
选定后锁定 style block，所有镜头复用同一套风格语言。

## 3. 分镜确认

阅读 `references/beat-layer.md`。30 秒建议 6–8 个 beat 或 8–12 个镜头，每镜约 2.5–5
秒；一个 beat 可以拆成远景和细节镜头。每个镜头至少写：

```json
{
  "id": "01A",
  "time": "0.0–2.5",
  "purpose": "hook",
  "narration": "这一镜的旁白",
  "on_screen_text": "可选短标题",
  "shot_size": "EST_WIDE | WIDE | MEDIUM | CLOSE | DETAIL",
  "scene": "静态画面主体与分层元素",
  "palette": "本镜主色",
  "camera_move": "一个安全镜头运动",
  "element_motion": "一个连贯的元素动作",
  "image_prompt": "待生成",
  "omni_prompt": "待生成"
}
```

这是必须的确认点：先让用户确认创意、模板、镜头顺序、旁白和时间点，再输出完整提示词。
最后一句变更时，旁白音频和 SRT 必须同步变更。

## 4. GPT ImageGen 图片提示词

图片提示词只描述**静态关键帧**，不要写时间线、音效或动画。调用 ImageGen 时遵循
`imagegen` 技能的内置工具优先原则；项目要用的图片必须保存到项目目录。

每镜采用这个结构：

```text
Use case: illustration-story 或 historical-scene
Asset type: 16:9 VOX collage keyframe
Primary request: <本镜静态画面>
Scene/backdrop: <单色纸张背景与环境>
Subject: <主体 + 2–4 个有清晰边缘的剪纸元素>
Style/medium: mixed-media hand-cut paper collage, editorial print design, torn edges,
  tape corners, halftone dots, newspaper clippings, paper-stencil shapes, real paper shadows,
  printed texture, flat 2D scanned artwork
Composition/framing: <景别、层次顺序、留白、主体位置>
Lighting/mood: flat even scanned light, <情绪>
Color palette: <2–3 个主色>
Materials/textures: <kraft/newsprint/cardstock/ink grain>
Text (verbatim): "<精确短标题>"
Constraints: clean separable edges, stable layout, generous readable space, no watermark
```

规则：风格块全片复用；前景/中景/背景写成分离纸片；标题短且精确；关键字幕后期加；不
要把 Omni 的运动、声音或第二个场景写进图片提示词。

如果已经有 `beats.json`，可以运行 `python3 scripts/keyframes.py <project>`，把图片提示词和
Omni 提示词写回分镜，并导出 `keyframes/imagegen_prompts.*`、`keyframes/omni_prompts.*`。
这个脚本只导出提示词，不调用图像或视频模型。

## 5. Google Omni 视频提示词

视频提示词假设静态图已经作为输入，因此只写运动。每镜只用一个镜头运动和一个主动作，
强调连续、可控、低幅度的纸片运动：

```text
Animate the attached still image into a flat 2D paper-collage motion graphic.
Camera: one continuous <slow push-in / slow pull-out / lateral pan / vertical tilt /
  subtle layer parallax>, eye-level and parallel to the artwork, <very subtle or moderate>
  motion amplitude.
Action: <一个连贯动作>; the named paper cut-out layers <drift / slide / flutter /
  pivot / bob / settle> with visible paper-shadow parallax, then settle naturally.
Look: preserve the exact paper grain, torn edges, tape, halftone, ink colors, layer order,
  and flat 2D dimensionality of the attached still.
Mood and color: <本镜情绪>; preserve the still's limited palette and contrast.
Stability: keep the headline, logo, faces, maps, and all printed lettering sharp, legible,
  and in the same layout for the entire shot; do not redraw or re-letter them.
Shot structure: one single continuous shot, no scene change, no internal cut, no sudden zoom
  snap, and end with the elements settled in place.
```

Omni 规则：不要重复描述整张图或让模型新增物体；不要叠加多个 camera move；优先
`static`、`slow push-in`、`slow pull-out`、`slow pan`、`slow tilt`、`subtle parallax`；避免
`snap`、`slam`、`explosive zoom` 和逐秒指令；标题、地图、脸和 logo 视为锁定层。关键文字
如果被 Omni 破坏，保留画面并在最终 SRT 中后期覆盖。

## 6. 用户返回片段后的本地成片

阅读 [`references/local-edit.md`](references/local-edit.md)，创建 `local_edit.json`，运行：

```bash
python3 scripts/local_assemble.py <project>
```

默认 30 秒为 12 段 × 2.5 秒、1280×720、24 fps。默认交付是**火山/豆包旁白 + 烧录字幕，
不带音乐**。原片音效只有用户明确要求时才保留。可选混音模式：

1. 仅旁白；
2. 旁白 + 原片音效；
3. 旁白 + 原片音效 + 压低的音乐；
4. 旁白 + 音乐、去掉原片音效。

旁白全片使用同一音色。火山/豆包 API Key 只放在环境变量，例如
`DOUBAO_SPEECH_API_KEY`、`DOUBAO_SPEECH_VOICE_TYPE`、`DOUBAO_SPEECH_RESOURCE_ID`；JSON
只引用本地音频文件。旁白文案变更时，重新生成对应音频并同步更新 SRT。颜色跳变只在
对应时间范围做 `color_correction`，macOS 字幕优先使用 `Hiragino Sans GB W3`。

## 7. 配乐交付方式

成片先交付无音乐纯净版，然后让用户二选一：

- **开源音乐方案**：返回曲目页面、许可证、署名文案和建议入点。优先 CC0/CC BY；CC BY
  需要署名，CC BY-ND 未取得额外许可时不用于视频同步。
- **Suno 方案**：返回可复制的 Suno 提示词，包含类型、时代感、配器、速度、情绪曲线、
  强弱起伏和 30 秒剪辑结构。不自动调用 Suno，也不把音乐混入纯净版，除非用户明确要求。

## 验收

用 `ffprobe` 检查时长、画布、帧率和声道；抽查首帧、中段、最后字幕和修色段；听旁白是否
清楚、是否误带音乐；确认最后一句旁白与字幕同时结束。回复时给出纯净版路径、旁白音色、
SRT 路径，以及用户需要的开源音乐或 Suno 提示词。

详细规则：`SKILL.md`、`references/beat-layer.md`、`references/prompt-guide.md`、
`references/local-edit.md`。
