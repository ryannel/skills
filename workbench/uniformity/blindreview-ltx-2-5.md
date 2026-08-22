# Blind review — `skills/generative-media/ltx-2-5`

Reviewed against a snapshot taken 2026-08-22 21:45:42 CEST (`SKILL.md` md5 `23b004538096f8da7ab274b9433c012a`, 296 lines).
**The skill was being edited while I read it** — `SKILL.md` went 300 → 296 lines mid-review and three
references have a 21:44 mtime. Line numbers below are from the snapshot; re-check before applying.

No research material was consulted. Nothing under `workbench/ltx-2-5/` or `workbench/research-2026-08-22/`
was opened. Every "I went looking for a source" note below is a finding about the page, not about the model.

---

## Verdict

**SHIP WITH FIXES.** This is a strong skill — the provenance discipline is the best in the suite, the
licence treatment is the most careful legal writing in the repo, and the multishot chapter genuinely
teaches a technique rather than gesturing at one. But it has two defects a reader will hit on day one.
First, it spends its variant selector arguing that **2.3 is where the ecosystem actually is** (98 of ~101
LoRAs, more downloads than 2.5) and then gives a reader who takes that advice **nothing to run 2.3 with** —
no filename, no encoder file, no folder, no template, no sigma list, no confirmation that the `8k+1`
lattice even holds. The description promises "LTX-2.5 **and LTX-2.3**"; the body delivers 2.5 plus a
2.3 licence essay. Second, the skill's own headline number is internally inconsistent: the vendor says
**2–4 shots**, and SKILL.md converts that to **2–4 cuts** in three places while saying "two to four shots"
in two others — an off-by-one on the exact parameter the model is famous for. Add a missing MANDATORY
section (`## Per-mode settings`), one broken relative link, one silent-failure trap stranded in a
reference, and no marketplace/README/freshness registration, and this is a half-day of fixes rather than
a rewrite. Nothing here reads as invented, and the two-bar section is unusually honest about what it
does not know.

---

## Could I execute?

The task: a 3-cut video (so **four shots**), consistent character, synchronised audio.

**What worked, walked in order:**

1. **Pick a version.** Selector at `SKILL.md:45–56`. Multishot is 2.5-only, so 2.5 distilled. Clean.
2. **Settle the licence.** `SKILL.md:17–37`. I know within two minutes whether I may ship. Excellent.
3. **Download.** File table at `SKILL.md:112–120` gives filename → `models/` folder → loader node for
   all seven files. Gating and the token scope are at `setup-and-workflows.md:73` and `:217`.
   Minor gap: the table names files but never the **repo** they come from — I inferred
   `Lightricks/LTX-2.5` from the gating paragraph.
4. **Choose the decoder.** `SKILL.md:124` is the best paragraph in the skill: the choice is made by
   *which file you place*, the failure is at decode not at sampling, and the fix is named. This is
   exactly what a first-run reader needs and would not think to ask for.
5. **Frame count.** 10 s at 24 fps → 241. The fps→legal-seconds table at `SKILL.md:160–165` is correct
   in all four rows (I checked the arithmetic: 24 and 48 are unconstrained because both are multiples
   of 8; 25 needs multiples of 8 seconds; 50 needs multiples of 4). Genuinely useful.
6. **Sampler / sigmas / CFG.** `SKILL.md:128–136`, verbatim, labelled verbatim. Fine.
7. **Write the prompt.** See next section — this part works.

**Where I got stuck, in order of severity:**

**Sticking point 1 — consistent character across cuts has no worked path.** `characters.md:15–20` gives
me four options and rates Ingredients "Holds across a cut: **Partly**" — the best non-training answer.
But Ingredients' prompt is a **two-part string** (`Reference sheet: … / Generated video: …`,
`characters.md:54–57`), and the multishot rule is **one flowing chronological paragraph**
(`prompting-guide.md:78`). Nothing in either file tells me how those compose. Does the multishot
paragraph go entirely inside `Generated video:`? Do the cut descriptions survive that framing? There is
no worked example of Ingredients + multishot anywhere, and this is the exact combination the stated task
requires. Compounding it, the task-mode selector files `ICLoraPipeline` under **"V2V with control"**
(`SKILL.md:73`), which implies a reference *video* — but Ingredients takes reference *panels*. So I
cannot even tell which pipeline to invoke. **This is where I stopped.**

