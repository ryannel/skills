# LTX-2.5 — community evidence (2026-08-22)

Harvested from r/StableDiffusion (top/month + targeted threads), r/unstable_diffusion,
r/comfyui, and the civitai.red models API. **Everything here is community-sourced unless
marked `[vendor]`.** Craft claims carry a named handle; hard facts still need a primary read
(HF model card, `docs.ltx.io`, the licence file).

Raw page text: `../research-2026-08-22/raw/ltx-2-5-reddit-search.txt`,
`ltx-2-5-reddit-comments.txt`, `ltx-2-5-comparison-controversy.txt`,
`unstable-diffusion-search.txt`, `comfyui-search.txt`, `civitai-api-2026-08-22.txt`.

---

## Craft

### The three settings traps everyone hits, in order of how much time they waste

**1. The default VAE OOMs on 12–16 GB cards, and it OOMs at *decode*, not at sampling.**
This is the single most reported first-run failure. `u/irmemon225` (r/StableDiffusion,
"LTX 2.5. on 3060/16gb ram…") could not do 0.5 MP × 5 s on the same 3060/16 GB rig where OP
did 0.5 MP × 10 s in 180 s — and the failure was specifically at VAE decode. The fix, from
`u/matik802` in the same thread, is to swap in
`Lightricks/LTX-2.5/vae/ltx-2.5-video-vae-conv-bf16.safetensors`. `u/irmemon225` confirmed:
*"use video vae conv bf16 fixed for me.. I can generate 1mp 20sec no OOM."* Second-line fix
from `u/GrayingGamer`: a Tiled VAE Decode node.

**Even when it doesn't OOM, decode is the bottleneck.** `u/rinkusonic` (OP): *"Vae decode took
almost twice the time of generating."* `u/Lucaspittol` (3060 12 GB / 96 GB RAM) independently:
*"the tiled VAE decode stage takes longer than actually generating the video, which is very
odd. Reminds me of the last Huyuan video model."*

**2. The stock template's prompt enhancer can cost more than the generation.**
`u/AniZeee`: *"did you disable prompt enhancer? I had to turn it off cause it was literrally
taking 20 minutes… Once I turned it off a 3 sec clip was done in 3 min."* `u/MixDistinct1932`
diagnosed it: *"presumably your rig can't fit the suggested gemma model entirely onto VRAM."*
Note the OP disagrees — `u/rinkusonic`: *"Even on enabled it just took 30 seconds extra"* —
so this is VRAM-headroom-dependent, not universal. `[contested]`

**The enhancer also breaks prompt adherence outright.** `u/Hans-Wermhatt`: *"I'm using the
template default, but with tougher prompts, I will get a completely random video. Turning off
the prompt enhancer (gemma e2b full precision weights) fixes the issue at least partially."*
That is a correctness bug, not a speed one, and it is the more important half.

**3. The stock upscale stage stalls low-VRAM rigs.** `u/2legsRises` went from *"takes forever
on my machine. i have to literally kill the process each time"* to *"disable the upscaling. i
now get 1MP 10 seconds clips in about 1 minute."* `u/Comfortable-You-3881` reaches the same
place from the other direction: *"I usually don't upscale with LTX. I just bump up the base
resolution to 1mp."*

### Attention backend

`u/intLeon` (4070 Ti, 12 GB) is the cleanest datapoint: **15 s at 0.4 MP in under 2 minutes**
with either SageAttention or ComfyKitchen attention. His no-install route:
*"you can use the comfy kitchen attention by adding a `ModelAttentionBackend` node and picking
comfy kitchen attention. It has a very similar speed boost without any build/install."*
Sampler/steps he quotes for the comparable H3 run: `er_sde`, 4 steps, turbo LoRA at 0.75.

`u/mikemend` confirms Lightricks shipped **pre-optimised int8_convrot builds** for ComfyUI.
Watch for the CU130 trap the suite already documents for H3 — it reproduces on the Wan family
(see the SCAIL file), so it is worth checking on LTX too. `[unverified for LTX]`

### Frame and dimension constraints (these are hard, and they fail silently)

From `u/DaLyon92x` (ReDetail author, the most rigorous poster in the sweep):
- **Both output dimensions must divide by 64, not 32.**
- **Clip length must be `8n+1` frames or the model silently drops the tail.**
- **Silent clips fail** — *"because the model encodes audio and video jointly. Add a silence
  track first."*

