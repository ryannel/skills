# Community research pass — 2026-08-22

Sources swept: r/StableDiffusion (top month + top week + targeted searches),
r/unstable_diffusion (top month + targeted search), civitai.red (models API,
base-model composition over the last month), plus two primary sources pulled to
confirm claims (bfl.ai/blog/flux-3, Civitai model descriptions).

Everything below is **community-sourced unless marked otherwise** — the two-bar
rule applies: craft is authoritative from the community, hard facts are not.

---

## 1. The headline: the whole ecosystem has reorganised around MiniMax H3

For the past month r/StableDiffusion is *overwhelmingly* H3. Of the top 25 posts
of the month, 18 are H3. That is not hype noise — a genuine tooling stack formed
in three weeks, and almost none of it is in our skill.

### 1a. Acceleration — a three-layer stack the skill does not describe

Our skill says sparse attention is "withheld from this release; open inference is
full-attention only." **That is now false in practice** — the community shipped it.

| Layer | What | Numbers reported |
|---|---|---|
| **Sparse attention (SLA)** | `github.com/PlagueKind/ComfyUI-PlagueKind-Nodes`, designed by pl0x | 5060 Ti 16 GB, 864×1536 ×10 s: PyTorch attn 400 s/it → ComfyKitchen 140 → sparse 0.9 **80** → sparse 0.95 **60**. Sparsity 0.85 ≈ identical to PyTorch; 0.9 default; 0.95 for long/high-res. **Node must be LAST in the chain, directly on the guider/scheduler** — nearly every "it got slower/worse" report is this. Do not stack with cache nodes. Needs recent PyTorch + CU130. |
| **Spectrum** | `github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3` (marres), Chebyshev spectral forecasting from the Stanford/ByteDance Spectrum paper (arXiv 2603.01623) | Euler 34% lower sampler time (1.52×), RES multistep 29.6% (1.42×). 20-step Euler = 11 real transformer evals + 9 forecasts. |
| **ComfyKitchen / int8_convrot + SageAttention** | The quantised runtime path | Getting this wrong is the single biggest silent slowdown — see 1b |

**Spectrum's audio problem is the interesting part, and it is architectural.**
Because H3 packs audio and video into the same transformer sequence with
*different shifted timestep schedules*, a spectral forecast on the video features
feeds back through joint attention and corrupts audio on later evaluations —
symptoms are speech tripping, doubled syllables, distorted reference audio. Fixes,
in order of how the author got there:

1. Split the control: `blend_weight` (video) = 0.50, `audio_blend_weight` = 0.00.
2. That still leaks, because a forecast video feature changes the state the *next*
   real evaluation sees. v0.2.1 adds **`offline_smoothing_replay`** (now default):
   pass 1 captures anchors with both blends forced to 0, pass 2 restarts from the
   original latent and reconstructs the trajectory using past *and future* anchors,
   running zero transformer blocks. Preserves the 45% saving, restores clean audio.
3. Placement matters: model loader → LoRAs/patches → **Sigma Shift** → Spectrum →
   guider/sampler. **Do not run Spectrum and EasyCache together.**

This is a beautiful worked example of the "audio and video are one sequence, and
that fact leaks into everything" thesis the skill already argues.

### 1b. The setup traps that are eating people's speed

- **ComfyUI must be on CU130.** If the startup log does not say `+cu130`, INT8
  ConvRot is not actually engaged even with the int8 loader node — reported
  12–13 min → 4 min on the same job after upgrading. `[community — AI-imagine]`
- **`comfy-kitchen` 0.2.10 fails to import** with `cannot import name
  'TensorCoreConvRotW4A4Layout'` — one ERROR line at startup, then ComfyUI keeps
  working, just slower. 0.2.26 fixes it. **Check before benchmarking anything.**
- **The shipped templates use the `nvfp4` text encoder, which has no hardware path
  before Blackwell.** On 30/40-series use `int8_convrot` instead.
- **SageAttention:** reported to produce pure noise via the `--use-sage-attention`
  launch flag, but clean through the KJNodes *Patch Sage Attention* node set to
  `auto` (11.99 → 9.29 s/it, same seed, no visible difference).

### 1c. Hybrid FL2VA/Ref2VA checkpoints — a real fix for a real split

