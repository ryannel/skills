# Structural census — all published skills

Generated from the files themselves. Word counts are per-section body (excluding the heading).


---

## character-lora-training

- frontmatter keys: ['description', 'name']
- description: 221 words, 1408 chars
- SKILL.md: 2643 words, 9 headings
- tables in SKILL.md: 46
- provenance markers: flagged=1, contested=1, community=0, pending=0

### SKILL.md heading tree

- # Character LoRA training  _(146w)_
  - ## Before anything: can you publish it?  _(321w)_
  - ## The one rule that changes everything  _(203w)_
  - ## The dataset  _(345w)_
  - ## Hyperparameters as starting points  _(161w)_
  - ## Evaluating a run  _(568w)_
  - ## Adult and NSFW work  _(472w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(208w)_
  - ## Reference files  _(166w)_

### references


**dataset-and-captioning.md** — 1406w, 7 headings
- # Datasets and captioning  _(34w)_
  - ## 1. Size and curation  _(164w)_
  - ## 2. The coverage protocol  _(254w)_
  - ## 3. The synthetic dataset factory  _(195w)_
  - ## 4. Captioning  _(263w)_
  - ## 5. Multi-outfit and multi-character  _(198w)_

**evaluation-and-tooling.md** — 2912w, 13 headings
- # Evaluating a run: tooling and protocol  _(152w)_
  - ## 1. Layer 1 — samples during training  _(327w)_
  - ## 2. Layer 2 — the grid, and the tools that build it  _(350w)_
  - ## 3. Layer 3 — judging without fooling yourself  _(379w)_
  - ## 4. The held-out probe set  _(71w)_
- # baseline — should always work; if these fail, something is broken  _(27w)_
- # coverage — the angles and framings datasets usually miss  _(32w)_
- # flexibility — nothing like the dataset; this is where overfit shows  _(161w)_
  - ## 5. Putting a number on it  _(365w)_
  - ## 6. What a run costs  _(250w)_
  - ## 7. What to build yourself  _(219w)_
  - ## 8. What the professional tier does  _(306w)_
  - ## How to read the claims in this file  _(161w)_

**nsfw-training.md** — 1676w, 8 headings
- # Adult and NSFW LoRA training  _(73w)_
  - ## 1. The limit is data, not refusal  _(284w)_
  - ## 2. Base model selection by family  _(181w)_
  - ## 3. Captioning  _(196w)_
  - ## 4. Anatomy failure modes  _(215w)_
  - ## 5. Video  _(191w)_

**publishing-and-likeness.md** — 1103w, 6 headings
- # Publishing, likeness, and what makes a LoRA distributable  _(75w)_
  - ## 1. Civitai: real-person likeness is prohibited outright  _(272w)_
  - ## 2. The TAKE IT DOWN Act — live and enforced  _(242w)_
  - ## 3. Does a synthetic character count as a real person?  _(194w)_
  - ## 4. Dataset provenance  _(136w)_
  - ## 5. Where distribution is still open  _(134w)_

---

## comfyui-on-runpod

- frontmatter keys: ['description', 'name']
- description: 185 words, 1159 chars
- SKILL.md: 2940 words, 14 headings
- tables in SKILL.md: 46
- provenance markers: flagged=0, contested=0, community=0, pending=0

### SKILL.md heading tree

- # ComfyUI on RunPod  _(38w)_
  - ## What this owns, and what it doesn't  _(160w)_
  - ## The one rule that changes everything  _(394w)_
  - ## Volume layout  _(314w)_
  - ## The manifest — how a fresh volume becomes the old volume  _(174w)_
  - ## Getting the weights there without burning GPU hours  _(171w)_
  - ## Pod or serverless?  _(331w)_
  - ## Deploying and running workflows  _(177w)_
  - ## Smoke test before you trust it  _(169w)_
    - ### Ask the worker what it can see, instead of guessing  _(164w)_
  - ## Failure modes & QC  _(293w)_
  - ## Pre-flight checklist  _(134w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(257w)_
  - ## Reference files  _(68w)_

### references


**serverless-comfyui.md** — 1198w, 6 headings
- # ComfyUI as a serverless endpoint  _(46w)_
  - ## 1. The four moving pieces  _(210w)_
  - ## 2. API format vs UI format  _(215w)_
  - ## 3. Dispatch and polling  _(247w)_
  - ## 4. Scaling and cost shape  _(193w)_
  - ## 5. Failure modes  _(253w)_

**volume-and-models.md** — 1404w, 7 headings
- # Volume layout, `extra_model_paths.yaml`, and the model manifest  _(36w)_
  - ## 1. The dual mount root, in full  _(256w)_
  - ## 2. Placement table  _(256w)_
  - ## 3. LoRA organisation and compatibility  _(237w)_
  - ## 4. The manifest schema  _(243w)_
  - ## 5. Populating and rebuilding a volume  _(200w)_
  - ## 6. Custom nodes  _(134w)_

