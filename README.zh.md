<p align="right"><a href="README.md">English</a> · <b>简体中文</b></p>

# 🎬 Vox Video Director（拼贴动效导演）

**一个选题进，经过创意、模板、分镜和提示词确认，生成 Vox 风格拼贴视频——GPT
ImageGen 图片提示词、Google Omni 视频提示词、火山/豆包旁白、字幕和本地合成。**

一个**通用 agent 技能**。用户在 Google Omni 生成视频片段并回传，技能再用本地 `ffmpeg`
完成旁白和字幕纯净版。任何编码 agent（Claude Code、Codex 等）都能用。

![License: MIT](https://img.shields.io/badge/License-MIT-black.svg) ![Google Omni handoff](https://img.shields.io/badge/video-Google%20Omni-black.svg) ![Agent Skill](https://img.shields.io/badge/Agent-Skill-d97757.svg)

<div align="center">

<video controls preload="metadata" width="100%" src="https://github.com/fadeaway20242024/vox-video-director/raw/main/assets/showcase/zhenghe-yuanboxiaoshu-30s.mp4"></video>

[打开或下载展示视频](assets/showcase/zhenghe-yuanboxiaoshu-30s.mp4)

<b>▶《郑和下西洋：一支舰队》· 30 秒 · 火山/豆包旁白</b>

</div>

<table>
  <tr>
    <td width="25%"><a href="https://github.com/user-attachments/assets/216cd62f-6314-456c-94cf-1090b8559a22"><img src="assets/thumbs/football.jpg" width="100%" alt="足球如何征服世界"></a></td>
    <td width="25%"><a href="https://github.com/user-attachments/assets/561788b1-5615-4828-b3f8-b24ae5ad7bcd"><img src="assets/thumbs/mexican.jpg" width="100%" alt="墨西哥街头美食"></a></td>
    <td width="25%"><a href="https://github.com/user-attachments/assets/f69f072f-f50a-41ba-9e66-7ed0aae4ddc0"><img src="assets/thumbs/money.jpg" width="100%" alt="货币简史"></a></td>
    <td width="25%"><a href="https://github.com/user-attachments/assets/b9ff526f-577f-4acb-aafe-a2519a9b7c1c"><img src="assets/thumbs/silicon-valley.jpg" width="100%" alt="硅谷简史"></a></td>
  </tr>
  <tr>
    <td align="center"><sub>足球如何征服世界 · 60 秒</sub></td>
    <td align="center"><sub>墨西哥街头美食 · 60 秒</sub></td>
    <td align="center"><sub>货币简史 · 60 秒</sub></td>
    <td align="center"><sub>硅谷简史 · 60 秒</sub></td>
  </tr>
</table>

<p align="center"><sub><em>▶ 更多影片 —— 点击任意封面播放</em></sub></p>

---

## 这是什么

风格是 Vox 讲解片带火的现代编辑感**纸质拼贴**:手撕纸片、毛边、胶带、半调网点、报纸剪贴、每一拍一块大胆平涂色、大号剪纸标题——再配上动效、旁白、配乐和字幕,让整张海报活过来。

## 工作原理

一个选题依次流过每个阶段一个脚本,全程由每个项目一份 `beats.json` 驱动:

```
选题
  │
  ├─ 1. 创意       输出 3 个创意方案                         ◀── 决策点 1:选择创意
  ├─ 2. 模板       输出 2–3 个视觉模板                       ◀── 决策点 2:选择风格
  ├─ 3. 分镜       镜头、旁白、节奏                         ◀── 决策点 3:确认分镜
  ├─ 4. 提示词     GPT ImageGen 图片提示词 + Google Omni 提示词
  ├─ 5. 用户生成   在 Omni 生成片段并回传
  ├─ 6. 旁白字幕   火山/豆包旁白 + SRT
  ├─ 7. 本地合成   ffmpeg 拼接并烧录字幕（默认无音乐）
  └─ clean-master.mp4
```

上面这条是 **B-roll**——一个选题进去,画面全靠生成。另外两种输入形态复用同一套引擎:

- **A-roll——本 fork 中为旧流程/默认禁用。** 使用前需要另接 STT/视频编辑服务。
- **C-roll——本 fork 中为旧流程/默认禁用。** 默认请走标准 B-roll 的 imagegen 关键帧流程。

两个关键理念决定成败,技能就是围绕它们搭的:

1. **风格诞生在生图这一步。** 每一拍是一张成品拼贴*海报*,所有拼贴基因(撕纸、剪纸、网点、标题文字)都长在这张图里——图不够拼贴,后面再怎么救也救不回来。
2. **动效是后加的。** 默认由 AI 视频模型把整张海报动起来(「活海报」路径);要那种戏剧化的**零件逐个飞入拼合**,可选的本地关键帧引擎会把海报拆成零件逐帧驱动(无内容审核、像素级精确,尤其适合真人)。

三个决策点让你始终掌控（选择创意、选择模板、确认分镜）；之后按已确认的提示词在 Omni
生成片段，再完成旁白和本地合成。

## 交接与收尾

| 用途 | 标准选择 |
|---|---|
| 关键帧 / 拼贴海报 | Codex 内置 `imagegen` |
| 图生视频 | 用户在 Google Omni 生成 |
| 旁白 | 火山/豆包，统一音色 |
| 字幕 | 本地 SRT + FFmpeg |
| 配乐 | 开源音乐检索或 Suno 提示词 |

## 安装

这是一个**通用 agent 技能**——任何能读工作流、跑脚本的编码 agent 都能用(Claude Code、Codex 等)。Claude Code 会自动把它识别成 skill;其他 agent 读 [`AGENTS.md`](AGENTS.md) → [`SKILL.md`](SKILL.md)。

**方式 A —— 从本仓库:**
```bash
git clone https://github.com/Alisa0808/vox-director.git ~/.claude/skills/vox-video-director
```

**方式 B —— 用打包好的技能文件:** 下载 [`vox-video-director.skill`](vox-video-director.skill),在你的 Claude 技能界面里安装。

如果需要本地生成旁白，在私有环境中设置火山/豆包变量（不要提交到仓库）：
```bash
export DOUBAO_SPEECH_API_KEY="..."
export DOUBAO_SPEECH_VOICE_TYPE="..."
export DOUBAO_SPEECH_RESOURCE_ID="..."
```

## 快速开始

装好技能后,直接跟你的编码 agent 说:

> *「做一条 Vox 风格的拼贴视频,介绍墨西哥街头美食——全英文,16:9,15 秒。」*

agent 会先给出 3 个创意和 2–3 个模板，再输出分镜、ImageGen 图片提示词和 Google Omni
视频提示词。你在 Omni 生成并回传片段后，agent 用火山/豆包配音、烧录字幕，最后合成本地
纯净版。

## 环境要求

- 一个**编码 agent**——Claude Code、Codex 或类似工具
- **ffmpeg** + **ffprobe**(`brew install ffmpeg`)
- **Python 3**
- 仅在需要本地 TTS 时准备火山/豆包凭证

## 目录结构

```
SKILL.md              技能本体(英文)——agent 遵循的工作流
SKILL.zh.md           同一技能的中文版
AGENTS.md             非 Claude agent(Codex 等)的入口
references/           创意引擎
  prompt-guide.md       画面/LOOK 层:提示词结构 + 词库 + 9 套主题预设
  beat-layer.md         14 种叙事弧线 + 钩子/节奏 + 镜头模式
  voices.md             旧音频说明
  models-and-gotchas.md 旧 provider 说明（非标准流程）
  local-edit.md          本地 FFmpeg 配置与验收
  local-engine.md       高级的元素级动效引擎
scripts/              每个管线阶段一个脚本
examples/             可直接跑的 beats.json 示例
assets/               样片
```

## 致谢

作者 **[@alisaqqt](https://x.com/alisaqqt)** —— 关注我看更多 agent skill 实验。

灵感来自 **[Stav Zilber](https://x.com/StavZilber)**、**[rom1trs](https://x.com/rom1trs)**、**[Higgsfield](https://x.com/higgsfield_ai)** 的拼贴广告工作流,以及 **[Vox](https://www.vox.com)** 的讲解片视觉语言。

这个本地版本采用可控的 ImageGen → Google Omni 交接，再用火山/豆包 + FFmpeg 收尾。
Atlas、Agnes、imgw.cc 和自动远程视频生成不属于标准流程。

## 许可

[MIT](LICENSE)