**Sticking point 2 — which resolution is the template default?** `SKILL.md:132` gives, as verbatim
template JSON, `EmptyLTXVLatentVideo [768, 512, 97, 1]` (0.39 MP, 3:2). `SKILL.md:167` says templates
"default to **1280×736 (0.9 MP)** at 16:9", and `setup-and-workflows.md:84` bolds 1280×736 as
"(template default)". Both cannot be the default. I would have to open the JSON to resolve it — which
is exactly the lookup a "verbatim from the template" table exists to prevent.

**Sticking point 3 — the audio latent's second argument.** `LTXVEmptyLatentAudio [97, 25, 1]`
(`SKILL.md:132`, `setup-and-workflows.md:30`). I am changing 97 → 241; `setup-and-workflows.md:41` tells
me the frame counts must match, good. But what is the **25**? If it is fps, it disagrees with
`LTXVConditioning [24]` in the same graph — and the skill separately calls a `[25]`-vs-`[24]` mismatch in
the FLF2V template "almost certainly a bug" (`setup-and-workflows.md:47`). Either the 25 is not fps and
the FLF2V bug call is weaker than stated, or the T2V template has the same bug and the skill missed it.
Unresolvable from the page.

**Sticking point 4 — pacing across cuts.** With `--num-frames 241` fixed, I have four shots to fit in ten
seconds. Nothing anywhere tells me how to weight them. `SKILL.md:104` says "duration is also a sentence",
but that is the auto-duration head, which `prompting-guide.md:146` says requires *omitting* `--num-frames` —
mutually exclusive with the lattice discipline the whole skill insists on, and SKILL.md never says so.
For a multi-shot job this is a real gap: shot balance is the first thing that goes wrong.

**Sticking point 5 — what does an LTX clip look like?** I grepped the whole skill for "default look",
"graded", "aesthetic", "colour cast", "filmic". **Zero hits.** `wan-2-2` has
"The default is motion, not stillness — and the look is graded"; `minimax-h3` has "H3 directs itself —
the default look…". LTX's slot-7 section (`SKILL.md:171`) covers three *artefacts* and the locked-off
camera, but never the model's default grade or texture. I cannot tell whether I need to fight a look.

**Turning the enhancer off** is instructed four times but never shown — bypass the node? delete it?
Trivial, but it is the skill's own "check this before debugging anything else".

---

## Multishot

**Yes — I could write a working multishot prompt from the page alone, and the worked examples are *not*
the only thing carrying it.** This is the strongest chapter in the skill.

What does the work, in order of load-bearing-ness:

1. **`prompting-guide.md:82–85` — the four per-cut rules.** Name the transition; re-establish the shot;
   reuse the same visual identifier; state audio continuity. Four rules, each with two or three example
   phrasings inline. This alone is generative — I can apply it to a scene the skill never mentions.
2. **`prompting-guide.md:91–96` — the single-shot/multi-shot contrast table.** Four axes, both columns
   filled. This is what turns the four rules into a *choice*, and it is the thing a reader would
   otherwise get wrong by writing a single-take prompt and expecting cuts.
3. **`prompting-guide.md:112` — the rule-by-rule annotation of the vendor example.** The example is
   quoted, then each of the four rules is pointed at the exact phrase that satisfies it. This is
   teaching, not decoration.
4. **`prompting-guide.md:225` — the fill-in-the-blanks template.** Explicitly shaped for 2–4 cuts.
5. **`SKILL.md:96–102` — the Don't/Do table.** The `SHOT 1: / SHOT 2:` → prose transformation is the
   single highest-value line in the skill for this task.

So: rules + contrast + annotated example + template + anti-pattern. Four independent scaffolds. If both
worked examples were deleted, §4.2 + §4.3 + §11 would still get me there.

**Three real weaknesses:**

- **The count is wrong, or at least inconsistent.** The vendor quote at `prompting-guide.md:100` is
  "Prefer **2–4 shots**". `SKILL.md:11` correctly says "two to four connected **shots**". But
  `SKILL.md:104`, `SKILL.md:227` (pre-flight item 8) and `characters.md:32` all say "**2–4 cuts**" —
  and `characters.md:32` attributes it to "the vendor's own range". 2–4 shots is 1–3 cuts. A reader
  doing the task in this brief — three cuts, four shots — is told by the pre-flight checklist that they
  are safely mid-range when by the vendor's own number they are at the ceiling. `SKILL.md:209` says
  "2–4 shots" in the failure table, contradicting the pre-flight list three sections later.
