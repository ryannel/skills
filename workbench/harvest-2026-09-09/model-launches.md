# Uncovered model launches — sweep of 2026-09-09

**Scope.** Which major image/video model launches the `generative-media` suite does not cover, and which
deserve a skill. Window ≈ 2026-05-01 → 2026-09-09, plus anything earlier the atlas missed. Companion to
`freshness/generative-media-atlas.json`, which covered the *skills* ecosystem (BFL's repo, RunPod's 8th
skill, the H3 LoRA census) rather than the *model* landscape.

**Evidence base.** Everything below is primary: **`Comfy-Org/workflow_templates/templates/index.json`**
read raw (every template carries a `date`, an `openSource` flag and a `usage` counter — a dated vendor
record of native ComfyUI support and how much each model is run); the **ComfyUI commit log** for the date
core support landed; the **Hugging Face API** for licence, date, downloads and likes, plus its
`author=Comfy-Org` index whose repack `createdAt` dates ComfyUI support to within a day or two; the
**Civitai API** with full cursor pagination; and official GitHub READMEs, model cards and vendor blogs.

**Four caveats.** *Template `usage` and repack downloads measure distribution, not practice* — a
`Comfy-Org/<model>` repack is pulled by anyone opening the default template, so where it and the Civitai
LoRA count disagree, trust the LoRA count: it takes work. *Civitai's `metadata.totalItems` is gone* —
the API moved to cursor pagination and 403s a bare Python UA, so `scripts/civitai_census.py` needs
updating; counts here come from full enumeration. *`blog.comfy.org` is now a Substack subscription wall
with no post content*, so a freshness check pointed at it returns nothing silently. And *r/StableDiffusion
and Banodoco went unmeasured* — WebFetch refuses reddit here and the WebSearch budget hit 200/200, so
community sentiment below is **unmeasured, not low.**

---

## Verdict table

| Candidate | Verdict | Why | Source |
|---|---|---|---|
| **Qwen-Image family** (Qwen-Image, Edit-2509/2511, 2512, Layered) | **New skill — first priority** | Apache-2.0, ComfyUI-native since 2025-08, ~3.9M 30-day HF pulls, **1,162 Civitai LoRAs**; the suite routes readers to it and hands them nothing | https://huggingface.co/Qwen/Qwen-Image-Edit-2511 |
| **Bernini / Bernini-R** (ByteDance) | **New skill — second priority** | Apache-2.0 unified video *editing* — a job the atlas ranks nobody at; 108,960 dl/30d and a real derivative layer | https://github.com/bytedance/Bernini |
| **SenseNova U1 / U1.5-8B-MoT** (SenseTime) | **New skill — third priority** | Native 4K, region-controlled edit, ComfyUI **core** 2026-09-01 — and **the NoobAI team published its LoRA trainer** | https://github.com/OpenSenseNova/SenseNova-U1 |
| **HiDream-O1-Image** | **Contested — hold** | MIT, VAE-free, benchmarks over FLUX.2 [dev] and Qwen-Image, core support + musubi trainer — but 47 Civitai LoRAs | https://huggingface.co/HiDream-ai/HiDream-O1-Image |
| **Mage-Flow** (Microsoft Research) | **Contested — hold** | MIT 4B, core support in 3 days, 180,990 dl/30d — but **0 Civitai LoRAs** after seven weeks | https://github.com/microsoft/Mage |
| **FireRed-Image-Edit-1.1** (Xiaohongshu) | **Atlas mention + watch** | Apache-2.0 instruction edit, **2,740 template runs** (2nd-busiest open edit), no LoRA ecosystem | https://github.com/FireRedTeam/FireRed-Image-Edit |
| **GLM-Image** (Z.ai), **ERNIE-Image** (Baidu), **LongCat-Image** (Meituan), **PixelDiT** (NVIDIA), **Boogu**, **Lens**, **LLaDA-Image**, **JoyAI**, **Bria FIBO 1.5** | **Atlas mention** | Open and ComfyUI-reachable; none has a LoRA ecosystem or a job the suite lacks | see below |
| **nvidia/PiD**, **Pony V7**, **HunyuanImage 2.1 / 3.0** | **Atlas mention — three traps** | PiD is **NSCLv1 non-commercial** yet ships a Comfy template; Pony V7's licence bars inference services, >$1M revenue and professional video; HunyuanImage **excludes the EU, UK and South Korea** — a second territory gate beside `minimax-h3` | see below |
| **Wan-Animate-2** | **Already covered — do not re-file** | Apache-2.0, 2026-08-07, 491,911 dl/30d — `wan-2-2` documents it as of today's refresh | https://github.com/Wan-Video/Wan-Animate-2 |
| **SeedVR2** | **Already covered** | Apache-2.0 restoration/upscale; already the suite's upscaler in `image-production-workflows` | https://github.com/ByteDance-Seed/SeedVR |
| 20 hosted launches — Wan 3.0, Qwen-Image 2.0/3.0, FLUX 3, Kling 3.0, Seedream 5.0, Seedance 2.5, Nano Banana 2, GPT Image 2/2.5, Grok Imagine 2.0, Muse Image 1.0 and others | **Atlas mention** | All hosted, no open component; dated list in *Atlas-mention items* below | template index |
| 25 candidates incl. **Z-Image-Edit**, **Z-Image-Omni-Base**, FLUX 3 open weights, LTX-3, Chroma 2, HiDream 2, Illustrious 3, SD4, Veo 4, Sora 3 | **Not released / not found** | Enumerated with evidence in the last section | — |

