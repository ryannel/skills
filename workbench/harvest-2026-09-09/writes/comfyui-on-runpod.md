# comfyui-on-runpod — 2026-09-09 write report

## Headline verified
Fetched both evidence URLs. v2.12.0 (2026-08-27) changelog: "fix(pod): remove --stop-after and --terminate-after" (#330). PR #330: flags forwarded but never enforced ("the pod keeps running, and billing, past the deadline"), no read-back, CPU pods dropped them, only RFC 3339 accepted; `unknown flag … usage_error` now; restoration #331 blocked on RunPod#5718. RunPod's scheduling guide (updated 2026-09-08) recommends explicit API terminate. Rewrite proceeded.

## Edits
- SKILL.md description — added trigger "runpodctl says unknown flag --terminate-after". (v2.12.0)
- SKILL.md routing table — dropped `--terminate-after` from the runpod router row.
- SKILL.md volume tree — added `frame_interpolation/ optical_flow/ …` line pointing at reference §2. (Comfy-Org example yaml)
- SKILL.md "Getting the weights there" — fallback-ladder sentence `[live-use 2026-09-01]`; multi-DC serverless volume attach with sync caveat. (golden path 19)
- SKILL.md pod-vs-serverless table — "Good for" and "Cold start" rows updated with measured 107–494 s `[live-use 2026-09-03]`; new "Long video jobs stay on pods" paragraph `[live-use 2026-09-01]`.
- SKILL.md "Cost guards that actually work" — full rewrite: no CLI timer (v2.12.0/PR #330); `[contested]` 2026-09-03 auto-stop; external scheduler + trap + `pod remove` as primary guard (RunPod guide); watchdog on pod with `[flagged]` self-terminate call; stop/terminate semantics kept, `/root` wipe and bulk-stop lesson added `[live-use]`; command-surface note re-based on 2.7.3–2.12.0 capability; burn check gains `runtimeStatus`.
- SKILL.md smoke test step 1 — `--wait` and `runtimeStatus` (v2.9.0); template's own ComfyUI on 8188 returning 400s, gate on the probe `[live-use 2026-09-01]`.
- SKILL.md failure table — rewrote surprise-bill, pod-vanished and `--docker-args` (v2.7.3) rows; added `unknown flag`, trainer-pod pointer row (→ reference §8), symlinked LoRA, 24 GB `VAEEncode` garbage `[live-use 2026-09-05]`, worker dying on long video `[live-use 2026-09-01]`.
- SKILL.md pre-flight — item 8 rewritten (clock outside the pod); new item 9 (SSH + driver ≥ 580); renumbered.
- SKILL.md two-bar — hard-fact roll-call and sources updated; craft bar names the media lab as second source; "nothing contested" replaced by one `[contested]` and one `[flagged]`; third live-pass paragraph; `Facts dated 2026-09-09` line.
- volume-and-models.md §1 — nine upstream keys added to both yaml blocks. §2 — "Keys added upstream" paragraph `[official]`. §3 — `optimizer.pt`/resume and copy-not-symlink paragraphs `[live-use]`. §6 — 250 GB quota mid-`rsync` paragraph `[live-use 2026-09-09]`. New §8 "Launching, watching and killing a pod job" (stock template, driver gate + hold-and-reroll, `PIP_CONSTRAINT`/HTTP-1.1, silent-launch catalogue, cgroup cap, kill by port, monitor-is-a-nudge, U+00A0 and zsh traps, datatype-before-price). TOC and intro updated.
- serverless-comfyui.md §1 — prebuilt-image claim softened with worker-comfyui 5.10.0 / z-image-turbo tag `[official]`. §3 — `serverless run/status/health`, `create --wait` (v2.9.0). §4 — measured cold start, warm ≠ base loaded, on-pod-eval ten-minute rule `[live-use]`, multi-DC attach. §5 — logs streaming (v2.10.0) lead-in; rows for VAE-encode garbage, bad worker, long-video worker death; "workers never warm" fix extended.

## Findings
Resolved: runpodctl-cost-guard-flags-removed, runpodctl-docker-args-now-supported (marked "not yet exercised live"), runpodctl-version-far-behind, extra-model-paths-new-keys, worker-comfyui-prebuilt-images-broader. Declined: none.

## Techniques
Added: external-scheduler-explicit-terminate, runpodctl-wait-flag-and-runtime-status, runpodctl-log-streaming, runpodctl-serverless-run-status-health, multi-dc-volume-attach-serverless. Media-lab items omitted as trivial or off-boundary: FaceDetailer-on-endpoint unreliability (single mention, no mechanism), unique eval-plan stems (lab-tooling specific), 5090 vs 4500 prices (skill declines GPU pricing), U+00A0 kept but one line only.

## Watchlist
- Add `runpodctl-cost-guard-removed-pending-restoration` as proposed; also watch the `[flagged]` self-terminate call and the `[contested]` 2026-09-03 auto-stop (did a watchdog fire?).
- Amend `runpodctl-cost-flags` and `runpodctl-surface-split` as proposed; both now moot as cost guards.
- Add: `--docker-args` on `pod create` unexercised live; worker-comfyui tag catalogue vs suite models.
- Resolved: none.

## Cross-skill
- `generative-media-atlas` and any skill quoting `--terminate-after` as the RunPod cost guard (grep the suite; `minimax-h3` and `character-lora-training` are likely) need the same correction.
- Memory note `runpod-cost-gate.md` says "always set --terminate-after"; update.

## Shape
SKILL.md is 5,800 words against the 2,000–3,200 cross-cutting band; it was 4,644 before this pass, so the overage is pre-existing but I widened it by ~1,150. Corpus is 11,652 against a 10,000 cap; `volume-and-models.md` is 3,781 (has a TOC per §6.7). Readability tangle 6.6/7.5/4.6, all under 15. Recommend the orchestrator file a §7 deviation or a split (cost guards into a third reference) for a later pass.
