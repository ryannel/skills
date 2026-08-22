# Adversarial fact-check — `skills/generative-media/ltx-2-5/`

**Checked 2026-08-22.** Method: every hard fact enumerated, then classified against the three
workbench research files, then the high-stakes ones re-verified against primary text pulled
fresh with `curl` (`LICENSE.md`, the 2.3 `LICENSE`, the AUP PDF, the GitHub commit API, the HF
model API, `ltx-core`/`ltx-pipelines` docs, `ltx.io/llm-info`, the prompt guide, and — decisively
— the **shipped ComfyUI workflow JSON parsed as a graph, not grepped as text**). The skill was
being edited concurrently; line numbers are from the state at the end of this pass.

---

## Verdict

**MATERIAL ERRORS** — two, both in the same paragraph, both from the same root cause.

The licence work is **exemplary and I could not break it**: every operative sentence I re-pulled
matched verbatim, Attachment A really does enumerate exactly twenty restrictions, ¶20/¶17/¶18/¶19/¶5/¶7
are all present and correctly quoted, the AUP's sexually-explicit ban really does sit inside
*Universal Usage Standards* above the API section and the AUP really does define Products to include
"on-premises deployments", the 2.3 question is correctly left `[contested]` with all three pointers
accurately described, and the skill does **not** claim 2.3 is ungated. The technical lattice, the fps
set, the VAE compression figures, the frame formula, the pipeline names, the filenames, the ComfyUI
folders, the megapixel table, the DFR token costs, the multishot "no node, no flag" claim and the
surprising 2.3-IC-LoRA-on-2.5-transformer claim all survived independent verification — the last one
traced link-by-link through the graph, not just grepped.

What fails is the ComfyUI template reading. The research agent read `widgets_values` out of the
serialized JSON without checking whether those widgets are **link-driven**, and in these subgraph-based
templates most of them are. Two claims in SKILL.md:138 are therefore false: the prompt enhancer is
**off** in all three shipped templates, not on; and the FLF2V fps "mismatch" cannot exist, because both
nodes read the same source node. Both are stated as observed fact about a shipped vendor artefact,
and one of them is the #1 entry in the failure table. Beyond those, five checkable numbers are wrong
or misattributed (gating count, Civitai count, one loader node name, one "template default", the 22B
citation) and none change a recommendation.

---

## Licence

Re-pulled `https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE.md` — HTTP 200, **30,938
bytes**, md5 `bfee719d6c18a6fd21344b3335a4f106`, byte-identical to the verifier's cached copy. Title
line 1: `# LTX-2.x Community License Agreement`; line 3: `*License date: August 11, 2026*`. ✅

### §1.6 — aggregation across affiliates ✅ CONFIRMED

> "an Entity shall be deemed to include, on an aggregative basis, all subsidiaries, affiliates, and
> other companies under common Control with such Entity. When determining whether an Entity meets any
> threshold under this Agreement (including revenue thresholds in Section 2.1), all subsidiaries,
> affiliates, and companies under common Control shall be considered collectively."

§1.3 defines Control as ">fifty percent (50%) of the voting securities … or the power to direct the
management and policies." SKILL.md:25's gloss ("a small studio owned by a large parent is over the
line") is sound.

### §2.1 — the $10M threshold ✅ CONFIRMED, quoted verbatim and correctly

The skill's block quote at SKILL.md:23 matches the source word for word, including the parenthetical
`(excluding use solely for a Non-Commercial Purpose as set forth in Section 2.2)`. The direction is
right: at/above $10M you need a paid licence, below it you do not. Contact `ltxv-licensing@lightricks.com`
✅. The "no published fee schedule" claim is conceded by the licence's own breach clause — "absent
published standard fees, a reasonable market rate" ✅.

### §2.2 — the carve-out ✅ CONFIRMED

Covers (i) personal hobby/research and (ii) "use by a Commercial Entity for testing, evaluation, or
non-commercial research and development in a non-production or development environment", excluding
revenue-generating use, end-user impact, and training "for commercial use." SKILL.md:25's summary
("evaluation, testing and non-production R&D") is accurate.

### §3.2 / §3.5 — LoRAs as Derivatives ✅ CONFIRMED, with one omission