- **No diagnosed failure example.** Every example is a *good* prompt. There is no "here is a multishot
  prompt that produced one continuous take, and here is which of the four rules it broke". For a
  technique whose only handle is prose, a worked failure would be worth more than a third worked success.
- **Nothing on dialogue timing across cuts.** The second worked example (`prompting-guide.md:118`) puts a
  quoted line in shot 2 — but nothing says how the model decides *when* in shot 2 it lands, or what
  happens when two shots each carry dialogue.

**`prompting-guide.md:202`** asserts a shot list is "**not parsed as cuts**" — a mechanistic claim,
unattributed, and stronger than the vendor quote two sections earlier, which merely *discourages*
sluglines "unless you also describe the cut in prose". This claim sent me looking for a source the skill
does not give me.

---

## The 2.5 vs 2.3 decision

**Decidable as a *choice*; not executable as a *path*; and the LoRA question is answered with more
confidence than the evidence carries.**

**What is decided well.** `SKILL.md:54` is honest in a way most skills are not: 2.3 has more downloads,
98 of ~101 Civitai LoRAs, and "treating 2.5 as the obvious default misleads anyone whose work depends on
an adapter". `SKILL.md:56` pre-empts the obvious next move (2.3 as the ungated escape hatch) with a
per-repo gating count. The mode-split caveat — 2.5's T2V may be *worse*, its I2V better — is the kind of
thing a vendor page would never say.

**Where it fails.** Having argued the reader onto 2.3, the skill abandons them there. Grepping every file
for 2.3 setup material returns: "Monolithic checkpoints, **Gemma 3 12B**" (`SKILL.md:50`), "2.3 ships a
monolith bundling transformer, both VAEs and the text projection" (`setup-and-workflows.md:55`), and three
error-table rows about *mixing* 2.3 with 2.5. That is all. **No 2.3 filename. No 2.3 encoder filename. No
folder mapping. No template name. No sigmas, steps, CFG or sampler. No confirmation that `8k+1`, the
multiple-of-32 rule or the fps set apply to 2.3 at all** — and since the two-bar section separately flags
that 2.5 may have *changed* the VAE compression factors (`SKILL.md:281`), a reader has no basis for
assuming the lattice transfers backwards. A reader who follows the skill's own advice cannot run the
model it advised.

**"Gemma 3 12B" is a bare assertion with no marker and no source** — the only architecture claim in the
skill of that weight without one. It is also the single fact that decides whether a 2.3 install works.

**Can I tell whether a LoRA I found will load?** Partly, and the SKILL.md answer over-reaches.
`SKILL.md:60` states the "operative rule" as **"assume a 2.3 adapter works on 2.5 unless its listing says
otherwise"**. The evidence given for it is entirely about **IC-LoRAs** — Lightricks' own 2.5 IC-LoRA
workflows loading 2.3 IC-LoRA files, plus a docs page titled "All LTX-2.5 IC-LoRAs" listing 2.3 cards.
The reference is more careful: `setup-and-workflows.md:155` scopes plain-LoRA forward compatibility to
one Reddit post ("pretty much confirmed by the devs") where "75 comments produced no clean confirmation",
and ends "**Test at low strength before committing.**" That caveat never reaches SKILL.md, which is the
only file most readers load. Generalising IC-LoRA evidence to the 98 plain LoRAs is the most consequential
over-confidence in the skill, because it inverts the suite's default rule on the strength of a different
adapter class.

---

## Licence clarity

**The best licence writing in this repo, and I would trust it to decide whether to download.** Four
named gates, each with a mechanism, in the right order: revenue → field of use → content → derivatives.
Putting **¶20 (no competing products, no revenue floor)** *ahead of* the $10M threshold is the correct
call and the one a careless summary would get wrong — it is the clause that binds a hobbyist as hard as a
studio. §1.6 aggregation across affiliates is flagged as "the part people miss", which it is. The §2.2
evaluation carve-out is given as the useful counterweight rather than buried.

**Quoted where it matters.** §2.1, §3.2, §3.5, ¶20, ¶5 and §5 are all verbatim in quotation marks. The
AUP-binds-local-weights argument (`licence-and-derivatives.md:52`) is *reasoned* rather than asserted:
the section sits in Universal Usage Standards, the scope names "on-premises deployments", Attachment A
incorporates it wholesale with no carve-out. That is exactly the right register for a claim a reader
might want to argue with.