---

## flux-2

- frontmatter keys: ['description', 'name']
- description: 264 words, 2049 chars
- SKILL.md: 3922 words, 24 headings
- tables in SKILL.md: 74
- provenance markers: flagged=0, contested=0, community=0, pending=1

### SKILL.md heading tree

- # FLUX.2  _(188w)_
  - ## Variant selector  _(291w)_
  - ## The one rule that changes everything  _(400w)_
  - ## Setup & ecosystem  _(35w)_
    - ### FLUX.2 [dev] — text-to-image file layout  _(138w)_
    - ### FLUX.2 [klein] 4B — file layout  _(77w)_
    - ### Key ComfyUI node changes from Flux.1  _(81w)_
    - ### Quantisation  _(85w)_
    - ### Pose control (ControlNet)  _(65w)_
    - ### Face identity (PuLID)  _(69w)_
    - ### diffusers  _(76w)_
  - ## Per-variant settings  _(0w)_
    - ### [dev] — 32B guidance-distilled  _(68w)_
    - ### [klein] 4B — distilled (Apache 2.0)  _(52w)_
    - ### [klein] 9B — distilled / 9B KV  _(43w)_
  - ## Realism — the FLUX.2 approach  _(137w)_
  - ## Production pipelines & mixing models  _(227w)_
  - ## Failure modes & QC  _(245w)_
  - ## Pre-flight checklist  _(134w)_
  - ## Where FLUX.2 sits in the suite  _(227w)_
  - ## Licence & limitations  _(186w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(336w)_
  - ## FLUX 3 — announced, not available, and not an image model in the usual sense  _(362w)_
  - ## Reference files  _(263w)_

### references


**api-and-bfl.md** — 1203w, 12 headings
- # FLUX.2 — BFL Hosted API  _(42w)_
  - ## Contents  _(34w)_
  - ## 1. Endpoints and regions  _(37w)_
  - ## 2. Authentication  _(30w)_
  - ## 3. API model slugs and capabilities  _(141w)_
  - ## 4. Request format and parameters  _(238w)_
  - ## 5. Async polling pattern  _(142w)_
  - ## 6. Python example  _(100w)_
- # Usage  _(53w)_
  - ## 7. Commercial use via API  _(126w)_
  - ## 8. API pricing (community-tier — verify at bfl.ai/pricing)  _(100w)_

**characters.md** — 1365w, 7 headings
- # FLUX.2 Characters — creating a consistent character  _(71w)_
  - ## 1. Choose the path  _(251w)_
  - ## 2. Multi-reference as the character engine  _(246w)_
  - ## 3. The character LoRA pipeline  _(297w)_
  - ## 4. Beyond the face  _(160w)_
  - ## 5. Failure modes & fixes  _(232w)_
  - ## Sources & confidence  _(67w)_

**controlnet-and-identity.md** — 1470w, 19 headings
- # FLUX.2 — Pose Control & Identity Preservation  _(25w)_
  - ## Contents  _(32w)_
  - ## 1. Why Flux.1 ControlNets don't work on FLUX.2  _(85w)_
  - ## 2. ControlNet (Alibaba PAI Fun Union)  _(12w)_
  - ## 3. PuLID — face identity (iFayens)  _(40w)_
  - ## 4. IP-Adapter face — status  _(69w)_
  - ## 5. ReferenceLatent — native reference conditioning  _(115w)_

**lora-training.md** — 1553w, 8 headings
- # FLUX.2 LoRA Training  _(123w)_
  - ## Tooling  _(181w)_
  - ## The official reference config  _(212w)_
  - ## Hyperparameters  _(246w)_
  - ## Dataset & captioning — caption the residual, in prose  _(186w)_
  - ## Style LoRAs — the specifics  _(162w)_
  - ## Adult / NSFW work  _(174w)_
  - ## Assessing fit — judge by images, not loss  _(226w)_

**prompting-guide.md** — 2480w, 23 headings
- # FLUX.2 — Prompting Guide  _(20w)_
  - ## Contents  _(47w)_
  - ## 1. Anatomy  _(210w)_
  - ## 2. What the encoder actually parses  _(202w)_
  - ## 3. Hex color control  _(159w)_
  - ## 4. JSON for production (optional, not required)  _(254w)_
  - ## 5. Realism vocabulary: camera, lens, film stock  _(30w)_
  - ## 6. Multi-reference image editing  _(131w)_
  - ## 7. Text-in-image guidance  _(176w)_
  - ## 8. Drop-in prompt templates  _(0w)_
  - ## 9. Common mistakes and corrections  _(244w)_