Ref2VA is visibly worse than FL2VA despite identical architecture. ThatsALovelyShirt
diffed them: divergence is almost entirely in the `*.adaln_proj.*` tensors. Overlaying
ref2va's adaln_proj tensors onto an fl2va base **for blocks 30–49 only** keeps
reference capability while retaining (or improving) fl2va quality. Blocks 0–25
destroy quality — that is where ref2va's problems live.

- Node: `github.com/scottmudge/ComfyUI_MinimaxH3HybridLoader` (zero memory overhead,
  overlays at load time)
- Baked checkpoints: `smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models` — b30-49
  (recommended), b25-49, b20-49 (more reference retention, less quality), b15-49.
- Caveat reported in the wild: the hybrid is more likely to drag a character
  sheet's white background into the video. `[community — erioca]`

### 1d. Long-form video is solved locally, via context chaining

`Comfyui-H3--Motion-Context` (Nikodemon), forked as
`ethanfel/ComfyUI-MiniMaxH3-Contex-Loop`. Carries **22 frames from the previous
clip** as context into the next, plus reference images for identity. Gives a
prepended global prompt, per-scene reroll, per-clip checkpointing, and final
concatenation *including audio*. 1+ minute continuous videos on a 5090 (~10 min
per 15 s clip at 1.5 MP).

Craft that came with it: **plan each scene to end on a still transition beat**
(character standing still, or a close-up) because the ending shot has to connect to
the next scene's opening. Describe *all* the other characters in each scene's prompt
to stop character bleed. Also usable to split one 8 s clip into two 4 s halves for
higher resolution.

### 1e. H3 as a single-image edit model — genuinely new, and it competes

Generate **one frame** and H3 becomes an image editor that reportedly beats Krea 2 +
Identity Edit, Qwen-Image-Edit and Flux Klein 9B on character fidelity, 3D scenes,
mirrors and composition. ~8 s per edit on a 5090.

- Needs a **dedicated image VAE**: `Mamad8/MiniMax-H3-Image-VAE`. With the regular
  VAE, generating 5 frames and picking one gives blurry results; with the image VAE
  at 1 frame it is sharp — but the image VAE *at 5 frames* produces grid artefacts,
  so single-frame is mandatory.
- ComfyUI refused fewer than 5 frames; a patch removed the limit and it has since
  landed in nightly (issue `Comfy-Org/ComfyUI#15644`).
- Settings reported: hybrid b25-49 int8, Comfy Kitchen attention, `sa_solver`/`simple`,
  8 steps, CFG 1, lightx2v turbo LoRA.
- Demonstrated tasks: ageing, body-type change, outfit/location transfer from
  separate references, head replacement, depth-map reposing, geometrically correct
  mirror reflections, three-panel storyboards, multi-person composition, full-body
  character sheets, stylisation.

### 1f. Character reference sheets, generated by H3 itself

`PoopMan333/H3_Character_Sheet_Generator` — feed up to 9 imperfect references, the
workflow appends a fixed "B prompt" that spins the character 360° slowly with no
hard cuts, and assembles a 4- or 6-panel sheet plus the individual frames. Caveats
from the author: it generates 124 frames to use 6; Turbo LoRAs speed it up but cost
prompt adherence; resolution limits detail, so pair the sheet with close-ups for
close shots. The fixed prompt specifies a neutral A-pose — remove that for other poses.

### 1g. Video editing / character replacement — H3 doing SCAIL's job

Darqsat ran 400+ generations to find the prompt shape. The finding: **the
`retention_analysis` block is the main driver, not `detailed_description`** —
describing the action turned out to have no measurable influence.

```
subject_definitions:
<Subject 1> is the woman in <Picture 1> with red hair and a black tank top.
<Subject 2> is the woman originally in <Video 1>.
summary:
[video editing + Audio reuse] The target video is an edited version of <Video 1>.
<Subject 2> is replaced with <Subject 1>, who takes over her pose and movement.
retention_analysis:
<Subject 1>: fully_preserved — face, hairstyle and body from <Picture 1> retained.
             Her clothes are not retained.
<Subject 2>: attribute_transfer — pose, movement and screen position transferred.
detailed_description:
The target video keeps <Video 1>'s original style, lighting and camera work unchanged.
```