**Not over-hedged.** The skill reaches conclusions: "Publishing an LTX LoRA under a permissive licence
is not something this agreement lets you do" (`SKILL.md:31`). "The prohibition binds local weights"
(`licence-and-derivatives.md:52`). "That is practice, not permission" on 2.3 adult work
(`lora-training.md:26`). Each is a real answer, correctly bounded by "This skill does not tell you what
your legal position is."

**Three things a careful reader would want and does not get:**

1. **The 2.3 licence question is left genuinely unresolved, and that is correct — but it is not
   actionable.** `licence-and-derivatives.md:77–83` lays out three pointers resolving to two documents
   and the §1.9 scope clause that reaches neither. Then `:95` says a studio over the threshold should
   "get a written answer from Lightricks". Fine for a studio. A hobbyist under $10M gets no default:
   *assume the harsher January text and behave accordingly* would cost nothing and is the obvious safe
   read, since the January text is strictly worse (double liquidated damages, no evaluation carve-out).
   The skill declines to say it.
2. **¶20 is never sized.** It is called "the most commercially dangerous clause" and said to reach "much
   of what anyone would build with an open video model" — but Lightricks' actual product list is never
   given, only "consumer video-editing and generative-video apps". Whether my tool competes is the entire
   question, and I cannot answer it from the page. This sent me looking for a source the skill does not give.
3. **The one licence claim I want a quote for and do not get: the ¶18-vs-AUP gap.** `SKILL.md:27` says
   ¶18 "scopes itself 'for commercial use only'" — three quoted words. The reference (`:40`) gives the
   AUP's competing sentence in full but still only three words of ¶18 itself, and adds that ¶18 "carves
   out Derivatives of LTX-2.x" with no quotation at all. Since the conclusion is that a hobbyist sits in
   a gap between two instruments, the exact wording of ¶18 is load-bearing and is the one place the
   verbatim discipline lapses.

---

## Contradictions