**setup-and-workflows.md** — 1882w, 16 headings
- # FLUX.2 — Setup & Workflows Reference  _(28w)_
  - ## Contents  _(45w)_
  - ## 1. VRAM requirements table  _(235w)_
  - ## 2. ComfyUI — [dev] image-edit template  _(205w)_
  - ## 3. ComfyUI — [klein] 9B templates  _(114w)_
  - ## 4. ComfyUI — [klein] 9B KV template  _(146w)_
  - ## 5. ComfyUI — GGUF quants (community)  _(153w)_
  - ## 6. diffusers — detailed setup  _(45w)_
- # Standard load (requires ~20 GB VRAM)  _(7w)_
- # OR: CPU offload (works on <16 GB VRAM, slower)  _(1w)_
- # OR: Group offloading (finer-grained memory management)  _(0w)_
- # pipe.enable_group_offload(onload_device=torch.device("cuda"), offload_device=torch.device("cpu"), offload_type="block_level")  _(63w)_
- # Load exactly as Flux2KleinPipeline but with the KV class  _(158w)_
- # See HF bitsandbytes integration docs for full pattern  _(2w)_
  - ## 7. Using LoRAs  _(486w)_
  - ## 8. LoRA training → `references/lora-training.md`  _(88w)_

---

## ideogram-4

- frontmatter keys: ['description', 'name']
- description: 280 words, 1897 chars
- SKILL.md: 4571 words, 14 headings
- tables in SKILL.md: 52
- provenance markers: flagged=0, contested=0, community=0, pending=0

### SKILL.md heading tree

- # Ideogram 4  _(306w)_
  - ## The one rule that changes everything  _(249w)_
  - ## The JSON caption schema (canonical)  _(333w)_
  - ## Rendering speed, steps & guidance  _(246w)_
  - ## Caption craft — the high-leverage rules  _(428w)_
  - ## Realism the Ideogram way (the *opposite* default to most models)  _(284w)_
  - ## Text rendering & typography (the headline strength)  _(247w)_
  - ## Setup & ecosystem  _(503w)_
    - ### ComfyUI (day-0 native support)  _(342w)_
  - ## Failure modes & QC  _(295w)_
  - ## Pre-flight checklist  _(135w)_
  - ## Where Ideogram 4 sits in the suite  _(256w)_
  - ## Licence & limitations  _(714w)_
  - ## Reference files  _(153w)_

### references


**api-and-webapp.md** — 1365w, 12 headings
- # Ideogram 4 Hosted API & Web App  _(130w)_
  - ## 1. Auth & base  _(72w)_
  - ## 2. Generate — `POST /v1/ideogram-v4/generate`  _(192w)_
  - ## 3. Magic Prompt — `POST /v1/ideogram-v4/magic-prompt`  [confirmed from client source]  _(85w)_
  - ## 4. Other v4 endpoints  _(136w)_
  - ## 5. Pricing & credits  _(0w)_
  - ## 6. Web app features (v4)  _(250w)_
  - ## 7. Commercial usage  _(116w)_

**json-caption-guide.md** — 3436w, 24 headings
- # Ideogram 4 JSON Caption Guide  _(75w)_
  - ## 1. The schema  _(89w)_
  - ## 2. Plain text vs JSON vs Magic Prompt  _(229w)_
  - ## 3. Caption-craft rules (from Ideogram's Magic Prompt system prompt)  _(30w)_
  - ## 4. Bounding-box strategy  _(149w)_
  - ## 5. Realism — the Ideogram way  _(320w)_
  - ## 6. Text rendering, typography & multilingual  _(166w)_
  - ## 7. Color-palette conditioning  _(96w)_
  - ## 8. Transparency / cutouts  _(45w)_
  - ## 9. Drop-in templates  _(0w)_

**self-hosting.md** — 2290w, 20 headings
- # Self-Hosting Ideogram 4 (open weights)  _(146w)_
  - ## 1. Model access (gating)  _(120w)_
  - ## 2. diffusers  _(140w)_
  - ## 3. The `run_inference.py` CLI  _(211w)_
  - ## 4. ComfyUI (day-0 native support)  _(75w)_
  - ## 5. Safety filter (self-hosted)  _(118w)_
  - ## 6. LoRA training & fine-tuning  _(63w)_

---

## image-production-workflows

- frontmatter keys: ['description', 'name']
- description: 206 words, 1500 chars
- SKILL.md: 2574 words, 13 headings
- tables in SKILL.md: 55
- provenance markers: flagged=0, contested=0, community=1, pending=0

### SKILL.md heading tree

- # Image Production Workflows  _(165w)_
  - ## The production ladder  _(177w)_
  - ## The one rule that changes everything  _(179w)_
  - ## Mixing models — the three handoff rules  _(207w)_
  - ## Tool status that changed recently (mid-2026)  _(184w)_
    - ### A video model is now a legitimate stage in an image pipeline  _(205w)_
    - ### Generative upscaling versus restoration  _(217w)_
  - ## Workflows as code  _(144w)_
  - ## Failure modes & QC  _(256w)_
  - ## Pre-flight checklist  _(115w)_
  - ## The suite map  _(310w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(237w)_
  - ## Reference files  _(96w)_