§3.5 verbatim: *"No transfer of any Derivative of LTX-2.x **(including any fine-tuned weights, LoRA
adapters, or similar adaptations)** … If the transferee is a Commercial Entity (as defined in Section 2),
it must obtain a paid license from Licensor prior to any use of any Derivative of LTX-2.x, **regardless
of who created such Derivative**."* Both load-bearing phrases are exactly as the skill quotes them. ✅

§3.2 verbatim: *"must be distributed exclusively under the terms of this Agreement, subject to Section
3.6, with a complete copy of this Agreement included"* ✅.

**Two precision points, both minor:**

- **§3.5's final sentence is omitted everywhere in the skill:** *"Nothing in this Section 3.5 shall
  require a Commercial Entity to obtain a paid license for use solely for a Non-Commercial Purpose as
  permitted under Section 2.2."* SKILL.md:31 and `licence-and-derivatives.md`:58 present the transferee
  duty as unqualified. It is not — a Commercial Entity evaluating your LoRA in a dev environment does
  not need the paid licence. The omission **overstates** the burden.
- SKILL.md:31 says "**§1.5 and §3.5** name a LoRA adapter as a Derivative." §1.5 does not contain the
  word LoRA; it says "any fine-tuned or adapted weights, parameters, or checkpoints derived from
  LTX-2.x." Only §3.5 names LoRAs. `licence-and-derivatives.md`:11/57 gets this exactly right.

### Attachment A — twenty restrictions ✅ CONFIRMED (counted: exactly 20)

`grep -cE '^> \*\*[0-9]+\)\*\*'` over Attachment A returns **20**. The skill's "it enumerates twenty
restrictions" is literally correct, and the four it foregrounds are accurate:

- **¶20** verbatim: *"To use LTX-2.x or Derivatives of LTX-2.x in any product, service, or application
  that directly competes with Licensor's commercial products or services, or is designed to replace or
  substitute Licensor's offerings in the market, without obtaining a separate commercial license from
  Licensor."* The skill's quote at SKILL.md:27 is verbatim. No revenue floor exists in the paragraph ✅.
- **¶17** verbatim: *"For military, warfare, nuclear industries or applications, weapons development, or
  any use in connection with activities that may cause death, personal injury, or severe physical or
  environmental damage"* ✅.
- **¶18** verbatim: *"**For commercial use only:** To train, improve, or fine-tune any other machine
  learning model, artificial intelligence system, or competing model, except for Derivatives of LTX-2.x
  as expressly permitted under this Agreement"* — the "for commercial use only" scoping the skill flags
  is real ✅, and the AUP's unconditional counterpart under *Do Not Abuse our Products* is real too
  (quoted below). Marking the gap `[contested]` is the right call.