| Claim A | Claim B | Likely right |
|---|---|---|
| "Prefer **2–4 shots** in one generation" `prompting-guide.md:100` (verbatim vendor); "two to four connected **shots**" `SKILL.md:11`; "keep to **2–4 shots**" `SKILL.md:209` | "**2–4 cuts** is the working range" `SKILL.md:104`; "If multishot: **2–4 cuts**" `SKILL.md:227`; "Stay inside **2–4 cuts.** Past the vendor's own range" `characters.md:32` | **A — shots.** The vendor quote is verbatim. B is an off-by-one that inflates the range by a whole shot and misattributes it to the vendor. Fix all three B sites. |
| `EmptyLTXVLatentVideo [768, 512, 97, 1]`, presented under "**verbatim from `video_ltx2_5_t2v.json`**" `SKILL.md:132` and `setup-and-workflows.md:29` | "templates default to **1280×736 (0.9 MP)**" `SKILL.md:167`; "0.9 \| **1280×736** (template default)" `setup-and-workflows.md:84` | **A is the node's actual widget value; B is almost certainly the bolded row of the embedded `MarkdownNote` table.** Both are labelled "template default". Say which is the widget and which is the recommendation. |
| "**The prompt enhancer is on in the shipped JSON**" — bold, unhedged `SKILL.md:138` | "Whether the **prompt enhancer ships enabled** … `[contested]`" `SKILL.md:277`; "The official templates **wire** a Gemma 4 E2B enhancer" `prompting-guide.md:183` | **B.** The body asserts flatly what the tail lists as contested, and the reference uses the weaker verb. Hedge `:138` or drop the contested bullet. |
| "All three follow from the VAE — **32× spatial, 8× temporal, 128 latent channels**" `SKILL.md:150`, presented as the derivation of two hard rules | "whether **2.5 changed the VAE compression factors**, since the trainer now reads them from checkpoint metadata 'instead of assuming 32x32x8' `[flagged — re-verify]`" `SKILL.md:281` | **Unresolved, and that is the problem.** The entire lattice section — `8k+1`, multiple-of-32 — rests on a factor set the same file flags as unverified for 2.5. If the flag is real, the lattice is unsafe; if the lattice is safe, retire the flag. |
| "**2.5 dev/full** … a different hardware class, reported unrunnable on a 3090 `[community — Comfortable-You-3881]`" `SKILL.md:48` | "3090, 128 GB RAM \| **2.3 dev**, non-distilled \| would not run `[community — Comfortable-You-3881]`" `setup-and-workflows.md:109` | **B.** Same named source, and the reference scopes it to the **2.3** dev checkpoint. SKILL.md silently promotes it to a claim about 2.5 dev. Either re-scope `:48` or find 2.5-specific evidence. |
| "the operative rule here is **'assume a 2.3 adapter works on 2.5 unless its listing says otherwise'**" `SKILL.md:60` — evidence is entirely IC-LoRA | "Forward compatibility is claimed but soft … 75 comments produced no clean confirmation … **Test at low strength before committing.**" `setup-and-workflows.md:155`; "Whether a **2.5-trained plain LoRA loads on 2.3** `[contested]`" `lora-training.md:108` | **B.** The reference distinguishes IC-LoRAs (first-party evidence) from plain LoRAs (one unconfirmed post). SKILL.md collapses them and drops the test-at-low-strength caveat that most readers will never see. |
| "The two disagree less than they look: **stage 2 doubles stage-1 dimensions**, so a multiple-of-32 stage 1 yields a multiple-of-64 output anyway" `SKILL.md:155` | "**Skip stage 2**; raise base MP" is recommended twice — `SKILL.md:142`, `SKILL.md:184`, `setup-and-workflows.md:91`, `:120` | **Both, and they collide.** The 32↔64 reconciliation holds *only if stage 2 runs*. A low-VRAM reader taking the skill's own advice to skip stage 2 at 1280×736 delivers 736px — not divisible by 64 — and ReDetail rejects it. Say so. |
| FLF2V's `LTXVConditioning [25]` against `CreateVideo [24]` is "almost certainly a bug" `setup-and-workflows.md:47`, "looks like a template bug" `SKILL.md:138` | The **T2V** template ships `LTXVEmptyLatentAudio [97, **25**, 1]` alongside `LTXVConditioning [24]` `SKILL.md:132` | **Undetermined, and the skill never says what the audio latent's `25` is.** If it is fps, the FLF2V "bug" is weaker than claimed; if it is something else, say so, because a reader editing frame counts has to touch this node. |
| "**32 GB minimum**, A100 80 GB / H100 recommended … Prefer the documentation figure" `SKILL.md:142` | "conv if you are under **~24 GB**" `SKILL.md:223`; "3050 **4 GB VRAM** laptop … 0.9 MP × 10 s → 246 s" `setup-and-workflows.md:107` vs "4070 Ti **12 GB** … >10 s at 0.3 MP → **fails**" `:108` | **Nothing is clearly right, and the skill knows it (`[contested]` at `:142`).** But `~24 GB` in the pre-flight list is an orphan number appearing nowhere else, and the 4 GB-succeeds/12 GB-fails pair is left unreconciled directly above one another. |
| "the **2.5-native** Pixel Spatial Upscaler as `--detailing-lora`" `SKILL.md:188` | "Released adapters (**all `Lightricks/LTX-2.3-22b-IC-LoRA-*` unless noted**): … **Pixel Spatial Upscaler** (2× and 4×) … The only 2.5-native adapter is `Lightricks/LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler`" `setup-and-workflows.md:167` | **Both versions exist** — but the reference lists the name once inside a 2.3-scoped list and once as the 2.5 exception, which reads as a contradiction on a first pass. Disambiguate. |

Cross-skill, for completeness: `image-production-workflows/SKILL.md:143` states "both output dimensions
must divide by **64** (not 32)" flatly, where this skill (`SKILL.md:155`) reconciles 32 vs 64. The sibling
should adopt this skill's reconciliation — but see the stage-2 collision above, which means the
reconciliation itself needs a caveat first.

---

## Unsupported or over-confident

**Over-confident:**

- **`SKILL.md:50` — "Monolithic checkpoints, Gemma 3 12B".** No marker, no source, no artefact named,
  in a table cell that otherwise carries `[community — Civitai API 2026-08-22]`. It is the fact that
  decides whether a 2.3 install works.
- **`SKILL.md:60` — the adapter rule.** Covered above: IC-LoRA evidence generalised to all adapters, with
  the reference's "test at low strength" caveat dropped on the way up.
- **`SKILL.md:48` — "reported unrunnable on a 3090".** The cited source said 2.3 dev.
- **`prompting-guide.md:202` — "Not parsed as cuts".** A claim about the model's parsing behaviour,
  unattributed, stronger than the vendor quote it rests on.
- **`SKILL.md:9` — the architecture paragraph.** "Forty-eight blocks shared by a video stream and an audio
  stream of differing width, coupled by bidirectional cross-attention and cross-modality AdaLN … Video
  carries 3D RoPE (x, y, t); audio carries 1D temporal RoPE." One marker covers the whole paragraph
  (`[official — ltx-core README; arXiv 2601.03233]`) — acceptable as paragraph-scoped — but the skill
  separately flags that "**how the 22B splits** between video and audio streams — not published"
  (`SKILL.md:281`), which sits oddly beside asserting the block count and the stream asymmetry.
