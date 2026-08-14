# Publishing, likeness, and what makes a LoRA distributable

**Orientation, not legal advice.** This records what platforms and statutes actually say, with dates, so you can tell which constraints apply before spending training time. If real money or real exposure rides on it, ask a lawyer.

The reason this sits in a training skill at all: **these rules decide whether a finished LoRA can be published, and they constrain the dataset before you assemble it.** Finding out afterwards means the work was wasted.

---

## 1. Civitai: real-person likeness is prohibited outright

The largest host of community models now bans it completely. From their published content rules:

> *"Content that depicts, or is based on the likeness of real people - living or deceased - including public figures, celebrities, influencers, and private individuals, is strictly prohibited."*

The scope is wider than people expect:

| Covered | Notes |
|---|---|
| Living **and deceased** individuals | Including historical figures |
| Public figures, celebrities, influencers | No public-interest carve-out |
| **Private individuals** | Including yourself, for distribution purposes |
| Fictional characters **as portrayed by a real actor** | The output resembling the actor is what's prohibited, not the character |
| **SFW as well as NSFW** | This is not an adult-content rule. It is universal |

**The arguments the policy explicitly rejects:**

- *"They consented to being filmed/photographed."* Consent in one context does not extend to AI generation.
- *"It's for a fictional character, not the actor."* Training on a real actor's face is prohibited even when the depiction is fictional.
- *"It's a lookalike, not actually them."* If the result resembles an identifiable person, it is covered.

**The one thing that is allowed:** using a name in a prompt where the result does not resemble that person in any meaningful way. That is a statement about *outputs*, not a licence to train on someone.

Civitai frames the rationale as consent and privacy, and as future-proofing against tightening global regulation.

**Practical consequence:** a character LoRA trained on a real person cannot be published to the main community host, whatever its content rating. Plan for that before assembling the dataset, not after.

---

## 2. The TAKE IT DOWN Act — live and enforced

US federal law, and the reason platform policy moved when it did.

| | |
|---|---|
| Passed | 28 April 2025 |
| Signed | 19 May 2025 |
| Platform compliance deadline | **19 May 2026** |
| FTC enforcement began | **19 May 2026** |
| Civil penalty exposure | ~**$53,088 per violation** |

**What it does:** makes it a federal crime to knowingly share, or threaten to share, non-consensual intimate imagery — **explicitly including AI-generated images depicting real people**, where the depiction is *"indistinguishable from an authentic visual depiction."*

**What platforms must do:** implement notice-and-removal with a **48-hour** response window. "Covered platform" is defined broadly — any website, online service or application serving the public that primarily hosts user-generated content. That definition reaches well past the obvious hosts.

**What this means for a trainer:**

- The exposure attaches to *distribution* of the imagery, not to the existence of a model file — but a published LoRA whose evident purpose is generating NCII of an identifiable person is not a comfortable position under either the statute or any host's terms.
- **48-hour takedown is fast.** If you run any service that accepts user uploads, you are likely a covered platform and need a process.
- This is US law. The EU, UK and several other jurisdictions have their own instruments, and state-level deepfake statutes are still landing. **The picture is moving** — re-verify rather than trusting a snapshot.

---

## 3. Does a synthetic character count as a real person?

The genuine question people get stuck on: every base model was trained on photographs of real people, so is a character generated from one inherently a real-person likeness?

**No. The test is resemblance of the output, not provenance of the training data.**

- A character that does not resemble any identifiable individual is fine, even though the base model learned from real photographs. Every synthetic face is in some abstract sense a blend of many.
- A character that *does* resemble an identifiable individual is covered, even if you never deliberately trained on them. **Accidental resemblance still counts** — and this is a real risk when a dataset is small or a prompt names a celebrity's characteristics.
- The check is empirical: does anyone looking at it say "that's <name>"? If a reverse image search or a colleague identifies them, treat it as covered.

**This is why the synthetic dataset-factory route is worth preferring** for any character intended for distribution. Locking an anchor image that resembles nobody, then generating the varied set from it, gives you a character that is unambiguously yours — better coverage than photography, and no likeness question to answer.

---

## 4. Dataset provenance

Even where likeness is not at issue, where the images came from matters:

- **Scraped from social media or a paid-content platform** — resemblance aside, this typically breaches those platforms' terms and may involve people who never agreed to anything. It is also the sourcing pattern most likely to produce an accidental identifiable likeness.
- **Licensed stock** — check whether the licence permits AI training. Many now explicitly do not.
- **Your own photographs of consenting adults** — the cleanest sourcing, and still not publishable to Civitai under the real-person rule.
- **Synthetically generated** — cleanest overall. No third-party rights, no likeness question, and full control over coverage.

**Keep a record of where a dataset came from.** If a LoRA is ever challenged, provenance is the answer you need to have and cannot reconstruct later.

---

## 5. Where distribution is still open

The real-person rule closes one door, not all of them:

- **Original and synthetic characters** publish normally, adult content included, subject to the usual rating and metadata rules. NSFW uploads generally require metadata to stay visible in feeds.
- **Licensed and public-domain fictional characters** — subject to the actor clause where a live-action portrayal is involved.
- **Private use** is governed by law and your own judgement, not platform policy. The constraints there are the NCII statutes, which are about intimate imagery of real people regardless of where it is hosted.

**One rule worth internalising for anything involving a real person:** the direction of travel across every jurisdiction and platform is toward stricter, not looser. A workflow built on real-person likeness has a shortening shelf life independent of anyone's view about whether it should.