### references


**mixed-model-recipes.md** — 1159w, 7 headings
- # Mixed-Model Recipes — cross-family handoffs and the control stack  _(67w)_
  - ## Contents  _(26w)_
  - ## 1. The three handoff rules  _(273w)_
  - ## 2. Named recipes  _(369w)_
  - ## 3. The structural-control stack, per family (mid-2026)  _(198w)_
  - ## 4. Regional prompting status  _(83w)_
  - ## 5. Identity across a mixed pipeline  _(101w)_

**production-ladder.md** — 1168w, 10 headings
- # The Production Ladder — multi-stage settings in depth  _(34w)_
  - ## Contents  _(42w)_
  - ## 1. Base generation & the two-pass discipline  _(143w)_
  - ## 2. The hires / refine second pass  _(123w)_
  - ## 3. Detailers  _(167w)_
  - ## 4. Tiled diffusion upscale  _(145w)_
  - ## 5. Final restorers & GAN upscalers  _(152w)_
  - ## 6. Inpainting craft  _(116w)_
  - ## 7. Color management  _(94w)_
  - ## 8. Detail tricks  _(98w)_

**workflows-as-code.md** — 953w, 7 headings
- # Workflows as Code — ComfyScript, the API route, comfy-cli, diffusers, and pro conventions  _(25w)_
  - ## Contents  _(34w)_
  - ## 1. The four code routes, compared  _(125w)_
  - ## 2. ComfyScript  _(189w)_
  - ## 3. The native API route  _(134w)_
  - ## 4. diffusers as the code-first alternative  _(92w)_
  - ## 5. Pro conventions  _(311w)_

---

## krea-2

- frontmatter keys: ['description', 'name']
- description: 313 words, 2088 chars
- SKILL.md: 5292 words, 23 headings
- tables in SKILL.md: 58
- provenance markers: flagged=1, contested=0, community=31, pending=1

### SKILL.md heading tree

- # Krea 2  _(230w)_
  - ## Variant selector  _(428w)_
  - ## The one rule that changes everything  _(557w)_
  - ## Setup & ecosystem  _(21w)_
    - ### File layout  _(61w)_
    - ### Stock node settings (template JSON, verbatim)  _(146w)_
    - ### Quantisation & VRAM  _(208w)_
    - ### diffusers  _(29w)_
- # Turbo: is_distilled=True in the pipeline config → fixed mu=1.15; num_inference_steps=8, guidance_scale=0.0  _(40w)_
    - ### Hosted surfaces  _(59w)_
  - ## Per-variant settings  _(0w)_
    - ### Turbo (the local workhorse)  _(173w)_
    - ### Raw (the training base)  _(129w)_
    - ### Medium / Large (hosted)  _(33w)_
  - ## The anti-AI-look and its two taxes  _(262w)_
  - ## Production pipelines & mixing models  _(430w)_
  - ## LoRA training & characters (summary — full treatment in references)  _(424w)_
  - ## Failure modes & QC  _(357w)_
  - ## Pre-flight checklist  _(161w)_
  - ## Where Krea 2 sits in the suite  _(367w)_
  - ## Licence & limitations  _(267w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(575w)_
  - ## Reference files  _(207w)_

### references


**api-and-hosted.md** — 718w, 7 headings
- # Krea 2 — API & hosted surfaces  _(60w)_
  - ## Contents  _(30w)_
  - ## 1. Hosted vs open — what's actually different  _(157w)_
  - ## 2. The Krea API  _(196w)_
  - ## 3. The web app  _(67w)_
  - ## 4. ComfyUI partner nodes  _(55w)_
  - ## 5. fal (and other hosts) for the open models  _(109w)_

**characters.md** — 2228w, 11 headings
- # Krea 2 — Consistent characters  _(37w)_
  - ## Contents  _(34w)_
  - ## 1. The state of identity tooling  _(255w)_
  - ## 2. The character-LoRA pipeline  _(640w)_
  - ## 3. The nearest no-training tools (young)  _(394w)_
  - ## 4. Deployment: the detailer-stage swap  _(90w)_
  - ## 5. Multi-outfit, multi-character  _(93w)_
  - ## 6. Failure modes  _(164w)_
  - ## 7. When to use another model  _(220w)_