- **`SKILL.md:190` — "The dominant real-world use of LTX-2.5 today is not generation — it is finishing
  someone else's clip."** A strong claim about the whole ecosystem, supported by "nearly every
  high-scoring LTX post in the last month" and three usernames. Directionally plausible; the phrasing
  outruns three data points. "Nearly every" is a counting claim with no count.
- **`SKILL.md:171` — "The most-cited complaint about 2.5"** on the strength of one quoted user. Same
  problem: a frequency claim with no frequency.

**Unsupported craft (no named source, §6.2(c) triggered):**

- `SKILL.md:223` — "conv if you are **under ~24 GB**". Orphan threshold; contradicts the 32 GB figure
  four sections earlier and appears nowhere else.
- `setup-and-workflows.md:119` — enhancer "Frees a **~5–10 GB** model `[contested]`". `[contested]` is
  not attribution; and a Gemma-4-**E2B** at 5–10 GB wants explaining.
- `setup-and-workflows.md:153` — LoRA strength "at the usual **0.5–1.5** band". Suite-generic, but it is
  a number a reader types.
- `setup-and-workflows.md:183` — Mix Studio / ComfyUI-Stimma versions marked bare `` `[community]` ``
  with no named source or venue.
- `SKILL.md:177` — the jerk-oracle mechanism is described in confident mechanical detail (inserts hold
  frames proportional to smearing, extra sampling step, chops them off) from a single report. The marker
  says `single report`; the prose does not read like one.