- **¶19** ✅, **¶7** ✅ ("To impersonate or attempt to impersonate (e.g. deepfakes) others without their
  consent"), **¶5** ✅ verbatim (*"without expressly and intelligibly disclaiming that the information
  and/or content is machine generated"*).

**One narrowing to fix.** SKILL.md's description, pre-flight item 1 (SKILL.md:255) and the suite table
(SKILL.md:279) all render ¶20 as competing with Lightricks' own "**video** products." The clause says
"Licensor's commercial products or services" — unqualified. Lightricks ships photo and design apps
(Facetune, Photoleap) as well as video. The body at SKILL.md:27 quotes it correctly; the three summaries
**understate** the clause's reach. Also at SKILL.md:27, "so this **reaches** much of what anyone would
build" is a firmer legal conclusion than the text supports; an earlier revision said "plausibly reaches,"
which was better.

### §5 / §6 — outputs, disclosure, watermarks ✅ CONFIRMED

§5 verbatim ✅. **No branding requirement:** grepped the full text for "powered by" / "branding" —
absent; the only attribution duty is §3.4's ordinary notice-retention on redistributed *weights*, not
on output ✅. §6 verbatim contains "shall not remove, disable, alter, or circumvent, any safety or
security measures, disclosures, metadata, watermarking, content provenance, latent disclosure, or other
transparency features … including any capability of LTX-2.x to include latent disclosures in Outputs,"
and *"If Licensor knows or **reasonably believes** … Licensor may in its sole discretion **revoke the
license** granted under this Agreement effective immediately upon notice"* ✅ — SKILL.md:33's phrasing
is precise. §6 also names the **California AI Transparency Act** alongside the EU AI Act, which the
skill does not mention (not an error; a small addition available). Article 53(2) EU AI Act
free-and-open-source positioning ✅ confirmed at `LICENSE.md`:57.

### The AUP ✅ CONFIRMED — and the on-premises reach is real

Re-downloaded `https://static.lightricks.com/legal/ltx-acceptable-use-policy.pdf` (HTTP 200, 110,423
bytes) and extracted with `pdftotext -layout`. `Last Updated: March 30, 2026` ✅.

Section ordering in the extracted text — this is the whole argument and it holds:

| Line | Heading |
|---|---|
| 69 | **Universal Usage Standards** |
| 163 | Do Not Abuse our Products |
| **181** | **Do Not Generate Sexually Explicit Content** |
| 210 | Use of our API |

The sexually-explicit section sits at 181, **inside** Universal Usage Standards and **above** the
API-specific section at 210 ✅. Its bullets verbatim: *"Depict or request sexual intercourse or sex
acts; Generate content related to sexual fetishes or fantasies; Facilitate, promote, or depict incest
or bestiality; Engage in erotic chats"* — exactly the skill's paraphrase at SKILL.md:29 ✅.

Scope, verbatim from the AUP's opening: Products are *"made available on cloud-hosted basis and/or
**on-premises deployments**"*, and *"This Acceptable Use Policy ("AUP") applies to anyone who uses
Lightricks' Products."* ✅ Attachment A incorporates it *"into and made part of this Agreement by
reference"* ✅. **The skill's conclusion that the NSFW ban binds local weights is correct and I could
not refute it.**

¶18's unconditional AUP counterpart, verbatim from *Do Not Abuse our Products*: *"Use or access our
Products or any outputs to develop, modify, fine tune or improve any products or services that compete
with our Products, including to develop, fine tune or train any artificial intelligence or machine
learning algorithms or models of any kind"* ✅ — the reference file quotes this exactly.

The likeness clause quoted at `licence-and-derivatives.md`:43 is verbatim ✅ (it sits under *Restrictions
on Use of Licensed Content for AI Model Training*, not under *Do Not Abuse*; the reference does not
misattribute it).

### The LTX-2.3 question ✅ CORRECTLY LEFT `[contested]`

All three pointers independently verified:

| Pointer | Resolves to | Verified |
|---|---|---|
| `huggingface.co/Lightricks/LTX-2.3/raw/main/LICENSE` | **LTX-2 Community License Agreement / License date: January 5, 2026** (21,399 bytes) | ✅ |
| That repo's `license_link:` frontmatter | `https://github.com/Lightricks/LTX-2/blob/main/LICENSE.md` — the **August** text | ✅ |
| That repo's body link (line 75) `.../blob/main/LICENSE` | the **August** text in plaintext | ✅ |

GitHub commit API on `path=LICENSE`: `9ce438b353` (2026-01-05), `4dbd99e628` (2026-02-09),
`2362161611` (2026-08-11), **`3518503496` 2026-08-12T08:54:23Z "Add LTX-2.x Community License Agreement
in txt format"** ✅ — the 2026-08-12 overwrite the skill describes. `LICENSE.md` has exactly **one**
commit, 2026-08-11 ✅, so "unamended since" is right.

Old-text differentials, all verified by grep on the fetched file: `$10,000,000` present ✅;
`grep -ci "Non-Commercial Purpose"` = **0** ✅; `grep -ci lora` = **0** ✅; `grep -ci "regardless of who"`
= **0** ✅; and verbatim *"to liquidated damages, which will be paid to Licensor immediately upon demand,
in an amount equal to **double the amount** that would otherwise have been paid by you"* ✅.

§1.9 verbatim: *"This license is applicable to all LTX-2.5 versions released since August 11, 2026, and
all future releases of LTX-2.x under this license."* ✅ — wording that does not reach backwards to 2.3.

**The skill asserts no resolution.** SKILL.md:35, SKILL.md:290 and `licence-and-derivatives.md` §8 all
carry `[contested]` and present the conflict rather than a winner. ✅ Correct.

### Gating ✅ correct in direction, ❌ wrong in count

The skill does **not** claim 2.3 is ungated — SKILL.md:56 explicitly warns against treating it as "the
ungated escape hatch." ✅ The gate date (2026-07-26) ✅ and "including `Clean-Plate` and both plain-LoRA
repos" ✅ both check out. **But the count is wrong** — see Errors found #3.

### Licence verdict

**CLEAN.** No misstatement of any operative clause. Three minor precision items (the §3.5 carve-out
omission, the "video products" narrowing, and §1.5 credited with naming LoRAs). Nothing here would
mislead a reader into a licence breach; two of the three err toward over-caution.

---

## Errors found

| # | Claim (`file:line`) | What is actually true | Source | Severity |
|---|---|---|---|---|
| 1 | `SKILL.md:138` — "**The prompt enhancer is on in the shipped JSON**"; the failure table (`SKILL.md:240`) makes "turn the enhancer off" the first thing to check | **Off in all three official templates.** The subgraph node's `prompt_enhance` BOOLEAN widget is `False` in `video_ltx2_5_t2v.json`, `_i2v.json` and `_flf2v.json`. The inner `PrimitiveBoolean [True]` is a stale serialized widget whose `value` input is **link-driven from the parent subgraph input**, so the outer `False` wins. The template's own MarkdownNote says *"(Optional, **off by default**)"*, and `docs.comfy.org` agrees | `raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/video_ltx2_5_{t2v,i2v,flf2v}.json`, parsed as a graph | **MATERIAL** |
| 2 | `SKILL.md:138` and `references/setup-and-workflows.md:47` — FLF2V "ships `LTXVConditioning [25]` against `CreateVideo [24]`, which **looks like a template bug and makes timing wrong without erroring**" / "almost certainly a bug" | **No mismatch is possible.** In `video_ltx2_5_flf2v.json`, `LTXVConditioning.frame_rate` and `CreateVideo.fps` are both link-driven from **the same node #212** (`ComfyMathExpression['a']` ← `PrimitiveInt [24]`). Both `[25]` and `[24]` are stale widget values that never execute. Timing cannot go wrong from this | same file, link graph traced | **MATERIAL** |
| 3 | `SKILL.md:56`, `references/licence-and-derivatives.md:81`, `references/setup-and-workflows.md:71,202` — "**14 of 18** 2.3-family repos are `gated: auto`" | **16 of 18** adapter repos are gated (14 IC-LoRAs + **both** plain-LoRA repos, which the same sentence names). Across the full 21-repo 2.3 family it is **16 of 21**. Only `LTX-2.3`, `-fp8`, `-nvfp4`, `IC-LoRA-Motion-Track-Control` and `IC-LoRA-Union-Control` are ungated | `huggingface.co/api/models?author=Lightricks&full=true` (57 repos enumerated) | minor |
| 4 | `SKILL.md:4,50,54,278`; `setup-and-workflows.md:149`; `lora-training.md:95` — "**98** Civitai LoRAs" / "98 of ~101" | **168.** The 98 is one page of a cursor-paginated response; page 2 returns 70 more. Correct figures for 2026-08-22: **168 LoRAs tagged `LTXV 2.3` against 3 tagged `LTXV 2.5`** (~171 total). The "~101" arithmetic collapses with it. Direction unchanged — the point is *strengthened* | `civitai.com/api/v1/models?baseModels=LTXV%202.3&types=LORA&limit=100`, both pages walked; 2.5 confirmed at exactly 3 with no next page | minor |
| 5 | `SKILL.md:120` — file-layout table, **"Loader node"** column gives `LTXVLatentUpsampler` for `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | The loader is **`LatentUpscaleModelLoader`**. `LTXVLatentUpsampler` is the node that *consumes* the loaded model (`samples`, `upscale_model`, `vae`); it takes no filename. The other three rows are right — `UNETLoader` ("Load Diffusion Model"), `CLIPLoader`, `VAELoader` ("Load VAE") | `video_ltx2_5_t2v.json`, node #371 → #348 | minor |
| 6 | `SKILL.md:207` — "4 s = **97** frames (**template default**)" | 97 is not the template default. The shipped duration primitive is **5 s** at 24 fps → **121 frames**. 97 is the stale `EmptyLTXVLatentVideo` widget value, overridden by `ComfyMathExpression['a * b + 1']`. The `4 s = 97` arithmetic itself is correct | `video_ltx2_5_t2v.json` nodes #378, #362, #361 | minor |
| 7 | `SKILL.md:132` and `references/setup-and-workflows.md:29` — "Stock node settings — **verbatim from** `video_ltx2_5_t2v.json`": `EmptyLTXVLatentVideo [768, 512, 97, 1]` | Verbatim from the file, but **functionally inert**: `width`, `height` and `length` are all link-driven. The template actually builds a stage-1 latent of **640 × 368 × 121** (1280×736 halved; 5 s × 24 + 1). This also silently contradicts `SKILL.md:212`'s correct "templates default to 1280×736" | same file, links traced | minor |
| 8 | `SKILL.md:9` — "**22B**-parameter asymmetric dual-stream diffusion transformer … `[official — ltx-core README; arXiv 2601.03233]`" | The 22B figure is right, but **neither cited source says it**. `ltx-core/README.md` says "14B-parameter video stream + 5B-parameter audio stream" (= 19B, lines 36/221/266) and arXiv 2601.03233 is the LTX-2 paper with the same split. 22B comes from `ltx.io/llm-info`. The research file flagged the per-stream split for 2.5 as unpublished; the skill merged the two provenances. "48 blocks", "3D/1D RoPE", "cross-modality AdaLN" are all correctly sourced to ltx-core | `raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/README.md`; `ltx.io/llm-info` | minor |
| 9 | `SKILL.md:200` — reconciling 32 vs 64: "stage 2 doubles stage-1 dimensions, so a multiple-of-32 stage 1 yields a multiple-of-64 output anyway" | Backwards relative to the template, and the conclusion fails on the stock default. `ResolutionSelector` snaps the **output** to a multiple of 32 (1280×736) and stage 1 is *half* that (640×368 — not a multiple of 32). And **736 = 32×23 is not divisible by 64**, so the stock default does not satisfy ReDetail's rule. The reconciliation should be dropped or rewritten | `video_ltx2_5_t2v.json` node #409 → #353/#355 | minor |

Errors 1, 2, 6 and 7 share one root cause: **serialized `widgets_values` in these subgraph templates
are frequently dead**, overridden by links from the parent graph. Any future template reading for this
suite should resolve links before quoting a widget.

---

## Claims absent from all research

| Claim | Determination |
|---|---|
| `SKILL.md:114–120` — the entire **ComfyUI folder** column (`models/diffusion_models/`, `models/text_encoders/`, `models/vae/`, `models/latent_upscale_models/`, `models/model_patches/`, `models/loras/`) | **Author's own verified find — correct.** Not in any research file (which listed HF repo paths). The T2V template's "Model Storage Location" MarkdownNote publishes exactly this tree, including the unusual `models/latent_upscale_models/`. ✅ |
| `SKILL.md:114–119` — the **Loader node** column (`Load Diffusion Model`, `CLIPLoader`, `Load VAE`) | **Correct** — these are the ComfyUI display names of `UNETLoader`, `CLIPLoader` (type `ltxv`) and `VAELoader` as instantiated in the template. Fourth row wrong (error #5). |
| `SKILL.md:9` — "the projection bundled in", "Gemma 4 12B", version check `gemma4-12b-ltx-v1` | In research, and **independently re-verified verbatim**: LTX-2 README line 76 — *"Google's stock Gemma 4 release is not a substitute: loading checks the encoder's version against the one the checkpoint was trained with (`gemma4-12b-ltx-v1`)"* ✅ |
| `SKILL.md:126` — "the `ComfyUI-LTXVideo` top-level README is still 2.3-centric" | **Verified stronger than stated:** the README contains **32** occurrences of "2.3" and **zero** of "2.5" ✅ |
| `SKILL.md:60` — five named 2.5 workflows loading 2.3 IC-LoRAs | **Verified, and traced beyond the research.** All five files fetched; each references its named `ltx-2.3-22b-ic-lora-*` file ✅. I additionally traced `LTX-2.5_ICLoRA_Union_Control_Distilled.json`: node #5607 `LTXICLoRALoaderModelOnly ['ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors', 1]` takes `model ← #5602 UNETLoader ['ltx-2.5-22b-distilled-transformer-bf16.safetensors']`. **The 2.3 adapter is applied directly to the 2.5 transformer.** The `ltx-2.3-22b-dev.safetensors` string also present in these files is a combo option, not a wired loader. The "contradicts the suite's usual rule" claim is correct ✅ |
| `SKILL.md:60` — "HDR, Dub-It and **Relight** are 2.3-only" | **Correct**, though it needed two different reads: HDR and Dub-It carry `**Compatibility:** LTX-2.3 only — LTX-2.5 support in development`; **Relight** is flagged only inside the summary table as *"(LTX-2.5 in development)"* ✅ |
| `SKILL.md:52` — "`LTX-2.5-Pre-Trained`, the raw non-SFT base"; "LTX-2 (19B) still hosts the camera-control LoRAs" | ✅ Both repos exist; all seven `LTX-2-19b-LoRA-Camera-Control-*` repos confirmed at **0 downloads**, and `ltx.io/llm-info` still advertises them under "Creative Controls" — the `[flagged — re-verify]` on "may be stale marketing" is well placed |
| `SKILL.md:49` — "**No `LTX-2.5-fp8` repo exists**" | ✅ Verified: across all 57 `Lightricks/*` repos, the only name containing "fp8" is `Lightricks/LTX-2.3-fp8` |
| `SKILL.md:54` — HF downloads "1.58M vs 695k" | ✅ 1,578,744 vs 694,670, live |
| `references/lora-training.md:59` — "89 frames (`8×11+1`)" | ✅ arithmetic correct; matches the trainer validation default in CHANGELOG 1.2.0 |
| `SKILL.md:68` — "**twelve** `python -m ltx_pipelines.<name>` entry points" | ✅ The selection guide's comparison table lists exactly 12. (The package README's prose says "all 11 pipelines" — a vendor inconsistency the skill sidesteps by counting the table.) All twelve class names verified against `docs/pipeline-selection.md` ✅ |

