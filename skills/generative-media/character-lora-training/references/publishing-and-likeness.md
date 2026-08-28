# Publishing, likeness, and what makes a LoRA distributable

**This file is orientation, not legal advice.** It records what platforms and statutes actually say, with dates, so you can work out which rules apply before you spend training time. If real money or real exposure rides on it, ask a lawyer.

Why does this sit in a training skill at all? Because **these rules decide whether a finished LoRA can be published, and they constrain the dataset before you assemble it.** If you find out afterwards, the work was wasted.

**Everything here is dated, because it moves.** Platform policy and statute are the two fastest-moving kinds of claim in this whole skill, and both changed within the last eighteen months. **Facts in this file were read on 2026-08-13.** The direction of travel is consistently toward stricter rules. Re-verify the specific rule you are relying on before you publish `[flagged — re-verify]`.

---

## 1. Civitai: real-person likeness is prohibited outright

The largest host of community models now bans real-person likeness completely. Their published content rules say:

> *"Content that depicts, or is based on the likeness of real people - living or deceased - including public figures, celebrities, influencers, and private individuals, is strictly prohibited."*

The scope is wider than people expect:

| Covered | Notes |
|---|---|
| Living **and deceased** individuals | Including historical figures |
| Public figures, celebrities, influencers | No exception for public interest |
| **Private individuals** | Including yourself, if you want to distribute it |
| Fictional characters **as played by a real actor** | What is banned is the output resembling the actor, not the character |
| **SFW as well as NSFW** | This is not an adult-content rule. It applies to everything |

**The policy rejects three common arguments by name:**

- *"They agreed to being filmed or photographed."* Agreeing in one context does not extend to AI generation.
- *"It's for a fictional character, not the actor."* Training on a real actor's face is banned even when the depiction is fictional.
- *"It's a lookalike, not actually them."* If the result resembles an identifiable person, it is covered.

**One thing is allowed:** using a name in a prompt, where the result does not meaningfully resemble that person. That is a statement about *outputs*. It is not permission to train on someone.

Civitai explains the rule as being about consent and privacy, and about getting ahead of regulation that keeps tightening.

**What this means in practice:** a character LoRA trained on a real person cannot be published to the main community host, at any content rating. Plan for that before you assemble the dataset, not after.

---

## 2. The TAKE IT DOWN Act — live and enforced

This is US federal law, and it is the reason platform policy moved when it did.

| | |
|---|---|
| Passed | 28 April 2025 |
| Signed | 19 May 2025 |
| Platform compliance deadline | **19 May 2026** |
| FTC enforcement began | **19 May 2026** |
| Civil penalty exposure | ~**$53,088 per violation** |

**What it does:** it makes it a federal crime to knowingly share, or threaten to share, non-consensual intimate imagery. That **explicitly includes AI-generated images of real people**, wherever the depiction is *"indistinguishable from an authentic visual depiction."*

**What platforms must do:** run a notice-and-removal process with a **48-hour** response window. "Covered platform" is defined broadly. It means any website, online service or application serving the public that mainly hosts user-generated content, and that definition reaches well past the obvious hosts.

**What it means for a trainer:**

- The legal exposure attaches to *distributing* the imagery, not to a model file existing. Even so, a published LoRA whose obvious purpose is generating NCII of an identifiable person is not a comfortable position to be in, under either the statute or any host's terms.
- **A 48-hour takedown window is fast.** If you run any service that accepts user uploads, you are probably a covered platform, and you need a process for handling notices.
- This is US law. The EU, the UK and several other jurisdictions have their own versions, and state-level deepfake statutes are still arriving. **The picture is still moving**, so re-verify rather than trusting a snapshot.

---

## 3. Does a synthetic character count as a real person?

This is the question people genuinely get stuck on. Every base model was trained on photographs of real people. So is a character generated from one automatically a real-person likeness?

**No. The test is whether the output resembles someone, not where the training data came from.**