`u/Cptcrocro` hit the frame rule the hard way when using LTX 2.5 as an upscaler for H3:
*"a 10 seconds video at 24 fps is 240 frames long, but LTX would process only 233 frames,
meaning my generated videos would often lose a few frames at the end, cutting the audio."*
His fix: duplicate the last frame up to the next legal `8n+1` value, then drop the padding
before video combine. For >10 s on a 4090 he swapped the sampler for **LTX Looping Sampler**
(first-party, Lightricks) and reached 20 s without OOM.

### VRAM / speed reality vs claim

| Rig | Job | Time | Source |
|---|---|---|---|
| 3060 16 GB RAM | 0.5 MP × 10 s | **180 s** | `u/rinkusonic` |
| 3050 4 GB VRAM / 16 GB RAM laptop | 0.9 MP × 10 s | 246 s | `u/Pitiful-Clothes3133` `[single source]` |
| 4070 Ti 12 GB + sage/kitchen attn | 0.4 MP × 15 s | <120 s | `u/intLeon` |
| unspecified | 1080p60 × 8 s (i2v) | ~10 min | `u/No_Ratio_5617` |
| 4070 Ti 64 GB | >10 s @ 0.3 MP | **fails at sampling** | `u/Ill_Health_4996` `[single source]` |
| 3090 / 128 GB RAM | LTX-2.3 **1.1 Dev** (non-distilled) | *"I absolutely cannot run"* | `u/Comfortable-You-3881` |

The dev/non-distilled model is a different hardware class from the distilled one.
`u/Comfortable-You-3881`: *"the Dev model was released with the expectation that people were
running workstation cards or at the bare minimum, something the likes of a 5090."*
`u/b-monster666` on the distilled: *"Even an 18GB distilled might be a bit chonky for 16GB
cards, leaving this in the 'prosumer' tier."*

### The smearing problem, and the community fix

`u/SillyLilithh` (1 day old at harvest, 165 pts) is the newest and most actionable craft in the
LTX space: *"LTX 2.5 has a known smearing problem. It's really bad, and makes almost every
output of LTX completely unusable."* She ported the **jerk-oracle** nodes from a MiniMax H3
node pack over to LTX 2.3/2.5:

> *"the jerk oracle creates new 'hold' frames based on the amount of smearing per frame. Some
> frames have larger 'hold' amounts. We pipe that into a new sampling step, which improves the
> smearing. After the sampling is finished, we chop off the added 'hold' frames so that we are
> left with just the original frame count, but now these frames actually have better
> consistency."*

Her verdict: *"This makes it look like a generational improvement, closing the gap on MiniMax
H3 in terms of temporal stability (ain't no way in hell its ever matching the instruction
following or general capabilities of H3 lmao)."* `[single source]` — nobody had reproduced it
within the first day.

### A structural theory of where LTX-2.5's speed comes from

