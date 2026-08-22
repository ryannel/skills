# LTX-2.x licence, clause by clause

This file owns the licence in detail: the clause map, Attachment A's twenty restrictions, the derivative and output duties, and the unsettled question of which text governs LTX-2.3. SKILL.md carries the four gates a reader must know before downloading; this is what to read when a specific clause matters.

**Sources, all read from raw text rather than a summary page:** `raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE.md` (LTX-2.x Community License Agreement, 30,938 bytes, licence date 11 August 2026), `huggingface.co/Lightricks/LTX-2.3/raw/main/LICENSE` (LTX-2 Community License Agreement, 5 January 2026), and `static.lightricks.com/legal/ltx-acceptable-use-policy.pdf` (Acceptable Use Policy, last updated 30 March 2026, five pages). Licence commit history and per-repo gating come from the GitHub and Hugging Face APIs. **This is not legal advice.**

## Contents

1. [How to use this file](#1-how-to-use-this-file)
2. [The revenue threshold](#2-the-revenue-threshold)
3. [Attachment A — the twenty restrictions](#3-attachment-a--the-twenty-restrictions)
4. [The AUP, and why it reaches local weights](#4-the-aup-and-why-it-reaches-local-weights)
5. [Derivatives, redistribution and hosting](#5-derivatives-redistribution-and-hosting)
6. [Outputs](#6-outputs)
7. [Other terms](#7-other-terms)
8. [The LTX-2.3 question, unresolved](#8-the-ltx-23-question-unresolved)
9. [Gating, and what could not be reached](#9-gating-and-what-could-not-be-reached)

---

## 1. How to use this file

Sections below follow the agreement's own order: the revenue grant (§§1.6, 2.1, 2.2), Attachment A's twenty restrictions, the incorporated AUP, derivatives and redistribution (§§1.5, 3.1–3.6), outputs (§§5–6), the remaining terms (§§6, 7, 12–14), and the unresolved LTX-2.3 question.

## 2. The revenue threshold

SKILL.md quotes §2.1's operative sentence in full. Two things it does not cover:

**Aggregation (§1.6) is the part people miss.** The test is not your entity's revenue but the group's, counted collectively across subsidiaries, affiliates and companies under common control — so a wholly-owned production company inside a large media group is over the line on the group's numbers.

**§2.2's carve-out** lets a Commercial Entity use the model unpaid "solely for a Non-Commercial Purpose" — personal hobby or research use, or "use by a Commercial Entity for testing, evaluation, or non-commercial research and development in a non-production or development environment," provided no direct or indirect payment arises. Explicitly outside it: revenue-generating activity, anything with end-user impact, and training or fine-tuning any model for commercial use.

**Breach remedy** is unpaid fees for the period of use, at "Licensor's standard commercial license fees… or, absent published standard fees, a reasonable market rate," payable within 30 days of written demand.

**The paid tier's actual terms are unreachable.** §2.1 defers pricing to a document "as will be provided by the Licensor," obtainable only by emailing `ltxv-licensing@lightricks.com`. There is no published fee schedule — the breach clause's own "absent published standard fees" wording concedes it. `[flagged — re-verify]`

## 3. Attachment A — the twenty restrictions

Attachment A opens by incorporating the Acceptable Use Policy "into and made part of this Agreement by reference," then enumerates twenty prohibited uses. Four bite hardest:

- **¶20 — no competing products, at any revenue.** You may not use LTX-2.x "in any product, service, or application that directly competes with Licensor's commercial products or services, or is designed to replace or substitute Licensor's offerings in the market, without obtaining a separate commercial license." The clause says **"commercial products or services"** — unqualified, and not limited to video. Lightricks ships photo and design applications (Facetune, Photoleap) alongside LTX Studio and LTX Desktop, so this is a **field-of-use restriction with a wide and imprecisely-bounded surface**, and it has no revenue floor. The licence does not enumerate the products it protects, which is itself the problem: whether your tool competes is the whole question and the text will not answer it. It is the most commercially dangerous clause in the document and the one most often left out of summaries.
- **¶18 — no training other models, "for commercial use only."** The paragraph is scoped to commercial use and carves out Derivatives of LTX-2.x. **But the incorporated AUP imposes what reads as an unconditional version on everyone**, under "Do Not Abuse our Products": "Use or access our Products or any outputs to develop, modify, fine tune or improve any products or services that compete with our Products, including to develop, fine tune or train any artificial intelligence or machine learning algorithms or models of any kind." The narrower carve-out and the broader ban sit in the same instrument. A hobbyist distilling LTX output into another model is squarely in that gap. `[contested]`
- **¶17** bars military, weapons and nuclear applications; **¶19** bars circumventing watermarking or content filters, repeating §6; **¶5** requires disclosing output "without expressly and intelligibly disclaiming that the information and/or content is machine generated."
- **¶7 — no impersonation**, "e.g. deepfakes," without consent. The AUP adds that for commercial use, "users must assume responsibility for ensuring it does not replicate any real-world likeness, person, brand, or location unless independently cleared" — LTX's analogue of the real-person restrictions tracked in [`character-lora-training`](../../character-lora-training/).

## 4. The AUP, and why it reaches local weights

The AUP is a living document — Attachment A says Lightricks "may update it from time to time, and the version in effect at the time of your use governs," with no retroactive application to prior use.

The natural objection is that the AUP is written for Lightricks' hosted products — it discusses accounts and API keys — and so cannot bind a local checkpoint. **That reading does not survive the document.** The section sits inside the AUP's **Universal Usage Standards**, above and separate from its API-specific section; the AUP's own scope states that it "applies to anyone who uses Lightricks' Products," and defines Products as "made available on cloud-hosted basis and/or **on-premises deployments**." Attachment A then incorporates it wholesale with no carve-out. The prohibition binds local weights.

## 5. Derivatives, redistribution and hosting

- **Derivatives inherit and the obligation travels** — §3.2 and §3.5, quoted in SKILL.md. Note that §1.5's definition is generic ("any fine-tuned or adapted weights, parameters, or checkpoints derived from LTX-2.x"); **§3.5 is the only clause that names LoRA adapters**, in the parenthetical "(including any fine-tuned weights, LoRA adapters, or similar adaptations)". What SKILL.md omits: §3.2's inheritance is "subject to Section 3.6", and §3.5 adds a positive duty to **notify the transferee in writing** and a prohibition on transferring "any Derivative of LTX-2.x to a Commercial Entity unless such Commercial Entity has obtained the required paid license." That is what makes an open public download hard to reconcile with the licence: you cannot vet who downloads.
- **§3.5 ends with a carve-out that most summaries drop**, and it materially narrows the duty: *"Nothing in this Section 3.5 shall require a Commercial Entity to obtain a paid license for use solely for a Non-Commercial Purpose as permitted under Section 2.2."* A large company evaluating your LoRA in a dev environment is covered.
- **Redistribution and SaaS are permitted** — §3 allows hosting "for third parties remote access purposes (e.g. software-as-a-service)" and redistributing copies "in any medium, with or without modifications" — conditional on passing §4 and Attachment A through as enforceable terms, shipping the Agreement, marking modified files, and retaining notices.

## 6. Outputs

§5: "Except as set forth herein, Licensor claims no rights in the Output you generate using LTX-2.x. You are accountable for input you insert into LTX-2.x, the Output you generate and its subsequent uses. No use of the Output can contravene any provision as stated in the Agreement."

There is **no branding or attribution requirement** — the text was searched for one and it is absent, a genuine advantage over MiniMax H3's display obligation. But "outputs are yours, free and clear" overstates it: the grant is bounded by "Except as set forth herein," ¶5 imposes the machine-generated disclosure duty, and §6 forbids removing "any safety or security measures, disclosures, metadata, watermarking, content provenance, latent disclosure, or other transparency features." If Lightricks "reasonably believes" you have, it "may in its sole discretion **revoke the license** … effective immediately upon notice."

**Whether open-weights output actually embeds anything is undocumented.** The clause protects a mechanism that no public documentation describes. This matters because it is the only clause that can revoke the licence unilaterally. `[flagged — re-verify]`

## 7. Other terms

**§6** asks you to "undertake reasonable efforts to use the latest version," with non-current use "at your risk" — soft, but a small argument against pinning 2.3 indefinitely; it also states Lightricks "intends that LTX-2.x be treated as a free and open-source general purpose AI model within the meaning of Article 53(2) of the EU AI Act," pushing high-risk-system provider obligations onto you. **§7** is the only territorial term: a warranty that you are not in a comprehensively sanctioned territory or on a US restricted-party list — far narrower than [`minimax-h3`](../../minimax-h3/)'s exclusion of the US, EU, UK and South Korea. **§12** sets New York law and **§14** ICC arbitration seated in New York with jury-trial and class-action waivers, carved out for mandatory consumer-protection rights in the EU, UK and California. **§13** terminates your licence if you sue Lightricks over LTX-2.x or its Output, and on termination requires deleting all copies of the model *and derivatives* and notifying downstream recipients.

## 8. The LTX-2.3 question, unresolved

**Three live pointers, two different documents.** Do not state a resolution the sources do not support. `[contested]`

| Pointer | Resolves to |
|---|---|
| The `LICENSE` file shipped in `Lightricks/LTX-2.3` | **LTX-2 Community License Agreement, 5 January 2026** |
| That repo's `license_link` frontmatter | The **11 August 2026** text on GitHub |
| That repo's body link to `.../blob/main/LICENSE` | The **11 August 2026** text — Lightricks overwrote the repo-root `LICENSE` on 2026-08-12 |

Compounding it, **§1.9 of the new text scopes itself to "all LTX-2.5 versions released since August 11, 2026, and all future releases of LTX-2.x"** — wording that does not obviously reach backwards to 2.3. So the file says one thing, the links say another, and the scope clause says neither. Hugging Face's `license_name` label is `ltx-2-community-license-agreement` on **both** repos and does not distinguish them.

**Which one governs changes real exposure**, because the January text differs in two directions:

| | LTX-2 CLA (Jan 2026) | LTX-2.x CLA (Aug 2026) |
|---|---|---|
| Revenue threshold | $10,000,000 | $10,000,000 |
| Breach remedy | **Liquidated damages "equal to double the amount"** otherwise payable | Unpaid fees at standard or market rate |
| Non-Commercial carve-out | **Absent** | §2.2 |
| LoRAs named as Derivatives | **Not mentioned** | §3.5, explicitly |
| "Regardless of who created such Derivative" | **Absent** | §3.5 |

So the older text is harsher on damages and lacks the evaluation carve-out, while the newer one is more explicit about adapters. A studio over the threshold planning 2.3 work should get a written answer from Lightricks rather than choosing a reading. **Below the threshold, the safe default costs nothing: behave as though the January text governs.** It is strictly harsher — double liquidated damages, no evaluation carve-out — so complying with it complies with either, and a hobbyist needs no legal advice to adopt it.

## 9. Gating, and what could not be reached

**Gating is not a 2.5-only phenomenon.** `Lightricks/LTX-2.5`, `-Pre-Trained` and `-Diffusers` are `gated: auto`, requiring an account, acceptance of terms, and contact information with **consent "to receive offers and updates including targeted and personalized advertisements."** `Lightricks/LTX-2.3` itself is ungated — but **16 of 18 2.3 adapter repos are `gated: auto`**, including `Clean-Plate` and both plain-LoRA repos, with gates dating from **2026-07-26**, a fortnight *before* 2.5 shipped `[official — HF API, author=Lightricks]`. The dates matter for how you read the policy: gating was not a launch-day decision taken about 2.5, it was already Lightricks' default for adapters, so a 2.3-based plan inherits it rather than escaping it.

Three things could not be established, and all three are flagged where they are argued — §2 for the Commercial Use Agreement's terms and pricing, §8 for which licence Lightricks intends to govern 2.3: the paid tier's fees, email-only and nothing published; the 2.3 licence question, which needs a statement from Lightricks; and **whether the gated 2.5 repos ship an in-repo `LICENSE` differing from GitHub's** — the ungated 2.3 repo demonstrably does, making this a live risk rather than a theoretical one.
