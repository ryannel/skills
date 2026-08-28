# MiniMax H3 — the licence, clause by clause

**This is not legal advice.** It is a reading guide to a document you should read yourself. If anything material rests on it, read it with a lawyer. Everything below is quoted or closely paraphrased from the `LICENSE` file in `MiniMaxAI/MiniMax-H3`. The licence is dated **2 August 2026**.

## The parties and the law

- **Licensor:** *"We," "Us" or "MiniMax" means* **Nanonoble Pte. Ltd.** This is a Singapore-registered entity. It is not the MiniMax consumer brand you may have dealt with elsewhere.
- **Governing law:** the laws of the **Hong Kong Special Administrative Region**. The licence expressly excludes conflict-of-laws rules and the UN Convention on Contracts for the International Sale of Goods.
- **Jurisdiction:** exclusive, in the courts of Hong Kong SAR. Both parties consent.
- **Formation:** the Agreement takes effect on *any* act of using, reproducing, modifying, distributing, running or displaying the works. You do not need to click "accept" to be bound.

## The territory clause

Three definitions chain together, and you have to follow all three:

> **§I.3** *"Applicable Territory" means worldwide, excluding the Excluded Territories.*
>
> **§I.5** *"Excluded Territories" means the European Union, the United Kingdom, the Republic of Korea and the United States of America.*
>
> **Exhibit A, prohibited use #1:** *Use outside the Applicable Territory.*

The grant in §II is made *"Solely within the Applicable Territory."* The distribution right in §III is *"solely within the Applicable Territory"* and only *"to Third Parties within the Applicable Territory."*

So the restriction operates twice. The licence **does not grant** rights outside the territory, and the Acceptable Use Policy separately **prohibits** use there. This is not an ambiguity or an oversight. The drafting is deliberate and consistent throughout the document.

**Why this is unusual.** Community licences in this space normally restrict by *revenue* (Krea, LTX), by *commercial use* (Ideogram weights), or by *acceptable use* (Llama-style). A restriction by *geography* is rare, and one that specifically excludes the US, EU, UK and Korea is rarer still. The pattern is consistent with avoiding the regulatory regimes of those jurisdictions rather than with protecting a market. But the licence does not state a reason, and this skill will not invent one.

**What it means in practice, stated carefully:** if you are in one of the excluded territories, you do not have a licence under this agreement, and the AUP lists your use as prohibited. Whether a Hong Kong-governed click-through is enforceable against you, what remedies exist, and how any of this interacts with your local law are exactly the questions this document cannot answer.

## If you are covered — the obligations that still apply

**Commercial threshold (§IV.1).** If you earn more than **US$20 million** in yearly revenue from the products or services involved, you need *"separate, prior written authorization"*. To request it, email `api@minimax.io` with the subject line *"MiniMax H3 licensing - authorization request"*.

**Mandatory attribution (§IV.2).** You *"shall prominently display 'MiniMax H3' on the user interface"* of any commercial product or service using it. This is a **shall**, so it is a requirement, distinct from the encouraged items below.

**Downstream binding (§V.2).** Before giving anyone access, including access through a hosted service, you must bind them to terms *"at least as protective as"* §V and Exhibit A, and notify them that the restrictions apply. If you build an API on top of H3, you become responsible for your users' compliance.

**Redistribution (§III).** All of the following apply:
1. Provide a copy of the Agreement to every third party receiving the works or using related products/services.
2. Cause modified files to *"carry prominent notices stating that you have modified such files."*
3. Ship a `NOTICE` text file with all distributions other than through hosted services, containing exactly:
   > *"MiniMax H3 is licensed under the MiniMax H3 Community License Agreement, Copyright © 2026 MiniMax. All Rights Reserved."*

You may add your own copyright notices to your modifications. But you **may not impose additional or different terms** on use, reproduction or distribution of them. Everything downstream must stay under this Agreement, and that includes the territory clause.

**Encouraged, not required (§III.3).** Three things are encouraged rather than mandated: displaying *"Powered by MiniMax H3"*, adding an AI-generation identifier to outputs, and publishing a technical blog post about your experience. It is worth knowing which of these are optional. The mandatory UI attribution in §IV.2 is easy to conflate with the encouraged notice in §III.3.a, and they are different obligations.

## Ownership

**§VI.1:** you own the derivative works, modifications and Model Derivatives you create. That ownership is subject to MiniMax's rights in the underlying works and to your compliance with the Agreement. **§VI.2:** there is no trademark licence beyond what is *"reasonably and customarily necessary to describe and distribute"* the works.

"Model Derivatives" is drawn widely. It covers any modification, any work based on the model, and *"any other machine learning model created by transferring the patterns of the weights, parameters, operational patterns, or Outputs"*. That definition reaches distillation and training on H3 output, not just fine-tuning.

## Exhibit A — Acceptable Use Policy

The AUP was last revised 2 August 2026, and **MiniMax reserves the right to update it**. That means the terms you accepted can change after the fact. It lists nineteen-plus prohibited categories. Beyond the obvious ones, these have teeth:

- **#1 Use outside the Applicable Territory** — the territorial restriction, restated as a use prohibition
- **#5** Circumventing or bypassing the safety guardrails
- **#6** Exploiting or harming minors
- **#9** Defamation, disparagement, harassment
- **#19** Military purposes

The rest run to the standard set: unlawful use, IP infringement, self-harm, harming others, and repurposing outputs to cause harm. Read the file for the full list, because the summary here is not a substitute.

## The encoder is licensed separately

An explicit note at the end of the licence says:

> *"Please note that the encoder of MiniMax H3 uses Qwen3-VL-32B, which is licensed under Apache 2.0 License."*

So the text encoder component carries permissive terms independent of the H3 licence. This does **not** rescue the rest of the model. The transformer, the VAEs and the system as a whole remain under the community licence, with its territory clause.

## Alternatives if the territory rules you out

| Model | Licence position |
|---|---|
| **[`wan-2-2`](../../wan-2-2/)** | **Apache 2.0, code and weights**, worldwide, commercial use included. No territory clause. It is the strongest open video model without this problem, and the suite's **licence-clean default**: the fallback when a territory or revenue clause has ruled the others out. It is not the community's default *generator*, though. The [`wan-2-2`](../../wan-2-2/) skill hands that position to H3 and claims the narrower role deliberately |
| **[`ltx-2-5`](../../ltx-2-5/)** | **LTX-2.x Community License Agreement** (11 Aug 2026), public ungated text on GitHub. Only the weights sit behind a Hugging Face contact-info gate. Free worldwide **below US$10M annual revenue** aggregated across affiliates, paid above it (evaluation and non-production R&D excepted). **LoRA adapters are Derivatives** and pass the obligation on to whoever uses them. Attachment A **¶20 bars competing with Lightricks' own products at any revenue**. The incorporated AUP **prohibits sexually explicit generation**, and its scope reaches on-premises deployments. This is a different axis of risk from H3's, not a milder one `[official — Lightricks/LTX-2 LICENSE.md + AUP]`. One point stays unsettled: which licence governs the older **LTX-2.3** weights, because the repo ships a January-2026 text while its own links point at the August one `[contested]` |
| **H3 hosted API / app** | `platform.minimax.io`, `hailuoai.video`, `hub.minimax.io`. These are governed by their own terms, **not** this Agreement. Read those terms separately before assuming they are more permissive |

## Re-verify

The licence is eleven days old as of this writing, and the AUP is explicitly amendable. Before relying on any of the above: re-read the `LICENSE` file in the repo, check whether the Excluded Territories list has changed, and check whether the two closed modules (Context-IR, Regenerate-2K) have been released under the same or different terms.