`u/V4nKw15h` (13 pts), unrebutted: *"LTX 2.5 genuinely looks like Minimax with a bunch of
caching optimisations and a low number of steps. Stuff like Easy Cache or Spectrum causes these
types of animation skips and jerkiness because it's actually skipped steps in the motion
generation phase. Seems like LTX 2.5 is finding it's speed via similar methods. I'd rather have
the choice to enable the optimisations manually."* `u/CurrentNew1039` offers the escape hatch:
*"You can try ltx 2.5 undistilled version, but we have to sacrifice this speed thing."`
This is the best available explanation for the "missed one step" walk/run artefact
`u/rinkusonic` reports (and which Wan 2.2 also had).

---

## Prompting (with quoted real prompts)

**LTX-2.5 is a natural-language / timestamped-scene model, and the community writes it the
same way it writes MiniMax H3 — very long, structurally sectioned, with explicit time ranges.**

The most complete posted prompt run through LTX (2.3, against H3 with the *identical* text) is
`u/Cold_Zone332`'s Pikachu-vs-Charizard fighting-game prompt. It is ~1,000 words and organised
as: `VISUAL STYLE` → `CORE MOVEMENT RULES` → `SCENE OBJECTIVE` → `TIMED GAMEPLAY ACTION`
(`[0.0s–2.5s]`, `[2.5s–5.5s]`, …) → `ANIMATION BEHAVIOR` → `CAMERA` → `AUDIO` → `CONSTRAINTS`.
Full verbatim text in `../research-2026-08-22/raw/ltx-2-5-reddit-search.txt`. Excerpt of the
timestamp register:

> *"[5.5s–7.5s] Charizard goes into a full shock reaction animation. Electricity crackles all
> over his body. He convulses, shakes violently, jerks backward, and briefly flashes with a
> stylized arcade electrocution effect. His body stiffens and reacts as if being stunned by the
> electric damage. His health bar drops noticeably. Add hit sparks, brief screen shake, and a
> powerful impact feel."*

His conclusion after running it both ways: H3 won. That prompt is therefore evidence of *the
register LTX expects*, not of LTX's strength.

**Short prompts + an LLM enhancer is the other live pattern.** `u/intLeon`'s base prompt before
enhancement was one line — *"She says; 'dad I'm in trouble, again!' and disappears with a
teleport effect.."* — expanded by `gemma 4 12b` inside ComfyUI via qwenvl nodes + llamacpp.
Given `u/Hans-Wermhatt`'s adherence problem with the *stock* enhancer, an external, fully-loaded
enhancer looks like the safer version of this pattern.

**Timestamps in prompts do land.** `u/Moarkush` (testing H3, but writing about what LTX kept
failing at): *"Wrote actual timestamps into the prompt and it more or less hit them. Scene
changes landed where they were supposed to… This is the thing LTX kept almost doing and
fumbling."* That is the multishot claim's exact contested surface.

**Camera is a known weakness.** `u/corod58485jthovencom` (PT): *"Essa câmera fixa do LTX e um
grande problema, não consegue gerar aquela sensação de câmera amadora ou mudança repentinas que
dão maior sensação de realismo"* — LTX's fixed camera can't produce the amateur-camera feel or
sudden changes that read as realism. He asks explicitly for Flux.3/MiniMax-style amateur camera
training.

---

## Ecosystem

### The decisive fact: the LoRA ecosystem is on 2.3, not 2.5

Civitai, 2026-08-22, `baseModels` filter, sorted by downloads:

| Base-model tag | Items returned | LoRAs | Checkpoints | Workflows |
|---|---|---|---|---|
| **LTXV 2.5** | **20 total** | **3** | 5 | 12 |
| **LTXV 2.3** | 100 (page cap) | **98** (LoRA-only query) | 8 | 49 |

A 2.5-only skill would be wrong for most existing rigs. The LoRA library is entirely 2.3's:
`LTX 2.3 - Enhancers` (vrgamedevgirl, 18k), `Furry Enhancer Video` (freek22, 18k),
`EditAnything` (NRDX, 7k), `Amateur Hour - LTX 2.3` (QualityControl, 5.4k),
`LTX2.3-IC-LORA-Dual-Character` (MaqueAI, 5.2k), `Cameraman IC-LoRA for LTX2.3 22B` (Cseti,
2.9k), `Camera Controls [LTX-2.3]` (ReltivlyObjectv, 2.8k), style LoRAs (Pixar CGI Toon,
Retro 90's Anime, Claymation, Fantasy Realism), and — worth flagging for the conditioning-class
section — **`LTX-2.3 Whisper / Soft-Spoken Audio LoRA` (plz12345, 1.9k), i.e. LoRAs can target
the audio branch, not just the video one.**

**Forward compatibility is claimed but soft.** `u/ArttTaku`, "Most LTX 2.3 Loras work on LTX
2.5": *"Pretty much confirmed by the devs."* `[single source, screenshot-based]` — 75 comments,
no clean confirmation in-thread. `[vendor]` `u/ltx_model` did confirm the adjacent claim:
*"the existing LTX Trainer works with LTX-2.5."*

### Checkpoints and quants

`REDGraft LTX 2.5 老同学 Fast 2K | sulphur2 ported` (AiMetatron) — **148,130 downloads**, an order
of magnitude above everything else tagged LTXV 2.5, including Civitai's own official
`LTX 2.5` upload (1,611). Also `LTX-2.5 22B, cut down to fit your card` and a
`Joy-LTX 2.5 Distilled GGUF / INT8 / NVFP4 / W4A8 / Mac` family (joeygambino), plus
`Joy-LTX 2.5 — One Take or a Seamless Multishot` (the only workflow whose title targets the
multishot feature directly). `Sulphur 2 Base` (FusionCow) and `LTX2.3 FP4` on the 2.3 side.

### V2V — the current community pick

`u/Interesting_Room2820` ("WEEKENDDDDDDDD 222…", 235 pts, 2 days old): *"After running a bunch
of tests, the one I'd recommend right now is
`Lightricks/ComfyUI-LTXVideo/example_workflows/2.5/LTX-2.5_ICLoRA_Union_Control_Distilled.json`.
It's been the most consistent one I've tried for V2V so far."* First-party workflow, community
verdict.

### ReDetail — LTX-2.5 as a generative video re-render

`u/DaLyon92x` / `Bambushu/redetail` (280 pts). The constraints are already in
`image-production-workflows`; the numbers worth carrying:

- 243 frames from 768×1408: **1.5× = 7 min, peak 65 GB; 2× = 17 min, peak 80.5 GB** (5090).
- Author prefers 1.5×: *"On skin most of that extra is invented, not recovered. Faster render,
  less made up texture."*
- **Cached conditioning** update makes the text encoder optional — ships pre-computed at 26 KB,
  skips the 15 GB download, peak VRAM **30.4 GB → 24.8 GB**.
- **Mac build exists** (`ReDetail_LTX25_upscale_MAC.json`), GGUF transformer, no text encoder,
  ~17 GB total. M5: 33 frames 640×384 → 1280×768 in 4.4 min; *"roughly 6x slower than a 5090,
  not the 30x I was expecting."* A 10 s clip lands ~34 min at 2×, ~19 min at 1.5×.
- Honest limitation: *"It invents fine detail. In every test with one person it added freckles
  that weren't there… Logos, numbers and text are all fair game."*

### LTX as the *finishing* stage for other models — the dominant real use

This is the strongest signal in the whole LTX sweep. Almost every high-scoring LTX post in the
last month is someone using LTX to upscale or outpaint **MiniMax H3** output:

- `u/Cptcrocro`, 159 pts — LTX 2.5 ×2 upscaler for H3 on a 4090, from Peter Duncan's
  `MINIMAX_H3_LTX2.5_Upscaler_v1.json`.
- `u/alisitskii`, 208 pts — H3 (~3:25 per 5 s @ 736×736, 20 steps) + LTX 2.3 ×2 spatial upscale
  (~2:05, 3 steps) on a 4080S 16 GB.
- `u/spiderofmars` (r/comfyui) — **SCAIL 2 + LTX 2.3 outpaint** to solve mushed faces (see the
  SCAIL file; the technique is LTX-side).
- `u/DaLyon92x` — ReDetail, above.
- And the reverse now exists: `u/lumos_ai`, *"MiniMax H3 Model Copied LTX 2.5's Best Feature"*
  — a latent-upscaler node bringing LTX-2.5-style low-res-pass-then-3-step-neural-upscale to
  H3, 10–11 min → 3–4 min.

Interface support: **Mix Studio v1.2.4** (blackmixture, GPL-3.0) ships LTX 2.5 t2v / first-frame
/ first-and-last-frame with synced audio and LoRA stacks, plus an "LTX Director Mode" built on
the LTX Director nodes (timelines, keyframes, extension, audio). **ComfyUI-Stimma** 1.0.13 adds
*"text-to-video with audio, image-to-video with optional end frame, extend, loop, stitch, up to
10 LoRAs."* `u/nghtdrp`'s SnapMoGen motion-library node drives LTX, SCAIL 2 and Bernini from a
searchable mocap browser.

---

## Characters & identity

**LTX-2.5 has no reference-to-video mode, and that is the reason people leave it.** This is the
most consistent identity finding in the sweep.

- `u/rk1213`: *"multishot is awesome but unfortunately need to stick with H3 for native
  references. Otherwise would use this as default."*
- `u/RelationshipSea2360`: *"Do you know when Ref2Vid will be available?"* — unanswered by the
  vendor account.
- `u/Concheria`: *"Does it work with character references?"* — unanswered.
- `u/No_Damage_8420`: *"If your model can do ref2vid that's it. That would be killer."*

**Face drift is not fixed.** `u/Inside-Cantaloupe233`: *"ONE QUESTION! - FACE DRIFT!! DID THEY
FIX IT? NO? OK THX."* → `u/aziib`: *"no lol"*.

**Multi-character scenes break character LoRAs.** `u/sacx05`: *"Minimax prompt adherence and
identity lock are miles ahead of LTX 2.3 even including character loras since multiple
characters in a scene would fuck it up."* `MaqueAI`'s `LTX2.3-IC-LORA-Dual-Character` (5.2k
downloads) is the community's answer to exactly this, and it is a 2.3 asset.

**The defection story is worth quoting in full**, because it is the multishot claim's real-world
test. `u/Dry-Statistician-684` (329 pts):

> *"I've been using LTX 2.3 for quite some time but as soon as I wanted to make just a few
> simple shots of the same character with cuts, LTX wasn't even remotely capable of that. Which
> left me so frustrated I eventually gave up on it completely. But when I tried Minimax
> everything has changed. Reference to video model is something else."*

Against that, `u/hidden2u` on 2.5: *"Just want to say thank you, the multi shots maintain
consistency a lot better."* `[single source]` — the only positive multishot report in the sweep.
`[contested]`

**Character LoRA training on 2.5 is an open question.** `u/Yeti-Bhanot`: *"the rl post-training
is the part i'm most curious about. does it change how lora training behaves? i had decent luck
with small curated sets on 2.3 at the usual step counts, wondering if the new base pushes back
more."* Unanswered by the vendor.

---

## NSFW

**LTX **2.3** is the NSFW workhorse; LTX 2.5 has not appeared in adult use at all yet.** Every
high-scoring adult LTX post in r/unstable_diffusion in the last month names 2.3:

- `u/BarelyAI`, *"The magic of LTX 2.3, fantastic realism"* — **1,208 points**, the single
  highest-scoring hit in the NSFW sweep. Also *"Hotwife picked up and fucked at the casino —
  made with a combination of LTX, WAN, Krea and Ideogram"* (245) and *"My 32 year old hotwife
  takes two cocks for the first time (LTX + KREA)"* (72).
- `u/Able-Pear-783` — a seven-post series of ~50-second shorts, every one credited
  *"使用工具:Krea2 + Ltx-2.3"* (Krea 2 + LTX-2.3).
- Civitai carries `LTX2.3 All in one [SFW / NSFW] - LTX Director + ID` (LatentHeart, 30,553
  downloads — the most-downloaded LTX 2.3 workflow of all), plus `Furry Enhancer Video`
  (18,457) and `Amateur Hour - LTX 2.3` (5,414).

**Censorship of 2.5 is contested, and nobody has actually tested it.** The argument is entirely
about 2.3's behaviour plus vendor priors:

- `u/CaptainAnonymous92` (25 pts): *"with H3 coming out and being pretty much uncensored, any
  video models that come out after it open will be compared to it and if they're censored out
  of the box like most of the others are then that might be seen as a dealbreaker."*
- `u/Beneficial_Toe_2347` (19 pts): *"2.3 literally didn't understand what humans look like."*
- `u/DoctaRoboto`: *"this model is dead on arrival. I still remember my anime test video with
  2.3, just a girl in a ballerina costume dancing...it was the stuff of nightmares."*
- `u/JesusShaves_`: *"Any censorship at all, and I mean any and this flavor of ltx will be
  ignored."*
- **Counter-argument, and the one that matters:** `u/TopTippityTop`: *"It works with 2.3 loras,
  so in a way it is uncensored from the gate 😂"*
- `u/NeuroPalooza` widens it beyond nudity: *"I would be shocked if it was remotely as
  uncensored (I mean in terms of IP, not just NSFW) as H3."*

The vendor account (`u/ltx_model`) answered several technical questions on that thread and did
**not** answer any of the censorship or licence ones.

Adjacent, from the r/unstable_diffusion H3 material and relevant to any LTX prompting guide:
`u/Thorozar` found that **stripping `<d>` tags removes audio glitches at clip start** in H3 —
worth checking whether LTX's dialogue tagging has the same failure, since both models encode
audio and video jointly.

---

## Positioning vs covered models

**vs MiniMax H3 — the community verdict is lopsided and the vendor made it worse.**

`u/Obvious_Set5239` (210 pts): *"LTX is not even close, Minimax dwarfs it."*
`u/MISEMUNJIOZONE`: *"Minimax h3 generates so much better quality and accurate video of i2v than
ltx2.5."* `u/SanDiegoDude`: *"it's 2.3 with some lipstick on it."*
`u/Codeman119`: *"LTX 2.3 only worked about 30% of the time for me and with minimax H3 it works
about 95% of the time."*

The defence exists and is coherent — `u/glusphere`: *"its like shitting on someone releasing a
4B model because a 27b model exists in the same space!"* — and speed sometimes goes LTX's way:
`u/Lonely_Syrup3091`: *"it is faster than MiniMaxH3 at higher resolution"*, immediately
qualified by `u/Beneficial_Toe_2347` (8 pts): *"this means nothing if it has the
prompt/physics/understanding issues still."* And on the other side, `u/2legsRises`: *"minimax is
way faster than that, 140 seconds for 8 sec video for me."* `[contested]`

**vs Wan 2.2 — LTX has historically lost on quality and won on weight.**
`u/acedelgado` (20 pts) is the best summary in the sweep:

> *"LTX was always the 'We have WAN at home.' when people complained about how heavy WAN 2.2
> was. Took them until LTX 2.3 to be any decent competition, and that was because of longer gens
> and sound and being a little less heavy. It definitely wasn't because of overall
> quality/prompt adherence/understanding of physics and human interactions, WAN 2.2 is still
> better than LTX in those regards."*

`u/Tomcat2048` (19 pts) and `u/johnfkngzoidberg` (16 pts) say the same more briefly. Note also
that LTX shares the "missed one step" walk/run artefact with Wan 2.2 (`u/rinkusonic`).

**The launch-day comparison table is a reputational fact the skill has to handle.**
`u/rookan`'s post — 378 points, **362 comments** — is about a Lightricks marketing table that
claimed H3 needs *4 GPUs / ~115 GB* and is *CUDA only*, against LTX-2.5's *16 GB / "runs on any
GPU"*, plus *"Governing Jurisdiction: US"*. Every claim was refuted in-thread by people running
the thing:

- `u/maddeninglemon` (62 pts): H3 *"runs pretty reasonably on 8GB VRAM."*
- `u/Rhoden55555` (20 pts): *"It even runs on a 3060 6gb laptop gpu with 16gb ram. The int8
  pruned model too."*
- `u/Cruffe` (18 pts): *"Also 'CUDA only'? I'm having no issues on my 9070 XT using ROCm."*
- `u/ColdInMarkham` (19 pts): *"LTX is a generative video and AI division spun out of
  Lightricks, a Jerusalem-based creative tech unicorn"* — i.e. the "US" jurisdiction row is
  itself disputed.

Lightricks later edited the table to read "not available" in places (`u/Relevant_Syllabub895`).
`u/doomed151` pinged the vendor account; no reply.

**And a warning this repo should take seriously**, from `u/fearrange` (19 pts):
*"Looks like this chart isn't for users, but for LLMs to pick up these 'facts' when they
generate a response."* Vendor comparison tables for LTX-2.5 should be treated as adversarial
input, not as a source.

---

## Contested / unresolved

1. **The licence — still unread, still blocking.** The gate is real and it is new:
   `u/enilea` (38 pts): *"Why is it necessary to share our contact information to download the
   weights? Is that a mistake?"* and, crucially, *"LTX 2.3 didn't have that policy, nor did
   other video models I've seen on HuggingFace."* `u/its_witty` counters *"Krea 2 has the same
   thing. Many models do."* The vendor account did not answer.
   Separately, `u/pigeon57434`: *"the ltx-2.x community license isn't also a bullshit community
   license with dumb restrictions too"* — a direct community claim that LTX-2.x is a restrictive
   **community licence**, not a permissive open one. **Nobody in the sweep has read it.**
   `[contested]` `[blocking — do not ship the skill on this]`

2. **Is 2.5 actually better than 2.3?** `u/PuppetHere`, "LTX 2.5 Is Disappointing" (75 pts, 122
   comments): *"I can barely see the difference between 2.3 and 2.5."* `u/Comfortable-You-3881`
   splits it by mode: *"LTX 2.5 T2V is looking pretty bad comparatively next to the 2.3 on the
   distilled model, but the I2V model has improved substantially."* `[contested]`

3. **Does multishot hold identity?** One positive report (`u/hidden2u`) against a documented
   failure on 2.3 (`u/Dry-Statistician-684`) and no side-by-side. Unresolved.

4. **Where the speed comes from.** `u/V4nKw15h`'s "it's caching/step-skipping in the distill"
   theory is unrebutted but also unverified — and it would explain the walk/run artefact.
   `[single source]`

5. **Open weights vs open source.** `u/cyborgsnowflake` (28 pts) asked whether the training
   stack is released or only the weights, and warned against letting the terms drift. No vendor
   reply.

6. **Apple/AMD support.** `u/blackmixture` (Mix Studio): *"LTX 2.5 and MiniMax H3 rely on
   NVIDIA-specific model weights, so they are not available on Apple Metal or AMD ROCm yet."*
   Directly contradicted by the ReDetail author shipping a working Mac GGUF LTX-2.5 build and by
   `u/Cruffe` running H3 on ROCm. `[contested]`

7. **RoPE limit unchanged from 2.3?** `u/nazgut` asked; unanswered.

8. **Realtime streaming.** `u/CelebrationBoth9537`: *"Has anyone figured out how to reliably use
   the realtime streaming video gen they claim to have? I think iv been trying for like a few
   hours now."* No answer. Vendor claims it; nobody has reproduced it. `[contested]`

9. **What the "world model" framing means.** `u/Arawski99` asked for a definition; `[vendor]`
   `u/ltx_model` deflected to a blog post (`ltx.io/blog/world-models-vs-llms`) and said the
   omission was deliberate: *"This video was made specifically for /StableDiffusion, and the
   people here care far more about video generation than anything else."*

**One clean vendor technical statement worth keeping** `[vendor]`, on how the pixel-space
decoder differs from NVIDIA PiD — `u/ltx_model`:
> *"Related idea, different thing: PiD decodes and upscales as a separate module, whereas ours
> is the video VAE's decoder itself pixel-space diffusion, no upscaling stage."*

`u/glusphere` reads this as *"The Pixel space Auto Encoder is also probably a first in the Video
models?"* and expects an **MoE in LTX 3**. `[single source, speculation]`

---

## Sources

Reddit (all read via old.reddit.com):
- `r/StableDiffusion/search?q=LTX+2.5&restrict_sr=on&sort=top&t=month`
- `r/StableDiffusion/comments/1vlqy46/ltx25_is_here/` — u/ltx_model, 993 pts, 256 comments
- `r/StableDiffusion/comments/1vlwfvj/ltx_25_on_306016gb_ram_05mp_10_second_video_took/` — u/rinkusonic, 83 comments
- `r/StableDiffusion/comments/1vllqxs/ltx_25_comparison_table_vs_minimax_h3_is_a/` — u/rookan, 362 comments
- `r/unstable_diffusion/search?q=SCAIL+OR+Anima+OR+LTX&restrict_sr=on&sort=top&t=month&include_over_18=on`
- `r/comfyui/search?q=SCAIL+OR+Anima&restrict_sr=on&sort=top&t=month`
- (read from search-result selftext, not opened individually) 1vo5vnz ReDetail · 1v?? WEEKENDDDDDDDD 222 V2V · LTX 2.5 x2 upscaler for Minimax H3 · LTX 2.5 Is Disappointing · Most LTX 2.3 Loras work on LTX 2.5 · MiniMax H3 + LTX 2.3 Spatial Upscale · I Found a way to reduce LTX 2.5's horrible smearing · Minimax H3 vs LTX 2.5 on the same prompt · Minimax H3 executes Order 66 · LTX 2.3 x MinMax H3 comparison

Civitai (JSON API, civitai.red, unauthenticated):
- `/api/v1/models?baseModels=LTXV 2.5&sort=Most Downloaded` (20 items)
- `/api/v1/models?baseModels=LTXV 2.3&sort=Most Downloaded` (100 items) and `&types=LORA` (98)
- `/api/v1/models?baseModels=LTXV 2.5&sort=Newest`
- `/api/v1/models?query=LTX&sort=Most Downloaded&period=Month`

Named third-party repos surfaced (not opened — for the primary-source agent to verify):
`Lightricks/ComfyUI-LTXVideo` (example_workflows/2.5/LTX-2.5_ICLoRA_Union_Control_Distilled.json),
`Bambushu/redetail`, `peterducan-hub/PeterDuncan_Comfyui`, `BlackMixture/Mix-Studio`,
`nghtdrp/nghtdrp_snapmogen_motion_library`, `huggingface.co/Lightricks/LTX-2.5`,
`docs.ltx.io/open-source-model/`, `ltx.io/2-5-open-weights`, `ltx.io/blog/world-models-vs-llms`.