---

## Arithmetic check

The frame lattice is `8k+1`; the templates compute `fps × seconds + 1`. A whole-second duration is
legal iff `fps × s ≡ 0 (mod 8)`.

| fps | Rule the skill states | Derivation | Verdict |
|---|---|---|---|
| 24 | any whole second | `24s = 8·3s` ≡ 0 mod 8 for all `s` | ✅ |
| 25 | multiples of 8 | `gcd(25,8)=1` ⇒ `s ≡ 0 mod 8` | ✅ |
| 48 | any whole second | `48s = 8·6s` | ✅ |
| 50 | multiples of 4 | `50s ≡ 0 mod 8` ⇔ `25s ≡ 0 mod 4` ⇔ `s ≡ 0 mod 4` | ✅ |

Every worked value satisfies the skill's own formula:

| Claim | `fps×s+1` | `(F−1) mod 8` | Verdict |
|---|---|---|---|
| 24 fps, 4 s = **97** | 97 | 96 = 8·12 → 0 | ✅ (but "template default" is wrong — error #6) |
| 24 fps, 5 s = **121** | 121 | 120 = 8·15 | ✅ — *this* is the template default |
| 24 fps, 10 s = **241** | 241 | 240 = 8·30 | ✅ |
| 25 fps, 8 s = **201** | 201 | 200 = 8·25 | ✅ |
| 25 fps, 16 s = **401** | 401 | 400 = 8·50 | ✅ |
| 48 fps, 5 s = **241** | 241 | 240 | ✅ |
| 48 fps, 10 s = **481** | 481 | 480 = 8·60 | ✅ |
| 50 fps, 4 s = **201** | 201 | 200 | ✅ |
| 50 fps, 8 s = **401** | 401 | 400 | ✅ |

Other arithmetic:

- `SKILL.md:199` — "lost **7** frames off every 240-frame clip": 240 − 233 = 7 ✅, and 233 = 8·29+1 is
  the largest legal value ≤ 240 ✅. Community quote matches.
- `SKILL.md:212` — 1280×736 = 942,080 px ≈ **0.9 MP** ✅; 1280/32 = 40 ✅, 736/32 = 23 ✅. All thirteen
  rows of the megapixel table in `setup-and-workflows.md:81–89` match the template's MarkdownNote
  exactly ✅.
- `setup-and-workflows.md:91` — "the 0.9 MP default lands at **2560×1472**" ✅ (1280×736 doubled).
- Sigma counts: stage 1 has **9** values → 8 steps ✅; stage 2 has **4** values → 3 steps ✅. Both
  strings verbatim ✅.
- VAE formula `[B,3,F,H,W] → [B,128,1+(F−1)/8,H/32,W/32]` — **verbatim** in `ltx-core/README.md`:331–333,
  with the worked example `[B,3,33,512,512] → [B,128,5,16,16]` ✅. 32× spatial / 8× temporal / 128
  channels all ✅.
- DFR keyframe cost — verbatim in `docs/conditioning.md`:43–45: *"At 512x768 / 241 frames, 5 keyframes
  is about +16% tokens (~1.35x attention cost); at 1088x1920 / 121 frames it is about +31% (~1.72x)."* ✅
- **One arithmetic-adjacent reasoning error:** the 32-vs-64 reconciliation at `SKILL.md:200` — error #9.

---

## Markers

**Correctly marked `[contested]`** — verified as genuinely unresolved:

- Which licence governs 2.3 (SKILL.md:35, 290) — three pointers, two documents, all three re-verified ✅
- ¶18 commercial-only vs the AUP's unconditional ban (SKILL.md:27) — both texts confirmed present ✅
- 2.3 LoRA on 2.5 (SKILL.md:60) — README says no, vendor workflows say yes; both confirmed ✅
- **VRAM (SKILL.md:142)** — marked `[contested]` and all three figures re-verified: docs
  system-requirements says *"NVIDIA GPU with a minimum 32GB+ VRAM"* / *"NVIDIA A100 (80GB) or H100"*;
  `llm-info` says *"80GB+ VRAM. Distilled and FP8-quantized variants support 32GB, and run locally on a
  single GPU with as little as 12GB VRAM"*; the launch table says 16 GB. ✅ The skill marks it contested
  **and** recommends the documentation figure with a stated reason — that is a reasoned preference on a
  flagged conflict, not a silent pick. Acceptable.
- Multishot identity retention; 2.5-vs-2.3; Metal/ROCm; real-time streaming; the enhancer's ship state —
  all listed at SKILL.md:311–318 ✅

**Mis-marked:**

- **`[contested]` on the FLF2V fps mismatch** (SKILL.md:138, `setup-and-workflows.md:47`, SKILL.md:317)
  — not contested, **refuted**. Should be deleted, not hedged.
- **The enhancer's ship state is listed as `[contested]` at SKILL.md:317 but asserted flatly at
  SKILL.md:138.** The body contradicts the skill's own unresolved list, and picks the wrong side.
- `SKILL.md:9`'s `[official — ltx-core README; arXiv 2601.03233]` is over-precise for the 22B figure
  (error #8) — the marker should read `[official — ltx.io/llm-info; ltx-core README]`.

**Correctly *not* marked** (i.e. asserted, and right to be): the licence quotes, the lattice, the fps
set, the pipeline names, the filenames, the folders, the multishot prompting rules, the IC-LoRA
cross-version evidence, the megapixel table, "no branding duty", "the AUP binds local weights".

**Under-hedged, mildly:** SKILL.md:27's "this **reaches** much of what anyone would build with an open
video model" — an unqualified legal reading of ¶20 in a skill that otherwise disclaims legal advice.

**Cross-links:** all 60+ relative links now resolve. `references/characters.md:89` had `../scail-2/`
(would need `../../`) at the start of this pass and was corrected during it; re-checked clean.

---

## Could not verify

- **Whether the gated 2.5 repos ship an in-repo `LICENSE` differing from GitHub's.** The HF API
  `siblings` listing for `Lightricks/LTX-2.5` shows **17 files and no `LICENSE`** — consistent with, but
  not proof of, "no divergent in-repo text." I did not authenticate through the gate, so the skill's
  `[flagged — re-verify]` stands as the right posture.
- **The exact HF gate wording** ("consent to receive offers and updates including targeted and
  personalized advertisements"). The API confirms `gated: auto` on all four 2.5 repos; the quoted
  click-through text comes from the verification file's rendered-page read, which I did not repeat.
- **Whether the paid Commercial Use Agreement has any published terms.** §2.1 defers to a document "as
  will be provided by the Licensor" and the breach clause concedes "absent published standard fees."
  Nothing public exists; correctly `[flagged — re-verify]`.
- **Whether LTX-2.5 output embeds a watermark or C2PA provenance.** §6 protects the mechanism; no
  documentation describes one. Correctly `[flagged — re-verify]`.
- **diffusers specifics** — `Lightricks/LTX-2.5-Diffusers` exists (`gated: auto`, 6,489 downloads, last
  modified 2026-08-20); I did not read its config, matching the skill's own `[flagged — re-verify]`.
- **All community craft claims** (jerk-oracle, step-skipping theory, decoder-OOM reports, measured
  timings, ReDetail numbers, positioning verdicts). Out of scope for a primary-source pass; the skill
  attributes each to a named handle and marks the single reports as such, which is the suite's standard.
- **Attachment A ¶20's practical scope** — whether it actually bites on a given product is a legal
  question, not a factual one. The skill says so.