**lora-training.md** — 3070w, 13 headings
- # Krea 2 — LoRA training  _(81w)_
  - ## Contents  _(60w)_
  - ## 1. The doctrine — and the dispute  _(323w)_
  - ## 2. musubi-tuner (the fullest documented path)  _(469w)_
  - ## 2a. Training on 12 GB — the low-VRAM configuration  _(250w)_
  - ## 2b. Adult / NSFW work  _(298w)_
  - ## 2c. 16 GB, measured — and four corrections that came out of it  _(455w)_
  - ## 3. AI-Toolkit and the Ostris turbo-adapter path  _(234w)_
  - ## 4. fal hosted trainer  _(24w)_
  - ## 5. Captioning doctrine  _(188w)_
  - ## 6. Character LoRAs: two named recipes  _(239w)_
  - ## 7. Style LoRAs  _(246w)_
  - ## 8. Evaluation  _(119w)_

**prompting-guide.md** — 1668w, 9 headings
- # Krea 2 — Prompting guide  _(69w)_
  - ## Contents  _(31w)_
  - ## 1. The two registers that work  _(243w)_
  - ## 2. Prompt anatomy  _(241w)_
  - ## 3. Realism & texture vocabulary  _(239w)_
  - ## 4. Text rendering  _(68w)_
  - ## 5. Style: LoRAs, references, moodboards, creativity  _(360w)_
  - ## 6. The prompt expander  _(183w)_
  - ## 7. Common mistakes  _(189w)_

**setup-and-workflows.md** — 1907w, 16 headings
- # Krea 2 — Setup & workflows  _(41w)_
  - ## Contents  _(37w)_
  - ## 1. ComfyUI: the official template, node by node  _(283w)_
  - ## 2. Quantisation & VRAM  _(350w)_
  - ## 3. The reference CLI  _(24w)_
- # Raw — full sampler with CFG; trained to 1K  _(15w)_
- # Turbo — 8 steps, CFG off, pinned mu; 1K–2K  _(72w)_
  - ## 4. diffusers  _(151w)_
  - ## 5. The Wan 2.1 VAE swap  _(154w)_
  - ## 6. Using LoRAs  _(156w)_
  - ## 7. Multi-stage workflows  _(0w)_
  - ## 8. Krea 2 in mixed-model pipelines  _(193w)_

---

## minimax-h3

- frontmatter keys: ['description', 'name']
- description: 284 words, 1937 chars
- SKILL.md: 6460 words, 25 headings
- tables in SKILL.md: 104
- provenance markers: flagged=6, contested=2, community=17, pending=1

### SKILL.md heading tree

- # MiniMax H3  _(143w)_
  - ## Before anything else — the licence and the territory  _(450w)_
  - ## What "open weights" means here — one module of three  _(284w)_
  - ## Task-mode selector  _(457w)_
  - ## The one rule that changes everything  _(244w)_
  - ## Setup & ecosystem  _(16w)_
    - ### File layout  _(231w)_
    - ### Sampling  _(49w)_
    - ### Do not swap in a "heretic" / abliterated text encoder  _(289w)_
    - ### diffusers  _(35w)_
  - ## Going faster — the acceleration stack  _(48w)_
    - ### Layer 0: the runtime, which is where most of the speed is hiding  _(195w)_
    - ### Layer 1: sparse attention (SLA) — the biggest single win  _(138w)_
    - ### Layer 2: Spectrum — and the audio failure that is worth understanding  _(365w)_
    - ### Layer 3: the Turbo LoRA, and what it costs the audio  _(408w)_
  - ## Frame count and resolution — two rules the UI hides  _(292w)_
  - ## Beyond one clip — three modes the templates do not show you  _(31w)_
    - ### Long-form: context chaining  _(193w)_
    - ### H3 as a single-image edit model  _(175w)_
    - ### Video editing — replacing a character in existing footage  _(336w)_
  - ## Failure modes & QC  _(690w)_
  - ## Pre-flight checklist  _(195w)_
  - ## Where MiniMax H3 sits in the suite  _(283w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(564w)_
  - ## Reference files  _(157w)_

### references


**characters.md** — 1335w, 9 headings
- # MiniMax H3 — characters and identity  _(80w)_
  - ## The Ref2VA budget  _(142w)_
  - ## Build the identity as stills first  _(114w)_
  - ## The voice is part of the identity  _(128w)_
  - ## Across shots  _(141w)_
  - ## What H3 cannot do here that `wan-2-2` can  _(163w)_
  - ## Failure modes  _(164w)_

**licence-and-territory.md** — 1139w, 9 headings
- # MiniMax H3 — the licence, clause by clause  _(45w)_
  - ## The parties and the law  _(96w)_
  - ## The territory clause  _(264w)_
  - ## If you are covered — the obligations that still apply  _(272w)_
  - ## Ownership  _(85w)_
  - ## Exhibit A — Acceptable Use Policy  _(107w)_
  - ## The encoder is licensed separately  _(65w)_
  - ## Alternatives if the territory rules you out  _(94w)_
  - ## Re-verify  _(56w)_