`[video editing]` and `[audio reuse]` are pre-trained summary keywords;
`fully_preserved` / `attribute_transfer` are the retention keywords. Anchor each
Subject on something visually large (hair, clothing, screen position) — bare "woman"
loses identity about half the time. Fails when the driving character is barely
recognisable (close-up, partial face, fast motion). `[audio reuse]` works but the
model re-renders rather than copies the audio.

Separately, another user reports subject matching in Ref2V degrades sharply past
5 s, that 12–15 steps latch better than the default 20, and that `ref_image_size`
= MAX beats `match`. `[community — single report, re-verify]`

### 1h. Reference-image craft for Ref2VA

- **Size references by importance**: character ~1000 px, background ~500 px, prop
  ~300 px. `[community — erioca]`
- The model does not know unusual props — supply them as references.
- Known-characters list maintained at `malcolmrey` on HF, v2 dated 2026-08-21.
  H3 has deep pre-trained knowledge of named characters, which is why so much of
  the output is franchise material.

### 1i. Prompting — the official guides are the thing people skip

There are **two** official guides on the HF page: one for T2V/I2V, one for the
Reference model, with different syntax. High-value specifics circulating:

- `<d>[Language in X's voice] line</d>` fixes both wrong-speaker dialogue and
  gibberish. Always name the speaker.
- `[Shot 1] … [Shot 2] At 00:06:000 …` controls cuts *and* pacing. **Never put a
  time code on the first shot.** Omit them all to let the model choose.
- Prompt length must match clip length or everything gets crammed and overlaps.
  Draft at **0.2 MP** to check timing before the long run.
- Structured field names in the wild: `integrated_multimodal_description`,
  `overall_soundscape`, `non_diegetic_music` (write `N/A` for none).

Tooling: `BMB12d3/minimax-h3-prompt-composer` (offline browser app, all five modes,
reusable characters/environments/voices, camera path planner, validity checks) and
`duckyshell/ComfyUI-MiniMaxH3-Prompt-Writer` (in-ComfyUI, local Gemma 4 multimodal,
reads your references, 8–32 GB tiers).

### 1j. Encoder replacement — 15.7 GB → 4.5 GB

`nicolab28/ComfyUI-ClipProj`: Qwen3-VL-4B (or 8B) plus a learned linear projection
into H3's 5120-dim conditioning space, calibrated by plain ridge regression. Works
because 4B and 32B share a tokenizer, so hidden states map position-by-position.
Honest about its limits, which is what makes it citable:

- Cosine ~0.71 (later 0.845–0.86 when calibrated against the DiT's own
  `Linear(5120→5376)` output instead of raw hidden states).
- **Named people come back wrong, not missing** — the 4B *thinks* Scarlett Johansson
  has dark brown hair, so the projection faithfully transmits a wrong memory. Fix:
  describe instead of naming, which spreads identity over a dozen agreeing tokens.
- **Non-English speech breaks.** French comes out half-Spanish. Cosine 0.90 is
  plenty for picture and not enough for phonetics — the audio branch needs far more
  precision than the image branch. Only French tested.
- Ships zero and identity control matrices so you can prove the projection is doing
  work. Exposed a real ComfyUI bug: `SDClipModel.generate()` drops `embeds_info` and
  never calls `build_image_inputs`, so Qwen3-VL image tokens land at linear positions
  with no DeepStack injection — any node on that path will happily describe an image
  it never saw.

Method generalises: **any large text encoder with a smaller sibling sharing its
tokenizer.** Flux.2 (Mistral3-24B), Ideogram 4 (Qwen3-VL-8B) are named candidates.

### 1k. NSFW craft for H3 — the best writeup in the sweep

From r/unstable_diffusion (`nsfwVariant`), and it is model craft rather than smut:

- **Ref2VA over FL2VA for this work** — you can still pass start/end frames, but you
  can also add anatomy references, and start frames behave as strong guides that the
  model adjusts to match the prompt rather than copies.
- Supply a **nude reference** so the model knows what is underneath; close-up anatomy
  references work as a substitute when you don't have a full-body nude of the character.
- **The single biggest source of jank is ambiguous ordering.** H3 assumes actions are
  *sequential* unless told otherwise. Use **"then"** for sequential and **"while"**
  for simultaneous; "and" is ambiguous and reliably produces awkward staggering.
