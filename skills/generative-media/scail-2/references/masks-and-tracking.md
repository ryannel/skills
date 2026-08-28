# SCAIL-2 — masks, tracking and mode selection

Masks are SCAIL-2's control surface. This file covers them end to end. It explains what the two masks are, how `SCAIL2ColoredMask` builds them, and how the `replacement_mode` contract silently decides which job the model performs. It also explains how identities are selected and kept stable across a shot.

It does not cover graph wiring, which lives in [`setup-and-workflows.md`](setup-and-workflows.md) §1, or identity strategy, which lives in [`characters.md`](characters.md).

## Contents

1. [The two masks](#1-the-two-masks)
2. [The `replacement_mode` contract](#2-the-replacement_mode-contract)
3. [Choosing who gets tracked](#3-choosing-who-gets-tracked)
4. [Multiple references](#4-multiple-references)
5. [What the masks do not control](#5-what-the-masks-do-not-control)
6. [Verifying you are in the mode you think you are](#6-verifying-you-are-in-the-mode-you-think-you-are)

---

## 1. The two masks

**There are two masks, not one, and their rules differ.** Both come from the single core node `SCAIL2ColoredMask`, and both are built from SAM3 tracks. Both are also *coloured*: the colour is a per-identity palette entry, not a soft alpha. Every quotation below is a node tooltip from the ComfyUI source `[official — PR #14373 diff]`.

| | `reference_image_mask` | `pose_video_mask` |
|---|---|---|
| Built from | `ref_track_data` — *"SAM3 track of the reference image"* | `driving_track_data` — *"SAM3 track of the driving pose video"* |
| Tooltip | *"Colored reference mask at the same resolution as `reference_image`"* | *"Colored per-identity SAM3 mask video at the same resolution as `pose_video`"* |
| Background | **Always black** — *"`reference_image_mask` is always black-bg regardless"* | **Black = Animation Mode, white = Replacement Mode** |
| Colour means | Which identity each region of the reference belongs to | The same identity, so a colour ties a reference region to a tracked person |

---

## 2. The `replacement_mode` contract

**`replacement_mode` exists on two nodes, and they must agree.** The tooltip is explicit: *"False = mask_video has black bg (Animation Mode). True = white bg (Replacement Mode). Set the matching `replacement_mode` on `WanSCAILToVideo`."* Set the flag on `SCAIL2ColoredMask`, which paints the background accordingly, **and** on `WanSCAILToVideo`, which tells the model how to read it. If the two disagree, you hit the failure the vendor documents: *"Without a correct mask, Animation mode collapses into Replacement-mode behavior in certain inputs"*. The result is a plausible clip doing the wrong job, and no error is raised.

---

## 3. Choosing who gets tracked

Both inputs live on `SCAIL2ColoredMask`:

- **`object_indices`** — *"Comma-separated list of person indices to include (e.g. '0,2,3'). Applied to both reference and pose video masks. Empty = all."* This is the input the community calls "the Identity Tracker's object indices". It is part of the core node, not a custom pack.
- **`sort_by`** — `left_to_right` (default), `area`, or `none`. It fixes *"the order in which palette colors are assigned to the tracked objects (applied to both reference and pose video so each identity keeps the same color)"*. **If two characters swap identities between your reference and your clip, this is the knob to use.** Do not try to fix a swap by reordering the reference.

Upstream of both inputs, your SAM3 nodes decide *what* gets tracked. When the frame is crowded, community practice is to select subjects by **point** rather than by box, because *"if there are more people present, [box] could lead to problems"* `[community — External_Trainer_213]`. Box selection over a crowd is the likeliest source of the reported outline or glow on non-target people. [`characters.md`](characters.md) §5 covers that claim.

---

## 4. Multiple references

**Multiple references go on one canvas, not in a batch.** The `reference_image` tooltip says it plainly: *"Reference image, for multiple references composite all on single image."* Identities are separated by mask colour, not by batching. The community guidance to *"feed in same number of images in the ref image batch and the mask batch"* `[community — nsfwVariant]` describes an alternate workflow, not the core node's contract. If you are on the stock graph, composite the references instead.

---

## 5. What the masks do not control

**In practice, Replacement mode does not repaint only the masked person.** One practitioner reports that backgrounds change anyway, across multiple workflows, and the report is unexplained and unanswered `[community — Coach_Unable; single report]`. Workflows carrying **RMBG background retention** exist to fight this `[community — External_Trainer_213]`.

**One more input is available, and it is optional.** The README notes zero-shot support for **SAM3D-Body** mesh rendering as an advanced control intermediate. This is a different Meta model: it produces a body mesh, not segmentation tracking.

---

## 6. Verifying you are in the mode you think you are

A mismatched `replacement_mode` produces a clip rather than an error, so check it before you spend a full 40-step run:

1. **Preview the `pose_video_mask`.** Its background should be **black** for Animation and **white** for Replacement. If it looks inverted, the flag on `SCAIL2ColoredMask` is wrong.
2. **Confirm the same value on `WanSCAILToVideo`.** These are two separate widgets. Changing one does not change the other.
3. **Run 8 steps on the LightX2V path first.** The model decides the mode long before it decides detail, so a cheap preview shows you a wrong-mode failure right away. The giveaway is that the source scene survives when you asked for a new one, or the reverse.
4. **Check that `reference_image_mask` is black-backed** in both modes. It never flips.

A run that passes all four checks and still looks wrong is a craft problem, not a mode problem. Go to [`characters.md`](characters.md).