**loras-and-training.md** — 1589w, 9 headings
- # MiniMax H3 — LoRAs and training  _(98w)_
  - ## What exists  _(556w)_
  - ## The one thing you must get right  _(112w)_
  - ## Which checkpoint to train  _(82w)_
  - ## Before you train, ask whether you need to  _(90w)_
  - ## Datasets, if and when  _(104w)_
  - ## Evaluating  _(121w)_
  - ## Adult / NSFW work  _(326w)_
  - ## Re-verify  _(54w)_

**prompting-guide.md** — 2191w, 16 headings
- # MiniMax H3 — prompting guide  _(131w)_
  - ## 1. The audio half  _(162w)_
  - ## 2. Prompt anatomy  _(135w)_
  - ## 3. Soundscape vocabulary  _(159w)_
  - ## 4. Dialogue  _(113w)_
  - ## 5. Picture and camera  _(102w)_
  - ## 6. Approximating H3-Context-IR  _(274w)_
  - ## 7. Worked examples  _(205w)_
  - ## 8. Ordering, timing and the shot list  _(38w)_
  - ## 9. Prompt tooling  _(213w)_

**setup-and-workflows.md** — 2592w, 13 headings
- # MiniMax H3 — setup & workflows  _(74w)_
  - ## 1. The graph  _(167w)_
  - ## 2. File layout and builds  _(255w)_
  - ## 3. Frame count  _(138w)_
  - ## 4. Resolution  _(178w)_
  - ## 4a. Deploying on rented GPUs  _(330w)_
  - ## 5. FL2VA vs Ref2VA wiring  _(191w)_
  - ## 6. Production pipeline and the 768p ceiling  _(359w)_
  - ## 7. Going long — context chaining  _(160w)_
  - ## 8. Single-frame image editing  _(173w)_

---

## sdxl

- frontmatter keys: ['description', 'name']
- description: 249 words, 1802 chars
- SKILL.md: 3889 words, 15 headings
- tables in SKILL.md: 62
- provenance markers: flagged=0, contested=0, community=0, pending=0

### SKILL.md heading tree

- # Stable Diffusion XL (SDXL)  _(168w)_
  - ## Two orthogonal axes — they compose  _(93w)_
    - ### Speed variants (the fast axis)  _(277w)_
    - ### Checkpoints (the style axis) — you want a finetune, not raw base  _(172w)_
  - ## The one rule that changes everything  _(394w)_
  - ## Setup & ecosystem  _(419w)_
  - ## Per-variant settings  _(224w)_
  - ## Realism: pick a finetune, then stack the gear  _(298w)_
  - ## Production pipelines & mixing models  _(224w)_
  - ## Failure modes & QC  _(280w)_
  - ## Pre-flight checklist  _(133w)_
  - ## Where SDXL sits in the suite  _(200w)_
  - ## Licence & limitations  _(307w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(287w)_
  - ## Reference files  _(316w)_

### references


**characters.md** — 1410w, 8 headings
- # SDXL Characters — creating a consistent character  _(75w)_
  - ## 1. Choose the path: adapter, LoRA, or both  _(279w)_
  - ## 2. The character LoRA pipeline  _(352w)_
  - ## 3. Deploying: the detailer LoRA swap and `[SEP]` routing  _(140w)_
  - ## 4. Style bleed — the block-weight fix (SDXL's unique lever)  _(127w)_
  - ## 5. Beyond the face  _(144w)_
  - ## 6. Failure modes & fixes  _(165w)_
  - ## Sources & confidence  _(69w)_

**checkpoints-and-loras.md** — 1465w, 9 headings
- # SDXL Checkpoints, LoRAs & Control Tooling  _(55w)_
  - ## Table of contents  _(56w)_
  - ## 1. Why finetunes, and the two dialect families  _(106w)_
  - ## 2. Photoreal / general finetunes  _(135w)_
  - ## 3. Anime / booru finetunes  _(144w)_
  - ## 4. Using LoRAs — loading any style / character / concept LoRA  _(495w)_
  - ## 5. The fast-variant LoRAs (stacking speed onto any finetune)  _(178w)_
  - ## 6. LoRA training → `references/lora-training.md`  _(60w)_
  - ## 7. ControlNet & IP-Adapter catalog  _(169w)_

**lora-training.md** — 3424w, 12 headings
- # SDXL LoRA Training (kohya_ss / OneTrainer / ai-toolkit)  _(173w)_
  - ## 1. Choosing the base  _(314w)_
  - ## 2. Tools  _(131w)_
  - ## 3. Hyperparameters  _(417w)_
  - ## 4. Dataset architecture — the identity ratio  _(237w)_
  - ## 5. Captioning  _(622w)_
  - ## 6. Dataset traps  _(167w)_
  - ## 7. Style LoRAs  _(226w)_
  - ## 8. Advanced: weight noising and depth anchoring  _(290w)_
  - ## 9. Stacking several LoRAs of the same character  _(133w)_
  - ## 10. Assessing fit  _(438w)_
  - ## 11. Adult / NSFW work on SDXL  _(208w)_