- When the model gets something wrong, **describe it in gratuitous mechanical detail**
  — H3 is prompt-adherent enough to be instructed through its own weak spots. The
  canonical failure is clothing phasing through limbs; the fix is spelling out the
  path ("pulls the skirt down over her thighs, then lets go so it slides down over
  her legs to the floor").
- **≥3 s per garment**, and time-stamp each step. Timestamp position is semantic:
  `at 00:03.000 she lifts her shirt, which exposes her breasts` stamps the *lift*;
  moving the stamp to the end stamps the *exposure*.
- ~**0.8 MP** is the reliability sweet spot; errors rise at both higher and lower
  resolutions. **30 steps beats 20** for cloth physics *and* audio quality.
- Retaining a start frame: write `The scene begins with <Picture 1> as the first
  frame at 00:00.000`, and if that fails add an explicit retention-analysis block.

Also from that sub: 11 languages confirmed in use, Italian works well, and the
undressing/anatomy limits are attributed to data gaps rather than refusal — which
matches what the skill already says.

### 1l. Model-level artefacts now on Civitai

- `RedCraft | REDMIX Hybrid A2A beta1 Lightning 8` — a **MiniMax H3 checkpoint**
  with ~343 k downloads, the single most-downloaded H3 artefact.
- `lightx2v/Minimax-h3-Turbo` — the *official* lightx2v turbo LoRA
  (`minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors`), 4–8 step.
  This supersedes the drbaph conversion story as the default recommendation.
- `Mamad8/MaxiMin-HHH-R2V-ThisIsFine` — detail LoRA.
- Multishot "Seamless Chain" workflows, filmmaking workflows with all speed-ups.

---

## 2. LTX-2.5 shipped — we have zero coverage of the LTX line

Lightricks released **LTX-2.5** on ~2026-08-12 (open weights on HF, pipelines on
GitHub, ComfyUI workflows in `Lightricks/ComfyUI-LTXVideo`). Vendor's own summary:

- **Native multishot** — one generation produces several connected shots holding
  character identity, environment, lighting, voice and style across cuts.
- **Diffusion Fidelity Rendering** — compute allocated per scene complexity instead
  of one fixed compression rate.
- A much better distilled model, explicitly aimed at consumer GPUs.

Community reality check: 0.5 MP / 10 s in **180 s on a 3060**. The predecessor
**LTX 2.3** is still widely used and has the mature IC-LoRA ecosystem:

- `Lightricks/LTX-2.3-22b-IC-LoRA-Clean-Plate` — removes all people/vehicles from a
  clip, leaving a matched empty plate. Used with `LTX-2.3_V2V_ICLoRA_Single_Stage_Distilled.json`.
- `Cseti/LTX2.3-22B_IC-LoRA-CrossView-Warp_v2` + `cseti007/ComfyUI-CrossViewWarp` —
  change camera position/orbit path of an existing clip, defined on an orbit sphere
  rather than by text.
- Union Control IC-LoRA (`LTX-2.5_ICLoRA_Union_Control_Distilled.json`) is the
  current community pick for V2V on 2.5.

**ReDetail** (`Bambushu/redetail`) uses the LTX-2.5 upscaler as a *generative*
video re-render, and it is being used on **MiniMax H3 output** — a genuine
cross-model production pipeline. Hard constraints worth recording: both output
dimensions must divide by **64** (not 32); clip length must be `8n+1` frames or the
tail is silently dropped; **silent clips fail** because the model encodes audio and
video jointly, so add a silence track first. 1.5× is the author's pick over 2×
(243 frames from 768×1408: 7 min/65 GB at 1.5× vs 17 min/80.5 GB at 2×). Cached
conditioning makes the text encoder optional (30.4 → 24.8 GB peak, skips a 15 GB
download) and there is a Mac GGUF build.

Civitai base-model tags now include `LTXV 2.5`, `LTXV 2.3`, `LTXV2`.

---

## 3. SCAIL-2 — a Wan-family model doing character replacement, uncovered

SCAIL-2 is **Wan 2.1-based** (users refer to it as "Wan SCAIL-2"), driven by a
reference image + a driving video, with SAM3-based identity tracking. It is the
community's default for exact motion transfer and character replacement — the thing
H3's Ref2VA does *approximately*.

- Strongest use case is character swap, and the trick is **prepping the reference**:
  edit your actual first frame into the new character (Flux Klein 9B or Krea 2
  Identity Edit LoRA) so the reference already matches the driving video's pose and
  framing.
- Reported to hold object permanence through off-screen excursions, invent plausible
  motion not present in the driving clip, and get transparent-object physics right.
  Weakest at text.
- Known limitation: in multi-person scenes, non-target people pick up an outline/glow.
- Ecosystem: `collbroGTR/comfyui-scail2-infinity`, "SCAIL-2 Unlimited Length"
  workflow, `dvelm/SCAIL-2-Unlimited-Video-Low-VRAM` (GGUF, 8–12 GB, chunked
  chaining for unlimited duration), Wan SCAIL-2 Segmentation Control workflow with
  an Identity Tracker (point/box selection, empty `object_indices` for multi-character),
  Wan2GP support. Works with LightX2V + Pusa LoRAs.
- **Bernini-R** is another Wan-family reference-video-to-video model in the same
  rotation — outfit swap works, face swap reportedly doesn't.

---

## 4. Anima — a 2B anime base model we have never mentioned

`Anima`: **2 billion parameter text-to-image model, CircleStone Labs × Comfy Org**,
anime/illustration focused, explicitly not for realism. On Civitai's most-downloaded
month window it is the **fourth-largest base-model tag (180 entries)**, behind
Illustrious (252), Krea 2 (204) and ahead of ZImageTurbo (137) and Pony (126).
MiaoMiao Harem alone has ~199 k downloads.

Ecosystem worth noting:
- **Cosmos-Reference** — a custom node enabling image conditioning in Anima; needs
  special LoRAs, of which Anima Edit is one. Turns Anima into a character-focused
  image-edit model.
- The "ReStyler" trick (`arthan1011`): stitch a solid-colour block onto the input,
  mask only that block, add `(split screen, multiple views:1.2)` to the prompt, and
  the model fills the empty canvas with the same character in a new pose/style —
  a workaround for Anima Edit being too rigid for pose changes.
- kohya-ss quietly published `anima-lllite-exp-change-2-000007.safetensors`, a
  ControlNet giving Anima broad edit capability. Undocumented.
- Anima is reported to be seed-unstable — some seeds simply ruin a generation.

---

## 5. Krea 2 — the image side's centre of gravity, and our skill is behind

Krea 2 is now the dominant *image* base model in this community, and second only to
Illustrious on Civitai by month volume. New material:

- **Krea 2 Identity Edit LoRA (v1.2)** is the single most consequential addition:
  single-sentence edits that preserve scene, background and lighting — profile turns,
  object swaps, outfit + pose taken from two references, expression changes, no masks
  or inpainting. Reported craft: **one short sentence beats a paragraph.** It is also
  the standard first-frame prep step for SCAIL-2 and the standard undressing tool in
  the NSFW community (paired with an NSFW LoRA such as SNOFS). Limits: posing is
  weak and will shift the face somewhat.
- **LoRA training on 16 GB is possible** — 1152 steps in 67 min at 3.42 s/it, peak
  15,284 / 16,303 MiB, 17.5 GB system RAM, on an RTX 5080. Key corrections from that
  writeup: **train at 1024, not 768** (the technical report says pretraining spanned
  256/512/1024 stages, so 768 was never a trained resolution); `fp8_base` and
  `fp8_scaled` must be set together; `blocks_to_swap` max 26 with
  `block_swap_h2d_only` to avoid host-RAM copy doubling; `timestep_sampling =
  "krea2_shift"` reproduces Krea's resolution-aware schedule per sample and survives
  aspect-ratio bucketing (or `shift` with `discrete_flow_shift = 2.5` at fixed 1024);
  `network_module = "networks.lora_krea2"`, dim/alpha 32, adamw8bit, LR 1e-4.
  **Official `krea/Krea-2-*` repos are gated; `Comfy-Org/Krea-2` is not and carries a
  byte-identical RAW checkpoint.** LoRA bleed without the trigger word is normal and
  the fix is regularisation images, not caption surgery.
- **VAE options have multiplied.** `Qwen Image VAE Sharp` / `Sharp Plus` for Krea 2
  Turbo/Raw — colour-shift-free crisper decode; FP32 build needs `--fp32-vae`.
- **Latent colour vectors**: `muerrilla` extracted exposure/temperature/tint/
  detail/contrast vectors from Krea 2's (Qwen Image) VAE, enabling Camera-Raw-style
  grading *during sampling* in latent space, with dynamic range beyond what the model
  will do on its own. Comfy node announced; also being derived for Z-Image (Flux VAE).
- **Differential Output Preservation** (with a LoKr config) enables **multiple
  character LoRAs in one image** with minimal bleed — class "woman", 1500 steps.
  **Capped at 4 characters**; 5 falls apart. Characters drift toward each other
  (lips especially); emphasise distinguishing features in the prompt.
  **Notably: this failed on Z-Image Base and worked on Krea 2.**
- NSFW ecosystem is large and named: `LUSTIFY!` (371 k downloads, the single
  most-downloaded model on Civitai this month), `FinePorn v3 TURBO`,
  `Moody Krea 2 Mix (uncensored)`, `krea2filterbypass3` LoRA, `MysticXXX_KREA2`.
  The existence of a *filter bypass* LoRA is itself a fact about the base model.
- **Krea 3 is being teased** (krea_ai on X, 2026-08-19).

---

## 6. Image-side items that touch existing skills

- **FLUX 3** (BFL, blog dated 2026-07-23): a *multimodal* foundation model trained
  jointly on image, video and audio, built on "Self-Flow". Video to 20 s with native
  audio, T2V/I2V/V2V/keyframe, multilingual dialogue, agentic chaining into
  multi-shot sequences. **Currently Early Access via API and private weights only.**
  The launch plan promises **"FLUX 3 Dev" — open-weight access to a multimodal
  backbone** — but no date. Preference-rate claims are BFL's own and preliminary
  (vs Grok Imagine 69%, Kling v3 Pro 60%, Seedance 2.0 52%, Runway Gen-4.5 77%,
  Luma Ray 3.2 93%). **This is the correct forward-looking note for the flux-2
  skill; it is not an open model today.**
- **NVIDIA `nvidia/Qwen-Image-Flash`** — 4-step DMD2-distilled Qwen-Image,
  shift-3 trajectory, same base architecture.
- **Seedance 2.5** (ByteDance, API) is the closed comparison point people reach for;
  H3 is reported to hold up well against it at 30 s single-generation.
- **MiniMax Music 3** (`MiniMaxAI/MiniMax-Music3`) with a ComfyUI template — adjacent
  to but distinct from H3; people are dropping Suno for it. Out of scope for the
  suite as it stands, but worth knowing it exists and is not H3.
- **SeedVR2 + RTX Video Super Resolution** remain the community's finishing pass on
  video; ReDetail (LTX-2.5) is the new generative alternative.
- `Qwen-Image-Edit-2511` is the current Qwen edit generation (SatEdit LoRA trained
  against it).

---

## 7. What this implies for the suite

**Updates to existing skills (done in this pass):**

| Skill | Change |
|---|---|
| `minimax-h3` | Large. Sparse attention correction, full acceleration stack, hybrid checkpoints, long-form context loop, single-image edit mode, video-edit prompting, Ref2VA reference craft, prompt tooling, encoder projection, NSFW ordering craft, setup traps |
| `krea-2` | Identity Edit LoRA, LoRA training measurements + the 1024 correction, VAE options, latent colour vectors, multi-character DOP, NSFW ecosystem, Krea 3 signal |
| `character-lora-training` | Differential Output Preservation for multi-character; H3 character-sheet generation as a dataset source |
| `image-production-workflows` | Video-model-as-image-editor, ReDetail, first-frame prep for video character swap |
| `flux-2` | FLUX 3 status |
| `wan-2-2` | SCAIL-2 / Bernini-R as the Wan-family character-replacement path |
| `z-image` | Loses to Krea 2 on Differential Output Preservation; still preferred for likeness in one production report |

**New skills the sweep says are missing** (briefs written, not authored):

1. **`ltx-2-5`** — LTX 2.5 + 2.3, the IC-LoRA ecosystem, ReDetail. Highest priority:
   a top-tier open video model with a mature control ecosystem and zero coverage.
2. **`scail-2`** — or a section in `wan-2-2`. Character replacement / motion transfer
   is a distinct job H3 does not do exactly.
3. **`anima`** — the anime pillar. Illustrious/Pony coverage lives inside `sdxl`;
   Anima is a separate 2B architecture with its own conditioning story.