**Correctly hedged, for balance** — and this is genuinely well done: `SKILL.md:253` ("Treat Lightricks'
own comparison table as adversarial input … **No claim here comes from it**") is the single most
trustworthy paragraph in the skill, and the twelve-bullet unresolved list at `SKILL.md:271–282` is more
candid than any sibling's.

---

## Fit with the suite

**Reads as a sibling.** Heading sequence, marker grammar, two-bar section, date line, reference-file
table, `[`sibling`](../sibling/)` link form — all match `wan-2-2` and `minimax-h3` closely. The
licence-first block follows the `minimax-h3` precedent correctly (§2 slot 2, gate is legal not technical),
and the two-axis selector explicitly cites the `sdxl` precedent at `SKILL.md:43`, which is the right way
to justify a deviation.

**Positioning is accurate and does not oversell.** The suite table (`SKILL.md:236–251`) is unusually
willing to lose: "Exact motion transfer" is a ❌ with the practitioner quote explaining why people stay on
H3; "Consistent characters" is "Weak — face drift is unfixed"; "Raw prompt adherence and physics" is
"Weak relative to the field". All seven required video axes (§6.5) are present. `characters.md:5` leads
with "there is no reference-to-video mode" — leading a characters file with the model's disqualification
is exactly right.

**Backlinks already exist**, which surprised me: `wan-2-2/SKILL.md:13,162,248,252,254,256,267`,
`minimax-h3/SKILL.md:4,40,42,284,345` and `image-production-workflows/SKILL.md:34,121,125,139,143,194`
all link `[`ltx-2-5`](../ltx-2-5/)`. Bidirectionality (check 36) passes. Two stale sibling strings to fix
on publish: `minimax-h3/SKILL.md:345` still calls LTX "(gated licence, unverified here)", and
`image-production-workflows/SKILL.md:143` states the 64-divisibility rule without this skill's reconciliation.

**No duplication of a sibling's territory.** ReDetail is deliberately deferred to
`image-production-workflows` (`SKILL.md:190`), the RunPod volume contract to `comfyui-on-runpod`
(`SKILL.md:110`), and general LoRA craft to `character-lora-training` (`lora-training.md:3`). Correct.

**Two fit defects:**

- **`characters.md:89` links `[`scail-2`](../scail-2/)` — broken.** From `references/` that resolves to
  `ltx-2-5/scail-2/`. Every other link in the file uses `../../`. P1.
- **`scail-2` and `anima` are linked as published siblings** (`SKILL.md:242`, `characters.md:89`) but
  appear in neither `marketplace.json`, the README table, nor `freshness.json`. Per §6.5 an unpublished
  model is plain bold with a status word, never linked. Either these three ship together, or the links
  are wrong. Publish-order dependency, not a content error.

---

## Rubric

Graded against STANDARD.md §8. Word counts are raw `wc -w`; the §5.1 census uses a stricter count
(`minimax-h3` measures 18,025 raw against the census's 15,306, a ×0.85 factor), so census-equivalents are
given in brackets.

**A. Shape**

| # | Result |
|---|---|
| 1 (P1) | **FINDING** — `## Per-variant settings` / `## Per-mode settings` (slot 6, MANDATORY) is **absent**. Both video siblings have it (`wan-2-2:94`, `minimax-h3:154`). Twelve pipelines are enumerated at `SKILL.md:70–80` and settings are given for exactly one (`video_ltx2_5_t2v`). A reader running `DFRPipeline`, `KeyframeInterpolationPipeline`, `A2VidPipelineTwoStage`, `RetakePipeline` or `ICLoraPipeline` gets no steps/CFG/sampler/resolution/frames/fps. §7 clause 13 permits *per-mode* framing but not omission. |
| 2 (P2) | **PASS** — order matches §2. |
| 3 (P1) | **PASS** — all ten verbatim headings byte-exact. |
| 4 (P2) | **PASS** — two selectors, both with "Use when", `[pending release]` on the Video Editing IC-LoRA. |
| 5 (P1) | **PASS** — 12 rows, causes state mechanisms. One weak cell (`SKILL.md:208`, "Camera stays locked off … The default is a static frame") restates the symptom. P3. |
| 6 (P2) | **FINDING** — see A1. |
| 7 (P2) | **PASS** — 11 items. |

**B. References**

| # | Result |
|---|---|
| 8 (P1) | **PASS** — all four core slots present under canonical names, plus `licence-and-derivatives.md` as a §4.2 descriptive extra (justified by the clause-by-clause depth; the `licence-and-territory.md` name would misdescribe it). |
| 9 (P2) | **PASS** — no renames. |
| 10 (P2) | **PASS** — 5 rows for 5 files, each says when to read. |
| 11 (P2) | **PASS** — cross-pointers both ways (`lora-training.md:3` ↔ `setup-and-workflows.md:3,151`). |
| 12 (P3) | **PASS** — TOCs on the three ≥2,000-word files, spelled `Contents`. `licence-and-derivatives.md` at 1,974 w is borderline; add one. |
| 13 (P3) | **PASS** — numbered `## N.` throughout. |

**C. Depth**

| # | Result |
|---|---|
| 14 (P2) | **BORDERLINE PASS** — 17,635 raw [≈14,970 census] against the 10,000–16,000 band. Largest raw corpus in the suite. |
| 15 (P2) | **FINDING (P3)** — SKILL.md 6,551 raw [≈5,560] is just over the 5,500 absolute cap; share 37% is fine. Two §5.2 justifications apply (a licence that can rule the reader out; more task modes than the suite norm — twelve pipelines) but neither is **named** in the skill. Name one. |
| 16 (P1) | **PASS** — 296 lines. |
| 17 (P2) | **PASS** — references 1,339–3,181 w. |
| 18 (P2) | **PASS** — no padding section found. |
| 19 (P2) | **FINDING** — the stage-1/stage-2 sigma lists are given in full in both `SKILL.md:130–136` and `setup-and-workflows.md:45`; the file-layout table in full in both `SKILL.md:112–120` and `setup-and-workflows.md:57–69`; the HF gating paragraph three times (`SKILL.md:56`, `setup-and-workflows.md:73`, `licence-and-derivatives.md:99`). §5.3: SKILL.md keeps the rule and anchor number, the reference keeps the table. |
| 20 (P1) | **FINDING** — one silent-failure trap is stranded in a reference: "**the audio latent's frame count must match the video's**" (`setup-and-workflows.md:41`). Getting it wrong on a non-default frame count is a silent desync, not an error, and changing frame count is the first thing any reader does. Promote to SKILL.md's lattice section. |
| 21 (P2) | **PASS** — all three pillars covered, characters honestly routed. |

**D. Apparatus**

| # | Result |
|---|---|
| 22 (P3) | **PASS** — 318 words (band ceiling 320), folded `>`, all five §6.1 elements including "even obliquely:" and the closing routing note. |
| 23 (P1) | **PASS** — two-bar section at `##`, heading byte-identical, second-to-last. |
| 24 (P2) | **PASS** — all five elements, ~30 named community authors, twelve contested bullets. Best in the suite. |
| 25 (P1) | **PASS** — `**Facts dated 2026-08-22.**`, ISO, final paragraph, distinct from the release date at `SKILL.md:9`. |
| 26 (P1) | **FINDING (P2)** — markers are greppable, but two contested points are **asserted unhedged in the body** and marked only in the tail list: the enhancer-enabled claim (`SKILL.md:138` vs `:277`) and the VAE compression factors (`SKILL.md:150` vs `:281`). |
| 27 (P1) | **PASS** — zero italic-parenthetical markers. |
| 28 (P1) | **PASS** — no nested or unterminated markers. |
| 29 (P2) | **FINDING** — orphans listed above: `~24 GB` (`SKILL.md:223`), `~5–10 GB` (`setup-and-workflows.md:119`), `0.5–1.5` LoRA band (`:153`), bare `` `[community]` `` (`:183`). |
| 30 (P2) | **PASS** — attribution survives the summarise-up hop for the timing and VRAM figures. |
| 31 (P3) | **FINDING** — stray marker vocabulary: `[inference from the guide's own rule, not a vendor statement]` (`prompting-guide.md:87`, `characters.md:26`) uses a tier token outside the closed six and busts the ~60-char payload cap; `[community — ArttTaku; single source]` (`setup-and-workflows.md:155`) — the closed set has `single report`; `[contested — the README gives a word cap, the blog says "match length to complexity"]` (`prompting-guide.md:35`) is ~72 chars; `[community — u/ltx_model, vendor account]` (`lora-training.md:95`) is a vendor statement tiered as community. |
| 32 (P2) | **PASS** — 25 flagged/contested markers in SKILL.md. |
| 33 (P1) | **PASS** — every sibling mention is a relative link. |
| 34 (P1) | **FINDING** — `characters.md:89` `[`scail-2`](../scail-2/)` is **broken** (needs `../../scail-2/`). Nothing reaches above `skills/generative-media/`. |
| 35 (P2) | **PASS** — all seven video axes. |
| 36 (P2) | **PASS** — `wan-2-2`, `minimax-h3` and `image-production-workflows` all link back. Two stale strings to update on publish (see Fit). |
| 37 (P3) | **FINDING** — `scail-2` and `anima` are linked as published but are not registered anywhere. Publish-order dependency. |
| 38 (P3) | **PASS**. |

**E. Registration**

| # | Result |
|---|---|
| 39 (P1) | **FINDING** — absent from `.claude-plugin/marketplace.json` (`plugins[0].skills` lists ten, no `ltx-2-5`) and from the README table. The plugin `description` also still says "video (Wan 2.2, MiniMax H3)". |
| 40 (P1) | **FINDING** — absent from `freshness.json`. The only occurrence of "ltx" in that file is `ltx-2-5-licence-unread` inside **`minimax-h3`'s** watchlist — which this skill now resolves and which should be retired. Register at **hot** tier (an 11-day-old model, by the skill's own `SKILL.md:284`) with a watchlist covering all twelve contested bullets. |
| 41 (P2) | N/A until registered. |

**Summary: 5 P1 findings** (missing `## Per-mode settings`; stranded silent trap; broken `scail-2` link;
no marketplace/README registration; no `freshness.json` entry), **6 P2**, **5 P3** — plus the substantive
content findings above, which the rubric does not reach.

---

## My one question

**Where does the "2–4" range apply — shots, or cuts?**

I am asking this one rather than a licence question because it is the *only* number in the skill that a
reader cannot check, cannot infer, and will get wrong in the exact direction the skill pushes them. The
vendor quote you reproduce says **shots** (`prompting-guide.md:100`), your intro says **shots**
(`SKILL.md:11`), your failure table says **shots** (`SKILL.md:209`) — and your one-rule section, your
pre-flight checklist and `characters.md` all say **cuts**, with `characters.md:32` attributing "cuts" to
"the vendor's own range". A reader building the canonical demo — three cuts, four shots, one character —
is told by item 8 of your checklist that they are comfortably inside the range when by the number you
quoted they are at its ceiling, on the axis where you also document that identity is re-anchored per cut
from text alone and degrades with shorter beats. If it is cuts, the vendor quote is being paraphrased
wrongly. If it is shots, three of your own sections are one shot too generous on the model's single
headline capability.

And the follow-on that decides how bad it is: **does the four-rule protocol scale with cuts or with
shots?** Rule 3's re-identification cost is per *cut*; rule 2's re-establishment cost is per *shot*. You
cannot tune a 200-word budget across four shots without knowing which one the ceiling is counting.