**prompting-guide.md** — 2033w, 18 headings
- # SDXL Prompting Guide  _(47w)_
  - ## Table of contents  _(50w)_
  - ## 1. Prompt anatomy  _(142w)_
  - ## 2. Weighting, ordering, token economy  _(165w)_
  - ## 3. The dual-encoder split (`text_g` / `text_l`)  _(216w)_
  - ## 4. Photoreal vocabulary (the copy-paste lists)  _(23w)_
  - ## 5. Lighting, framing, camera angles  _(97w)_
  - ## 6. Negative prompts (variant-aware)  _(131w)_
  - ## 7. Checkpoint dialects: Pony & Illustrious  _(151w)_
  - ## 8. Worked SDXL-calibrated examples  _(298w)_
  - ## 9. What was dropped from the SD1.5-era source  _(148w)_

**setup-and-workflows.md** — 1525w, 10 headings
- # SDXL Setup & Workflows  _(27w)_
  - ## Table of contents  _(51w)_
  - ## 1. File layout & the VAE gotcha  _(149w)_
  - ## 2. ComfyUI — base-only graph  _(97w)_
  - ## 3. ComfyUI — base + refiner ensemble  _(147w)_
  - ## 4. ComfyUI — Turbo / Lightning / LCM / Hyper  _(239w)_
  - ## 5. diffusers — t2i, img2img, inpaint, the ensemble  _(137w)_
  - ## 6. Hires-fix & tiled upscale  _(260w)_
  - ## 7. ControlNet & IP-Adapter  _(234w)_
  - ## 8. Quantisation & VRAM  _(117w)_

---

## wan-2-2

- frontmatter keys: ['description', 'name']
- description: 221 words, 1414 chars
- SKILL.md: 4228 words, 23 headings
- tables in SKILL.md: 62
- provenance markers: flagged=5, contested=2, community=11, pending=0

### SKILL.md heading tree

- # Wan 2.2  _(198w)_
  - ## Task-mode selector  _(330w)_
  - ## The one rule that changes everything  _(268w)_
  - ## Setup & ecosystem  _(29w)_
    - ### File layout  _(256w)_
    - ### Quantisation & VRAM  _(69w)_
    - ### diffusers  _(23w)_
  - ## Per-mode settings  _(39w)_
    - ### 14B — I2V, T2V, FLF2V  _(116w)_
    - ### 5B TI2V (dense)  _(30w)_
    - ### S2V-14B (dense, audio-driven)  _(36w)_
    - ### The speed LoRAs, and their tax  _(184w)_
  - ## Prompting Wan 2.2  _(218w)_
  - ## Motion, camera and structural control  _(126w)_
    - ### SCAIL-2 — the Wan-family model that took over character replacement  _(360w)_
  - ## The two-LoRA rule  _(207w)_
  - ## Production pipelines & mixing models  _(141w)_
  - ## Failure modes & QC  _(333w)_
  - ## Pre-flight checklist  _(147w)_
  - ## Where Wan 2.2 sits in the suite  _(252w)_
  - ## Licence and known limitations  _(268w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(321w)_
  - ## Reference files  _(157w)_

### references


**characters.md** — 945w, 9 headings
- # Wan 2.2 — consistent characters in motion  _(74w)_
  - ## Start with the still — the handoff that does most of the work  _(218w)_
  - ## Holding identity within a shot  _(11w)_
  - ## Multi-character scenes  _(134w)_
  - ## Failure modes  _(204w)_

**lora-training.md** — 1483w, 9 headings
- # Wan 2.2 — LoRA training  _(51w)_
  - ## 1. The two-expert question  _(314w)_
  - ## 2. Trainers  _(88w)_
  - ## 3. Hyperparameters  _(191w)_
  - ## 4. Datasets  _(222w)_
  - ## 4a. Adult / NSFW work  _(158w)_
  - ## 5. Evaluation  _(165w)_
  - ## 6. Speed LoRAs during training and evaluation  _(65w)_

**motion-and-camera.md** — 871w, 8 headings
- # Wan 2.2 — motion, camera and structural control  _(52w)_
  - ## Which tool for which job  _(152w)_
  - ## Fun Camera Control  _(123w)_
  - ## Fun Control  _(85w)_
  - ## Fun InP  _(67w)_
  - ## VACE  _(92w)_
  - ## Animate  _(114w)_
  - ## What is not controllable  _(152w)_

**prompting-guide.md** — 1243w, 8 headings
- # Wan 2.2 — prompting guide  _(28w)_
  - ## 1. The shift from image prompting  _(288w)_
  - ## 2. Prompt anatomy  _(139w)_
  - ## 3. Motion vocabulary  _(147w)_
  - ## 4. Camera vocabulary  _(162w)_
  - ## 5. Negatives, and when they apply  _(208w)_
  - ## 6. Prompt extension  _(86w)_
  - ## 7. Worked examples  _(145w)_