---

## New-skill candidates in detail

### 1. Qwen-Image — the omission, not the launch

**The largest hole in the suite, and not a 2026 launch at all.** Alibaba's open image line ran
`Qwen-Image` (2025-08-02), `Qwen-Image-Edit` (2025-08-17), `Edit-2509` (2025-09-22), `Edit-2511` and
`Qwen-Image-Layered` (both 2025-12-17) and `Qwen-Image-2512` (2025-12-30). **All Apache-2.0**, confirmed
from the HF API's `cardData`, with no territory, revenue or acceptable-use clause. Then the line stopped.
**Qwen-Image 2.0 launched 2026-02-10 as an API-only 7B** on Alibaba Cloud BaiLian, and
**Qwen-Image-3.0 (2026-07-21, GA 2026-08-05) is closed** — no weights, no licence, no technical report.
Comfy ships 3.0 Pro as a partner node (`openSource: false`, 2026-08-06).

The adoption evidence is not close. Upstream 30-day downloads: Edit-2509 **457,619**, Qwen-Image 313,794,
Edit-2511 302,580, Qwen-Image-Edit 139,172, Layered 82,828, 2512 71,751 — plus repacks at **2,327,318**
and **1,594,223**. Civitai returns **1,162 LoRAs, 192 character-tagged**: above FLUX.2 [klein] 9B's ~670,
an order of magnitude above MiniMax H3's 86 and Ideogram 4's 36, behind only the
Z-Image/Krea/Anima/SDXL 2,000+ tier. Comfy's Qwen templates total **~14,000 runs**, three of them
character workflows built on Qwen-Image-Edit. Trainers: musubi-tuner (2512 and Edit 2509/2511, up to
three control images), ai-toolkit, diffusion-pipe.

**The ranking consequence is sharper than the numbers.** The atlas already concedes, in its own identity
section, that *"the work has moved to edit models, meaning Krea 2 Identity Edit, Flux [klein] 9B and
Qwen-Image-Edit, mixed freely in one job"* — and Qwen is the only one of those three with no skill behind
it. `Qwen` appears roughly 150 times across twelve of the fourteen skills as a peer the reader is assumed
to have. A `qwen-image` skill sits beside `flux-2` and `krea-2` and takes three jobs the rankings leave
open: **instruction-based image editing**, where nothing is ranked first; **identity without training**,
as the third leg of the edit-model trio; and **layered RGBA decomposition**, which no suite skill does at
all. It also gives the licence ladder a genuinely unencumbered edit path, where FLUX.2 [dev] and
Ideogram 4 are not.

**The argument against, fairly:** the open line is frozen, so the skill documents a stable ecosystem
rather than a moving one. That is a reason to write it — it will not rot — and an argument for a
`stable` freshness tier.

### 2. Bernini-R — the video-editing job nobody owns