- A character who does not resemble any identifiable individual is fine, even though the base model learned from real photographs. Every synthetic face is, in some abstract sense, a blend of many.
- A character who *does* resemble an identifiable individual is covered, even if you never meant to train on them. **Accidental resemblance still counts.** That is a real risk when a dataset is small, or when a prompt names a celebrity's features.
- The check is simple. Does anyone looking at it say "that's <name>"? If a reverse image search or a colleague identifies them, treat it as covered.

**This is why the synthetic dataset-factory route is worth preferring** for any character you intend to distribute. Lock an anchor image that resembles nobody, then generate the varied set from it. You get a character that is unambiguously yours, better coverage than photography gives you, and no likeness question to answer.

---

## 4. The model's licence follows the LoRA

Likeness is the constraint people expect. Licensing is the one that catches them by surprise: **on some models the base licence attaches to the adapter you train, and the obligation travels to whoever you give it to.**

[`ltx-2-5`](../../ltx-2-5/) is the sharp case in this suite. Its Community License names a **LoRA adapter as a Derivative** (§1.5, §3.5). It requires any Derivative to be distributed *"exclusively under the terms of this Agreement … with a complete copy of this Agreement included"* (§3.2). Then it goes further than most licences do: *"If the transferee is a Commercial Entity … it must obtain a paid license from Licensor prior to any use of any Derivative of LTX-2.x, **regardless of who created such Derivative**"* (§3.5). You have to notify recipients in writing, and you may not hand a Derivative to a Commercial Entity that lacks the licence. `[official — LTX-2.x Community License, 11 August 2026]`

Here is what that means for a trainer, concretely:

- **You cannot publish an LTX LoRA under a permissive licence.** Not MIT, not CC0, not "do what you like with it". The agreement does not give you the power to grant that.
- **Uploading it to a model host counts as distribution.** The host's licence picker probably offers nothing that matches, so check what the platform will actually stamp on your upload before you publish.
- **The obligation spreads, in a way likeness rules do not.** A real-person LoRA is a problem you own. A licence-inheriting LoRA is a problem you pass along. A studio downloads yours, is over the revenue threshold, and now needs a paid licence, whether or not they ever read your model card.
- **This is not unique to LTX in principle**, only in degree. Wherever the base weights are non-permissive, check what the licence says about derivatives before you train, not after you have something to publish. [`anima`](../../anima/)'s dual non-commercial position is another case.

The contrast worth holding on to is this: an **Apache-2.0 base** such as Wan 2.2 lets you publish the adapter on whatever terms you like. That difference costs nothing at training time and everything at distribution time. This is why it belongs in the base-model decision alongside anatomy coverage and VRAM.

---

## 5. Dataset provenance

Even where likeness is not the issue, where the images came from still matters:

- **Scraped from social media or a paid-content platform.** Resemblance aside, this usually breaks those platforms' terms, and it may involve people who never agreed to anything. It is also the sourcing pattern most likely to produce an accidental identifiable likeness.
- **Licensed stock.** Check whether the licence allows AI training. Many now explicitly do not.
- **Your own photographs of consenting adults.** This is the cleanest sourcing there is, and it is still not publishable to Civitai under the real-person rule.
- **Synthetically generated.** This is the cleanest option overall: no third-party rights, no likeness question, and full control over coverage.

**Keep a record of where a dataset came from.** If a LoRA is ever challenged, provenance is the answer you need to have, and you cannot reconstruct it later.

---

## 6. Where distribution is still open

The real-person rule closes one door, not all of them:

- **Original and synthetic characters** publish normally, adult content included, subject to the usual rating and metadata rules. NSFW uploads generally have to keep their metadata visible in feeds.
- **Licensed and public-domain fictional characters** publish too, subject to the actor clause where a live-action portrayal is involved.
- **Private use** is governed by law and your own judgement, not by platform policy. The constraints there are the NCII statutes, which cover intimate imagery of real people wherever it is hosted.

**One thing is worth internalising about anything involving a real person:** across every jurisdiction and platform, the rules keep getting stricter, never looser. A workflow built on real-person likeness has a shrinking shelf life, whatever anyone thinks about whether it should.