**setup-and-workflows.md** — 1381w, 11 headings
- # Wan 2.2 — setup & workflows  _(56w)_
  - ## 1. The two-expert graph, node by node  _(462w)_
  - ## 2. The 5B graph  _(107w)_
  - ## 3. The S2V graph  _(60w)_
  - ## 4. Quantisation, VRAM and offload  _(248w)_
  - ## 5. The production ladder  _(173w)_
  - ## 6. Longer pieces: stitching and drift  _(134w)_
  - ## 7. diffusers  _(6w)_
- # Wan-AI/Wan2.2-T2V-A14B-Diffusers  _(0w)_
- # Wan-AI/Wan2.2-I2V-A14B-Diffusers  _(0w)_
- # TI2V-5B equivalent also integrated  _(80w)_

---

## z-image

- frontmatter keys: ['description', 'name']
- description: 211 words, 1638 chars
- SKILL.md: 3089 words, 16 headings
- tables in SKILL.md: 39
- provenance markers: flagged=0, contested=0, community=0, pending=0

### SKILL.md heading tree

- # Z-Image Family  _(55w)_
  - ## Variant selector  _(262w)_
  - ## Setup & ecosystem  _(436w)_
  - ## The one rule that changes everything  _(229w)_
  - ## Variant-specific settings  _(0w)_
    - ### Z-Image (undistilled)  _(132w)_
    - ### Z-Image-Turbo (distilled)  _(136w)_
  - ## Building multi-stage workflows  _(211w)_
  - ## Key realism technique  _(75w)_
  - ## Gaze control for high- and low-angle shots  _(132w)_
  - ## Failure modes & QC  _(265w)_
  - ## Pre-flight checklist  _(107w)_
  - ## Where Z-Image sits in the suite  _(231w)_
  - ## Licence and known limitations  _(114w)_
  - ## How to read the claims in this skill — two bars, by claim type  _(354w)_
  - ## Reference files  _(270w)_

### references


**characters.md** — 1588w, 8 headings
- # Z-Image Characters — creating a consistent character  _(118w)_
  - ## 1. The two paths (and how they chain)  _(218w)_
  - ## 2. Designing the character: the anchor image  _(123w)_
  - ## 3. Building the dataset  _(323w)_
  - ## 4. Train, evaluate, deploy  _(156w)_
  - ## 5. Beyond the face: outfits, props, multiple characters  _(301w)_
  - ## 6. Failure modes & fixes  _(222w)_
  - ## Sources & confidence  _(73w)_

**lora-training.md** — 2298w, 12 headings
- # Z-Image LoRA Training  _(60w)_
  - ## Which variant to train on — train on Base, generate on Turbo  _(111w)_
  - ## Dataset generation workflow  _(337w)_
  - ## Training with Ostris AI-Toolkit  _(0w)_
  - ## The fast path — RunPod + the Ostris template  _(189w)_
  - ## Experimental methods and how Z-Image responds  _(115w)_
  - ## Adult / NSFW work  _(170w)_
  - ## Assessing fit — is the LoRA actually working?  _(298w)_
  - ## Debugging  _(183w)_

**prompting-guide.md** — 3382w, 23 headings
- # Z-Image Prompting Guide  _(0w)_
  - ## 1. Prompt anatomy  _(195w)_
  - ## 2. Realism: killing the plastic default  _(204w)_
  - ## 3. Camera vocabulary  _(0w)_
  - ## 4. Lighting reference  _(127w)_
  - ## 5. High- and low-angle gaze control  _(0w)_
  - ## 6. Bilingual prompting and text rendering  _(105w)_
  - ## 7. Common mistakes  _(220w)_
  - ## 8. Drop-in templates  _(0w)_

**workflows.md** — 3462w, 26 headings
- # Z-Image Multi-Stage ComfyUI Workflows  _(103w)_
  - ## 1. The minimal build (start here)  _(77w)_
  - ## 2. The layered pipeline (the full build)  _(213w)_
  - ## 3. Per-stage settings (community layered pipeline)  _(227w)_
  - ## 4. Resolution strategy — generate small, upscale in layers  _(155w)_
  - ## 5. Universal node settings  _(176w)_
  - ## 6. Using LoRAs (any LoRA — style, concept, character, not just ones you train)  _(88w)_
  - ## 7. Optional improvement layers  _(259w)_
  - ## 8. Build order summary  _(80w)_
  - ## 9. Fun Union ControlNet (pose, depth, canny, and more)  _(64w)_
  - ## 10. Face identity — available methods  _(169w)_
  - ## 11. Z-Image in mixed-model pipelines  _(221w)_