ByteDance open-sourced the **Bernini** renderer weights **2026-06-01**, the 1.3B variant **2026-06-09**,
the full pipeline **2026-06-11** and **training code 2026-07-13**, all Apache-2.0 (paper 2026-05-22): an
MLLM semantic planner feeding a DiT renderer fine-tuned from Wan, with `Bernini-R` the renderer alone
(1.3B from Wan2.1, 14B from Wan2.2-T2V-A14B, plus a 7+14B pipeline and a `Bernini-v2`). **Six task modes
in one model — t2i, i2i, t2v, v2v, rv2v, r2v** — covering relighting, restyling, subject insertion and
local editing on stills and footage.

ComfyUI native templates landed **2026-06-14**; `Comfy-Org/Bernini-R` pulls **108,960/30d**. Unlike
every other new open model here it has grown a derivative layer — two independent GGUF repacks, a 4-step
LightX2V LoRA set (8,173 dl), an fp8-scaled Wan2.2 build and a motion-enhancer LoRA. People are
quantising it and building on it, which a repack download count cannot tell you. It is H100-class at 14B;
that is what the 1.3B variant is for.

**The ranking consequence:** the atlas's video section ranks *generation* (Wan 2.2 I2V, H3 audio, LTX
multishot) and exactly one *editing* job, SCAIL-2's tracked person replacement. Relighting a clip,
restyling it, inserting a subject, removing an object are not ranked at all, and the suite's only answers
are narrow LTX-2.3 LoRAs. A `bernini-r` skill sits beside `scail-2` with a clean boundary: **SCAIL-2
tracks a person; Bernini re-renders a scene.** It is also Apache-2.0 with no territory clause, so it is a
video-editing path that survives gates 1 and 3 where `minimax-h3` does not. **Both `scail-2` and
`wan-2-2` already name it as "announced, and not covered by this suite."**

### 3. SenseNova U1.5-8B-MoT — and the anime-pool migration behind it

SenseTime shipped **U1 on 2026-04-22** and **U1.5 on 2026-08-19**. The NEO-unify architecture drops both
the visual encoder and the VAE. Modes: t2i, single- and multi-image edit, **region-controlled edit via
masks, bounding boxes and visual markers**, interleaved text-image, **native 4K on U1.5**; ~17 GB peak on
a 24 GB card. **ComfyUI core support landed 2026-09-01** (`Support SenseNova U1.5 (CORE-411)`, #15922),
superseding the custom-node-only state of `OpenSenseNova/ComfyUI-SenseNova-U1` v0.2.0 (2026-08-16).

Adoption: U1 20,939 dl / 291 likes, U1.5 8,283 / 217, plus community GGUFs with real pull (24,987,
12,613 and 4,463 dl across three repos) and official `SenseNova-U1.5-8B-MoT-LoRAs` (2026-08-20).

**What makes it outrank HiDream-O1 on similar download numbers is one ecosystem fact: the NoobAI team
published a LoRA trainer for it** (`Laxhar/sensenova-u1-lora-trainer`, 2026-05-09), and `Laxhar` has
shipped no checkpoint since noobai-XL-Vpred-1.0 in 2024-12. **The answer to "is there a NoobAI successor"
is not a model; it is that the team moved here** — which bears directly on the atlas's anime ranking,
where `anima` and SDXL's Illustrious/NoobAI/Pony pools are the current answer.

**Verify two things first.** The Apache-2.0 claim comes from the GitHub repo, not the gated (401) HF
card; and the parameter count is ambiguous — "8B" in the name against ~18B total for the MoT. No VRAM
prose until both are read directly.

### 4 and 5. HiDream-O1-Image and Mage-Flow — strong on paper, absent in practice

**HiDream-O1-Image** (2026-05-08, MIT) is the HiDream-I1 successor — the line went I1 → O1, so **there is
no "HiDream 2"**. A pixel-level unified transformer with no VAE and no separate text encoder, doing t2i,
instruction editing and subject-driven personalisation to 2048². It claims **GenEval 0.90 / DPG 89.83**
against FLUX.2 [dev]'s 0.87/87.57 and Qwen-Image's 0.87/88.32, with Dev-2604 reported **#8 in the
Artificial Analysis T2I Arena**. ComfyUI core merged 2026-05-12; musubi-tuner added LoRA and full
finetune 2026-06-08; core added its DiffSynth LoRA format 2026-09-03. **Param count is contested** — the
card says 8B, the HF `totalSize` is 35.24 GB over 8 shards, implying ~17.6B at bf16.

**Mage-Flow** (Microsoft Research, 2026-07-22, MIT) ships six 4B checkpoints — Base/RL/Turbo for t2i and
the same three for edit — at native resolution 512–2048, ~18–20 GB peak, Turbo at 0.59 s per 1024² on an
A100, claiming GenEval 0.90. ComfyUI core merged it in **three days** (#15026); ai-toolkit and
SimpleTuner support it.

**Why both are held.** HiDream-O1 has **47 Civitai LoRAs / 10 character-tagged** and ~190 template runs.
Mage-Flow has **zero Civitai LoRAs** and ~130 template runs after seven weeks against a 180,990 repack
download count — the clearest case here of distribution without practice. Both benchmark claims are
vendor-published and unconfirmed, and both land on the axis `z-image` owns, where the atlas's bar is
adoption, not a leaderboard. **Both `microsoft/Mage-Flow*` and `microsoft/Lens` return HTTP 401**, so
their licence text is secondhand. **Re-check in four weeks against the Civitai count and the template run
count; if either doubles, commission the skill** — and commission HiDream-O1 regardless if its arena
placing is independently confirmed.

---

## Atlas-mention items

**Open, ComfyUI-reachable, no job the suite lacks — one line each in the ecosystem map:**

- **FireRed-Image-Edit-1.1** — Xiaohongshu, Apache-2.0, 2026-03-09; 10+ element fusion, strong identity
  retention, ~30 GB. **2,740 template runs** — the busiest open edit template after Qwen Edit 2509 — yet
  zero Civitai LoRAs. Promote it first if a Qwen skill wants a rival.
- **GLM-Image** — Z.ai (SCAIL-2's lab), MIT, 2026-01-08; 16B, edit + style transfer +
  identity-preserving + multi-subject, ~23 GB with offload, 11,137 dl / **1,105 likes**. ComfyUI custom
  node only.
- **Open, ComfyUI-reachable, no LoRA ecosystem:** **ERNIE-Image** (Baidu, Apache-2.0, 2026-04-07);
  **LongCat-Image** (Meituan, Apache-2.0, 2025-12-04, 6B bilingual, strong typography); **NVIDIA
  PixelDiT** (2026-05-25, repack **113,937 dl**, licence `other`); **Boogu Image 0.1** (Apache-2.0,
  2026-06-16, 10B, no named lab); **Lens** (Microsoft, MIT, 2026-05-20, 3.8B); **LLaDA-Image** (Ant,
  2026-08-28 — five days old, watchlist only); **JoyAI-Image-Edit** (JD, template shipped with **0**
  runs); **Bria FIBO 1.5**; and **LTX 2.3 Image** (2026-08-28), an image model inside a video family
  that is `ltx-2-5`'s to note.
- **Three ladder traps, one line each.** **`nvidia/PiD`** is a latent→pixel decoder and 4× upscaler
  dropping into FLUX, FLUX.2, SD3, SDXL and Qwen-Image — **NSCLv1, non-commercial** — and Comfy ships a
  template for it, so it gets picked up innocently. **Pony V7**'s custom licence bars inference services,
  companies over $1M revenue and professional video: a third revenue gate beside Krea 2's $1M and
  LTX-2.5's $10M. **HunyuanImage 2.1 and 3.0** ship under the Tencent Community Licence, which
  **excludes the EU, UK and South Korea** with a 100M-MAU cap — a second territory gate where the atlas
  presents H3's as the only one. (2.1 has zero Civitai LoRAs; 3.0 needs ≥3×80 GB, has no ComfyUI-native
  path and no trainer anywhere.)
- **Utility-only or already covered:** SeedVR2 (the suite's upscaler), Wan-Dancer, WanSong, Wan-Streamer,
  VOID video inpainting, Depth Anything 3, SAM3.

**Hosted-only — the closed frontier.** Dates are the **vendor's** announcement, not Comfy's node
(the two differ by days to weeks). *Image:* **Seedream 5.0 Pro** 2026-07-08 (busiest hosted image in
Comfy at 6,306 runs); **Qwen-Image 3.0** 2026-07-20; **Grok Imagine Image 2.0** 2026-08-07;
**Meta Muse Image + Muse Video** 2026-07-07 — Meta's first, agentic (it invokes search and code
mid-generation); **Nano Banana 2** GA 2026-05-28/29 and Lite 2026-06-30; **GPT Image 2** 2026-04-21 and
**2.5 Flare/Sunburst** 2026-09-08; **Midjourney V8.2** 2026-07-24 and a unified **V8 Edit Model**
2026-08-27; **Reve 2.0** 2026-06-03 and **2.1** 2026-07-09; **Recraft V4.1** 2026-05-14;
**Ideogram P-Image** 2026-07-30. *Video:* **FLUX 3** 2026-07-23 with **FLUX 3 Video** GA 2026-08-04;
**Seedance 2.5** 2026-07-31; **Wan 3.0** beta 2026-08-06; **Gemini Omni Flash** (May 2026) and
**Omni 1.1 Flash** 2026-08-27 — **Google's active video line, which supersedes Veo**; **Kling 3.0 Turbo
+ Omni editing** 2026-06-17; **Luma Ray3.2** 2026-06-09; **Vidu S1** 2026-07-03; **Runway Characters**
2026-07-19 (plus the Solaris and GWM Worlds 2 world models, 2026-09-01/03); **Mirage Avatar X**
2026-07-28; **Pixverse V6** 2026-08-25; **Hunyuan3D 3.0** (Comfy Cloud API only).
Comfy **archived Veo 3 on 2026-08-28** and dropped Veo 2 / 3.0 on 2026-08-26 — the tooling-side
confirmation that the Veo line is dormant.

**One framing line worth putting in the atlas.** Qwen-Image-3.0 went hosted-only with no weights, no
licence and no technical report in the same four months that Ideogram 4, Krea 2, MiniMax H3 and LTX-2.5
all *released* weights. **"Historically open lab" is not a durable prediction**, and the elimination
ladder should be run against the specific checkpoint, never against the vendor's reputation.

---

## Checked and not released / not found

So the next sweep does not redo these. All checked 2026-09-09 against the HF model index, the Comfy
template index and official repos.

- **Z-Image-Edit** and **Z-Image-Omni-Base** — **not released.** Both sit in the Z-Image Model Zoo as
  "*To be released*"; [Tongyi-MAI/Z-Image#163](https://github.com/Tongyi-MAI/Z-Image/issues/163) (opened
  2026-04-04) is still unanswered, and the org holds only Z-Image and Z-Image-Turbo.
- **FLUX 3 open weights** — none. FLUX 3 announced 2026-07-23 (hosted Early Access), **FLUX 3 Video** GA
  2026-08-04, **FLUX 3 Image not shipped**, and "FLUX 3 Dev" named on the roadmap with no date, licence,
  parameter count or repo. **BFL shipped zero open artifacts in the window** — its newest repo of any
  kind is `FLUX.2-small-decoder` (2026-04-06). Treat FLUX 3 open weights as announced-but-unshipped.
- **Wan 2.5 / 2.6 / 2.7 / 3.0 weights** — none. Wan 3.0 entered public beta 2026-08-06, API-only; the
  Apache-2.0 "1.3B + 14B" story circulating for it appears in no Alibaba announcement, and `Wan-AI` on HF
  has nothing past 2.2. The open Wan releases that *did* land are peripheral — Wan-Animate-2,
  Wan-Dancer-14B, WanSong, Wan-Streamer.
- **LTX-3** — not found; LTX-2.5 is current and enormous (1,644,796 dl/30d, 3,189 likes).
  **HunyuanVideo 2 / 3** — the line stops at 1.5. **HunyuanImage 3.1 / 3.5 / 4** — do not exist; the 3.0
  changelog ends 2026-01-26.
- **Chroma 2** — `lodestones/Chroma2-Kaleidoscope` (2026-01-24, Apache-2.0, a FLUX.2-klein-4B finetune)
  exists, but the card reads as explicit work-in-progress, the repo is idle since 2026-03-09 and 30-day
  downloads are 0: **never had a release.** `Kroma` (2026-07-31) is a *Krea 2 derivative* under the
  krea-2 community licence, not Apache.
- **HiDream 2** — does not exist; O1 is the successor line. Frozen lines, newest artefact in brackets:
  **Lumina 3** (`Lumina-DiMOO`, 2025-09-09 — nothing in 2026), **CogVideoX 2** (1.5, 2024-11),
  **Mochi 2** (`mochi-1-preview`, 2024-10), **Open-Sora 3** (v2, 2025-03), **Playground v4** (v2.5,
  2024-02), **Stability SD4** (SD 3.5, 2024-10 — aggregators publishing specific SD4 dates with no
  primary source should be **treated as fabricated**). **OmniGen 3**, **Pusa V2**, **Allegro**,
  **Step-Video**, **Kolors 2**, **Emu 4**, **Skywork UniPic 3**, **Flex.3** — none found.
- **Illustrious 3.0 / 3.5** — **no open weights;** `OnomaAIResearch` stops at Illustrious-XL-v2.0
  (2025-04-18) and v3.x exists only as platform-gated generation, with **Shakker shutting down
  2026-09-30**. **A NoobAI-XL successor** — not released; `Laxhar` has shipped no checkpoint since
  2024-12-22 and has moved to SenseNova U1 (above).
- **Misnamed or non-existent hosted models.** **Ideogram 5** → **Ideogram P-Image**. **Runway Gen-5** →
  Gen-4.5 is still flagship. **Luma Ray 4** → **Ray3.2**. **GPT-image-2** → GPT Image 2 / 2.5.
  **Vidu 3** → the line is Q1 → Q3 → S1. **Veo 4** → Google moved to the Gemini Omni line instead.
  **Sora 3** → the API tops out at `sora-2-pro`. **Krea 3** → preview only, one unfetchable X post, no
  model card. **Midjourney video** → still V1 (2025-06-18). **Moonvalley / Marey**, **Pika**, **Hedra**,
  **Adobe**, **Leonardo**, **Freepik** — nothing datable in the window.
- **MiniMax Hailuo 03 / an H3 successor** — the name does not exist; what shipped are hosted *tiers*,
  **H3 Max** (2026-09-02) and **H3 Max Turbo** (2026-09-04). **A new open audio-video model** — none;
  native audio in open weights remains H3 and LTX-2.5, exactly as the atlas states.
- **A new open character-replacement / motion-transfer competitor to SCAIL-2** — **Wan-Animate-2**
  (2026-08-07, Apache-2.0, 14B + Distilled + a real-time Lite variant, 491,911 dl/30d, ComfyUI template
  the same day). **Already documented in `wan-2-2` as of today's refresh**, task split against SCAIL-2
  included — not a gap. Nothing else in the VACE / UniAnimate / DreamActor family launched in the
  window.
- **ByteDance open *image* weights** — none; `BAGEL-7B-MoT` (2025-05-19) is still the latest. **Ovis
  image-gen** — endpoint empty twice; low-confidence negative, worth one re-check.

---

## What to do next, in order

1. **Author `qwen-image`** via `media-model-skill` — biggest gap, unambiguous evidence, frozen open line
   so it will not rot. Register at `stable` cadence; add it to the atlas suite map, the edit-model and
   identity rankings, and the Civitai census.
2. **Author `bernini-r`** beside `scail-2`, opening the **video editing** axis the atlas lacks.
3. **Author `sensenova-u1`** third — but read the gated HF card first to settle licence and parameter
   count, and file the NoobAI-trainer migration against the atlas's anime ranking either way.
4. **File atlas repairs without waiting for the skills:** the hosted frontier block and its framing line;
   the three ladder traps; and the negative results for Z-Image-Edit and Z-Image-Omni, which `z-image`'s
   watchlist is presumably still carrying as pending.
5. **Fix two pieces of measurement machinery:** `scripts/civitai_census.py` (cursor pagination, browser
   UA) and any freshness check pointing at `blog.comfy.org`.
