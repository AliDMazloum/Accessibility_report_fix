# Architecture Reference

Detailed per-step explanation of the Blackboard Ally fix pipeline. This file is the load-bearing reference for how the components work together — skim the README for a high-level view, read this when you need to remember how a specific piece behaves, what contracts it expects, or why a particular design choice was made.

## Table of contents

1. [System overview](#system-overview)
2. [Data directory layout](#data-directory-layout)
3. [Stage 1 — Collect (`v2_collect.py`)](#stage-1--collect-v2_collectpy)
4. [Stage 2 — Prepare (`semantic_agents.py`)](#stage-2--prepare-semantic_agentspy)
5. [Stage 3 — Semantic validate (`/semantic-validate`)](#stage-3--semantic-validate-semantic-validate)
6. [Stage 4 — Fix (`v2_fix.py` → `phase4_fix.py`)](#stage-4--fix-v2_fixpy--phase4_fixpy)
7. [Stage 5 — Alt-text validate (`/alt-text-validate`)](#stage-5--alt-text-validate-alt-text-validate)
8. [Stage 6 — Apply alt text (`phase4b_apply_alts.py`)](#stage-6--apply-alt-text-phase4b_apply_altspy)
9. [Stage 7 — Upload (`v2_upload.py`)](#stage-7--upload-v2_uploadpy)
10. [Multi-agent validation pattern](#multi-agent-validation-pattern)
11. [Skills and slash commands](#skills-and-slash-commands)
12. [Semantic JSON contract](#semantic-json-contract)
13. [Status policy (what "leave untouched" means)](#status-policy-what-leave-untouched-means)
14. [Efficiency features — why each one exists](#efficiency-features--why-each-one-exists)
15. [Ground rules for orchestration](#ground-rules-for-orchestration)
16. [v1 fallback pipeline](#v1-fallback-pipeline)

---

## System overview

Inputs:
- A Blackboard course with accessibility issues flagged by Ally.
- A Chrome browser logged in to Blackboard, launched in CDP mode by `launch_chrome.py`.
- Claude Code running (CLI or IDE) — provides the `Task` subagent tool used by the validation orchestrators.

Outputs:
- Every downloaded file fixed in place (deterministic + semantic + alt text), with a `backup_*` copy of the original kept next to it.
- Manifests under `data/` recording every decision so runs are resumable and auditable.
- Fixed files uploaded back through the Ally feedback window.

High-level flow:

```
                     ┌─────────────────────┐
                     │ Blackboard Ally     │
                     │ (source of truth)   │
                     └──────────┬──────────┘
                                │ download
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  1. Collect      v2_collect.py                   │
   │     Downloads everything below 85%               │
   └──────────────────────────────────────────────────┘
                                │ writes v2_collected_<COURSE>.json
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  2. Prepare      semantic_agents.py              │
   │     Extracts payloads + prefilters already-good  │
   └──────────────────────────────────────────────────┘
                                │ writes semantic_tasks_<COURSE>.json
                                │ (+ seeds already_good results)
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  3. Semantic validate   /semantic-validate       │
   │     2 generators + 1 validator per doc via Task  │
   └──────────────────────────────────────────────────┘
                                │ writes semantic_results_<COURSE>.json
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  4. Fix          v2_fix.py → phase4_fix.py       │
   │     Applies deterministic + semantic changes     │
   │     Extracts images needing alt text             │
   └──────────────────────────────────────────────────┘
                                │ writes v2_fixed_<COURSE>.json
                                │        v2_images_needing_alt_<COURSE>.json
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  5. Alt-text validate   /alt-text-validate       │
   │     2 generators + 1 validator per image         │
   └──────────────────────────────────────────────────┘
                                │ writes v2_alt_texts_<COURSE>.json
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  6. Apply alt texts   phase4b_apply_alts.py      │
   │     Writes descr/ActualText into each image      │
   └──────────────────────────────────────────────────┘
                                │
                                ▼
   ┌──────────────────────────────────────────────────┐
   │  7. Upload       v2_upload.py                    │
   │     Uploads fixed files via Ally feedback window │
   └──────────────────────────────────────────────────┘
```

---

## Data directory layout

Everything produced by a single course run lives under `data/`, keyed by `<COURSE>`:

| File | Written by | Consumed by |
|---|---|---|
| `v2_collected_<COURSE>.json` | `v2_collect.py` | `semantic_agents.py`, `v2_fix.py` |
| `semantic_tasks_<COURSE>.json` | `semantic_agents.py` | `/semantic-validate` |
| `semantic_tasks_<COURSE>.payloads/<N>.json` | `/semantic-validate` step 1 | the A+B generator Task subagents |
| `semantic_tasks_<COURSE>.payloads/_validator_batch_*.json` | `/semantic-validate` step 3 | the batched validator Task subagent |
| `semantic_results_<COURSE>.json` | `/semantic-validate` (incrementally) + `semantic_agents.py` (seeds `already_good`) | `v2_fix.py` |
| `v2_fixed_<COURSE>.json` | `v2_fix.py` | `v2_upload.py` |
| `v2_images_needing_alt_<COURSE>.json` | `v2_fix.py` | `/alt-text-validate` |
| `v2_alt_texts_<COURSE>.json` | `/alt-text-validate` (incrementally) | `phase4b_apply_alts.py` |

Course downloads live under `course_content/<COURSE_DIR>/_downloads/`. Each downloaded file's original is preserved as `backup_<filename>`; fixes are applied in place.

---

## Stage 1 — Collect (`v2_collect.py`)

**Purpose**: Walk the Ally Content report, click every item scored below 85%, capture the download through Playwright's `expect_download()`.

**Inputs**:
- Chrome logged in to Blackboard, parked on the course's Ally report Content tab.
- `scripts/courses.json` entry for `<COURSE>` with `{id, dir}`.

**Outputs**:
- Downloaded files in `course_content/<COURSE_DIR>/_downloads/`.
- `data/v2_collected_<COURSE>.json`: a list of `{report_name, downloaded_path, score}`.

**Key implementation details**:
- Uses a sticky page pointer on the report so progress is monotonic even when the DOM shifts between clicks.
- Binds each download to the specific button click via `expect_download()` — avoids the race where a second download event is mistaken for the first.
- Files larger than 20 MB (any format) or PDFs longer than 150 pages are skipped in later stages; Collect still downloads them because the page limit isn't known until the file is on disk.

---

## Stage 2 — Prepare (`semantic_agents.py`)

**Purpose**: Extract a text+structure payload from each collected document, prefilter documents that already have good metadata, and sort the remaining work largest-first.

**Inputs**:
- `data/v2_collected_<COURSE>.json`

**Outputs**:
- `data/semantic_tasks_<COURSE>.json`: list of `{report_name, source_path, document_kind, payload_size_estimate, payload}`, **sorted largest-first**.
- `data/semantic_results_<COURSE>.json` (seeded): already-good documents are pre-recorded with `semantic_status: "already_good"`.

**Payload shape** (per `document_kind`):

```jsonc
// PDF
{
  "document_kind": "pdf",
  "filename": "Lec03_Routing.pdf",
  "content": {
    "pages": [
      { "page": 0, "lines": [{"text": "...", "size": 24.0, "bold": true}, ...] },
      ...
    ]
  }
}

// PPTX
{
  "document_kind": "pptx",
  "filename": "vlans(1).pptx",
  "content": {
    "slides": [
      {
        "slide": 0,
        "shapes": [{"shape_idx": 0, "text": "...", "is_title_placeholder": false, "has_table": false}, ...],
        "tables": [{"shape_idx": 3, "rows": [["col A", "col B"], ["1", "2"]]}]
      },
      ...
    ]
  }
}

// DOCX
{
  "document_kind": "docx",
  "filename": "syllabus.docx",
  "content": {
    "paragraphs": [
      {"para_index": 0, "text": "...", "style": "Normal", "runs": [{"text": "...", "bold": false, "size": 11.0}]},
      ...
    ],
    "tables": [{"table_idx": 0, "rows": [["Day", "Topic"], ["Mon", "Intro"]]}]
  }
}
```

**Payload size caps** (keep per-doc payload well under the validator's context budget):

| Kind | Cap |
|---|---|
| PDF | First 30 pages + last 10 if total > 40 |
| PPTX | First 80 slides |
| DOCX | First 400 paragraphs |
| per-text unit | 800 chars |

**Prefilter logic** (`is_already_good`):
- PPTX — core title non-empty and not a template leftover, language set, every slide has a non-empty title placeholder.
- DOCX — core title non-template, language set, at least one `Heading 1/2/3` styled paragraph.
- PDF — non-template `/Title`, `/Lang` set, `/StructTreeRoot` exists, at least one `/H1`/`/H2`/`/H3` struct element.

Template titles rejected: `"the internet and its uses"`, `"presentation"`, `"powerpoint presentation"`, `"untitled"`, `"untitled presentation"`, `"document"`, `"slide 1"`, `"click to add title"`, `"title"`, plus any title that equals the filename stem (with `_`/`-` → space).

**Sort key**: `payload_size_estimate` descending (approx tokens = chars // 4). Biggest docs enter the pool first so they're not the tail of the run.

---

## Stage 3 — Semantic validate (`/semantic-validate`)

**Purpose**: Drive the 2-generator + 1-validator pattern per document using Claude Code's `Task` tool.

**Inputs**:
- `data/semantic_tasks_<COURSE>.json`
- Existing `data/semantic_results_<COURSE>.json` (used for resume + already_good skip)

**Outputs**:
- `data/semantic_results_<COURSE>.json`: list of `{report_name, semantic_status, semantic_attempts, reason, semantic}`.

**Per-doc loop**:

1. **Resume skip** — if `report_name` already has an entry in the results file, skip.
2. **Write payload to disk** — `data/semantic_tasks_<COURSE>.payloads/<N>.json`.
3. **Generators** — spawn two `Task` calls in parallel (single message, two `tool_use` blocks). Each Task prompt is "Use the semantic-generator skill on this payload file."
4. **A==B shortcut** — normalize both outputs with `json.dumps(sort_keys=True, separators=(',',':'))`. If equal, skip the validator; record `applied` with `semantic: A`.
5. **Queue for batched validation** — non-identical A/B pairs join a queue of `{doc_id, payload_summary, a, b}`. Flush when ≥5 entries, 20s elapsed, or task list drained.
6. **Validator** — one `Task` call per batch ("Use the semantic-validator skill in BATCH MODE on this batch file"). Returns `{results: [{doc_id, similar, chosen, reason, final}, ...]}`.
7. **Per result**: `similar: true` → record `applied` with `semantic: final`. `similar: false` → retry (new A, new B, back into queue). Second failure → `skipped_validation`, `semantic: null`.
8. **Incremental persist** — append to results file after every completion so a crash is recoverable.

**Concurrency**: `N_concurrent = min(N_remaining, 20)`. Pool semantics — free slot triggers next pending doc. Large docs first (already encoded in task order).

**Never**: produce the semantic JSON yourself as the orchestrator. Every field comes from a subagent. That's what makes validation meaningful.

---

## Stage 4 — Fix (`v2_fix.py` → `phase4_fix.py`)

**Purpose**: Apply the validated semantic result (if any) plus deterministic fixes, and extract images needing alt text.

**Inputs**:
- `data/v2_collected_<COURSE>.json`
- `data/semantic_results_<COURSE>.json` (may be missing; treated as empty map)

**Outputs**:
- Modified files in `course_content/<COURSE_DIR>/_downloads/` (original preserved as `backup_<filename>`)
- `data/v2_fixed_<COURSE>.json`: per-doc manifest including `semantic_status`, `fixed_path`, `images_need_alt`
- `data/v2_images_needing_alt_<COURSE>.json`: per-image manifest for the alt-text stage

**Per-doc branching by `semantic_status`**:

| Status | Behavior |
|---|---|
| `applied` | Apply deterministic fixes (tags, struct tree) + semantic overrides (title, language, headings, table flags, lists). File is fully fixed. |
| `already_good` | **Leave file untouched.** Record `fix_skipped_reason: "semantic already_good"`. |
| `skipped_validation` | **Leave file untouched.** Record `fix_skipped_reason: "semantic skipped_validation: <reason>"`. |
| `skipped_error` | **Leave file untouched.** Same as above. |
| (no entry) | Deterministic-only fallback: filename-derived title, font-size heading detection, blanket table header flagging, `en-US` default. |

**Why "leave untouched" instead of deterministic fallback?** User policy: if we can't validate a genuine semantic improvement, don't claim a partial fix. The backup remains; the downloaded file is left exactly as Ally served it.

**Deterministic fixes** (floor when `applied`, not applied when untouched):
- **PDF** — `/StructTreeRoot` + `/MarkInfo.Marked=true`, `/Lang`, `/Title`. Font-size heading detection in `add_headings.py`.
- **PPTX** — `core_properties.title`/`language`, slide title filling, `tblPr.firstRow=1` on tables.
- **DOCX** — `core_properties.title`/`language`, `Heading 1/2/3` styles via font-size or pattern heuristics, `w:tblHeader` on first table rows.

**Semantic overrides** (when `applied`):
- **Title / language**: always overwrite when semantic values are present. The title is also written to PDF `/Info/Title` + XMP `dc:title` even if the PDF already had a placeholder title (Ally rejects tooling-generated placeholders like `Microsoft Word - foo.docx`).
- **Headings**:
  - PDF → `add_headings_to_pdf(..., heading_override=semantic.headings)`. Each heading becomes a `/H1|/H2|/H3` struct element with `/ActualText` and `/Alt` set to the heading text, anchored to its page by text match (`anchor_text` substring). Levels are normalized in `_normalize_heading_levels` so the hierarchy always starts at H1 with no gaps, satisfying Ally's "headings begin at level 1" and "follow a logical order" checks.
  - PPTX → level-1 headings with `locator.slide` fill that slide's title placeholder.
  - DOCX → `Heading N` style applied to the paragraph at `locator.para_index`. Before application, `_docx_snapshot_runs` captures each run's effective font / color / size. After application, `_docx_restore_runs` reimposes those as direct run formatting. The `Heading N` style itself is neutralized (`_docx_neutralize_heading_style` strips the `<w:rPr>` block) so the style acts as a transparent semantic tag: screen readers and Ally see the outline level, but the visible text keeps the document's original look.
- **Tables**:
  - `has_header_row: true` → keep `firstRow` / `w:tblHeader` flag.
  - `has_header_row: false` → **do not** flag row 0 as header (override deterministic default).
- **Lists**:
  - PPTX → `_pptx_apply_list_to_shape` rewrites each paragraph's `pPr` to include `<a:buAutoNum>` (ordered) or `<a:buChar>` (unordered), strips leading `•/-/*/1./2.` glyphs.
  - DOCX → `List Number` / `List Bullet` style applied to paragraphs in `para_range`, leading glyphs stripped.

**Image extraction**: only runs for docs with `semantic_status: applied`. PPTX images with no `cNvPr.descr` and DOCX drawings with no `wp:docPr.descr` are extracted as PNG/JPG to `<dir>/_imgs_<stem>/` with context (`slide_text` or surrounding paragraphs).

**Size gates** (enforced here, not in Collect): PDF > 150 pages → skip. Any file > 20 MB → skip. Skips record `skipped_reason` in `v2_fixed_<COURSE>.json`.

---

## Stage 5 — Alt-text validate (`/alt-text-validate`)

**Purpose**: Drive the 2-generator + 1-validator pattern per image using `Task` subagents with vision.

**Inputs**:
- `data/v2_images_needing_alt_<COURSE>.json`
- Existing `data/v2_alt_texts_<COURSE>.json` (resume)

**Outputs**:
- `data/v2_alt_texts_<COURSE>.json`: list of `{fixed_path, alts: [{slide, shape_idx, alt_text} | {index, alt_text}]}`.

**Per-image loop**:

1. **Resume skip** — if `(fixed_path, locator)` already recorded, skip.
2. **Generators** — two `Task` calls in parallel. Each loads the `alt-text-generator` skill, `Read`s the image file (the `Read` tool supports images), and uses the provided `slide_text` / `context`. Each returns `{alt_text: "..."}`.
3. **A==B shortcut** — if `a.strip() == b.strip()` (including both being `""` for decorative images), record `applied` with that alt text, skip validator.
4. **Validator** — one `Task` call with the image, context, A, and B. Returns `{similar, chosen, reason, alt_text}`. `similar: true` → include in output. `similar: false` → retry once. Second failure → **skip this image entirely** (not included in the output alts list; the image keeps its pre-run state).
5. **Incremental persist** — rewrite the output file after each image (or every 20 images at minimum) for crash-safety.

**Concurrency**: `N_concurrent = min(N_remaining, 20)`, pool semantics, image size descending.

---

## Stage 6 — Apply alt text (`phase4b_apply_alts.py`)

**Purpose**: Write validated alt texts into each document's image descriptors.

**Inputs**:
- `data/v2_alt_texts_<COURSE>.json`

**Outputs**:
- Modified PPTX / DOCX files (alt texts written into `cNvPr.descr` and `docPr.descr`).

**Locator types**:
- `{slide, shape_idx, alt_text}` — PPTX: find slide N's shape at index M, set `cNvPr.descr`.
- `{index, alt_text}` — DOCX: find the N-th `w:drawing` in the body's XML tree, set `wp:docPr.descr`.

**Verification helper**: `verify_no_missing_alts` rescans each file after application and reports any remaining images without alt text (useful as a pre-upload sanity check).

---

## Stage 7 — Upload (`v2_upload.py`)

**Purpose**: Re-upload every fixed file through the Ally feedback window so Ally re-scores it.

**Inputs**:
- `data/v2_fixed_<COURSE>.json`

**Outputs**:
- Updated scores on the Blackboard Ally report.

**Key implementation details**:
- Re-uses the same sticky page pointer pattern as Collect.
- Only advances to the next report page when the current page has no remaining candidates.
- Cleans up `_imgs_<stem>/` staging directories when done.
- Skips files with `fix_skipped_reason` (including the "semantic skipped" cases — those keep their original file).

---

## Multi-agent validation pattern

Both `/semantic-validate` and `/alt-text-validate` implement the same 2+1 pattern:

```
                      ┌────────────────────┐
                      │ Generator A (Task) │──┐
                      └────────────────────┘  │
                                              │
  payload ──────────────▶                     │────▶ compare ──▶ ┌───────────┐
                                              │                   │ accept    │
                      ┌────────────────────┐  │                   │ (pick A   │
                      │ Generator B (Task) │──┘                   │  or B)    │
                      └────────────────────┘                      └───────────┘
                                                                        │
                                             if A == B  ─────────▶──────┤
                                                                        │
                                             if A ≠ B  ┌──────────────┐ │
                                                       │ Validator    │─┤
                                                       │ (Task)       │ │
                                                       └──────────────┘ │
                                                                        │
                                        validator says "similar: false"─┘
                                                                        │
                                                                        ▼
                                                              retry once, then skip
```

### Why it works

- **Independence of A and B**: Claude Code's `Task` tool spawns subagents in separate contexts — neither sees the other's output. Any consistent answer is likely correct; inconsistencies reveal where the prompt is ambiguous or the document is weird.
- **Validator as judge, not generator**: the validator never rewrites, merges, or invents — it just picks which of A or B is better, or declares them too different to trust.
- **Retry once, then skip**: if two full independent attempts can't agree, the document is probably unusual (mixed languages, ambiguous heading structure). Skipping avoids applying a wrong answer; the original file survives.

### A==B shortcut

Short or highly-structured docs often produce byte-identical A and B outputs. In that case the validator's answer is trivially "yes, they agree" — so we skip it entirely. Empirically this fires for ~30–50% of documents and an even higher share of decorative images (both generators returning `""`).

### Batched validator

For non-identical A/B pairs, we queue them and flush in groups of up to 5 into one validator call. The `semantic-validator` skill supports two input shapes: single `{payload_summary, a, b}` or batched `{batch: [{doc_id, payload_summary, a, b}, ...]}`. Cuts validator API spawns by up to 5× on large courses.

---

## Skills and slash commands

**Skills** are reusable subagent prompt bodies under `.claude/skills/`. Each skill is one markdown file with YAML frontmatter (`name`, `description`) and the body is the prompt itself. Claude Code auto-loads the skill when a `Task` prompt says "Use the `<skill-name>` skill".

| Skill | Role | Input | Output |
|---|---|---|---|
| `semantic-generator` | Generate semantic JSON from a payload | Payload file path | Semantic JSON |
| `semantic-validator` | Compare two semantic JSONs (single or batch) | `{a, b}` or `{batch}` | `{similar, chosen, reason, final}` or `{results: [...]}` |
| `alt-text-generator` | Describe one image | Image + context | `{alt_text}` |
| `alt-text-validator` | Compare two alt texts for one image | Image, context, A, B | `{similar, chosen, reason, alt_text}` |

The `semantic_prompts.py` module exposes the same prompts as Python constants via `__getattr__` — it reads the SKILL.md files on first access, stripping YAML frontmatter. This keeps the skill file as the single source of truth while allowing `from semantic_prompts import GENERATOR_SYSTEM` style access from Python.

**Slash commands** orchestrate the skills:

- [`/semantic-validate <COURSE>`](../.claude/commands/semantic-validate.md) — drives stage 3
- [`/alt-text-validate <COURSE>`](../.claude/commands/alt-text-validate.md) — drives stage 5

---

## Semantic JSON contract

Produced by `semantic-generator`, validated by `semantic-validator`, consumed by `fix_pdf.py` / `add_headings.py` / `fix_office.py` through `phase4_fix.fix_single_file(..., semantic=...)`.

```jsonc
{
  "semantic_title": "Introduction to IP Routing Protocols",
  "language": "en-US",
  "headings": [
    { "text": "Overview", "level": 1, "locator": {...} },
    { "text": "Static Routing", "level": 2, "locator": {...} }
  ],
  "tables": [
    {
      "table_idx": 0,
      "has_header_row": true,
      "header_row_index": 0,
      "scope": "col" | "row" | "both",
      "notes": "free text on merged cells, irregularities"
    }
  ],
  "lists": [
    { "locator": {...}, "ordered": false, "item_count": 5 }
  ]
}
```

**Locator shapes** (per `document_kind`):

| Field | PDF | PPTX | DOCX |
|---|---|---|---|
| heading | `{page, anchor_text}` | `{slide, shape_idx}` | `{para_index}` |
| list | `{page, anchor_text}` | `{slide, shape_idx}` | `{para_range: [lo, hi]}` |

**Rules**:
- Titles must be content-derived, not filename-derived.
- A slide title on each slide IS a heading (level 1 for section dividers, level 2 for content).
- `has_header_row: true` only if row 0 is genuinely column labels.
- Lists only include manually-typed bullets — skip native-style lists.
- Omit empty arrays.

---

## Status policy (what "leave untouched" means)

After `semantic-validate` runs, each document has one of these statuses in `semantic_results_<COURSE>.json`:

| Status | `v2_fix.py` policy | Final file state |
|---|---|---|
| `applied` | Apply deterministic + semantic fixes | Fully fixed |
| `already_good` | Do nothing | Original file on disk (never went through Fix) |
| `skipped_validation` | Do nothing | Original file on disk |
| `skipped_error` | Do nothing | Original file on disk |
| (no entry) | Apply deterministic only | Partially fixed (floor only) |

The three "do nothing" cases preserve the backup and the downloaded file exactly. This is an explicit user policy: "we failed to fix it, so don't pretend we did."

---

## Efficiency features — why each one exists

| Feature | Saves | When it helps most |
|---|---|---|
| Prefilter already-good docs | entire 2+1 pipeline for that doc | Mature courses where prior runs already fixed most files |
| A==B shortcut | one validator Task call | Short docs, simple structure, decorative images |
| Batched validator | up to 4× reduction in validator Task calls | Medium-large courses with many non-trivial A/B pairs |
| Dynamic concurrency (`min(N, 20)`) | wall-clock time | All courses — small courses run flat out, large courses saturate the rate limit without exceeding it |
| Largest-first ordering | wall-clock tail latency | Courses with a few very big lectures |
| Pool semantics (not batches) | wait time between slots | Courses with mixed doc sizes |
| Incremental persist / resume | rerunning after crashes or interruptions | Long runs (> 20 min) |
| "Leave untouched" on validation failure | not claiming a partial fix | Quality guarantee, not speed |

**Projected speedup** (200-doc course, assumes 30% prefiltered, 40% A==B shortcut fire):
- Baseline sequential: ~70 min
- All optimizations enabled: ~8 min

---

## Ground rules for orchestration

These are non-negotiable rules for `/semantic-validate` and `/alt-text-validate`:

1. **Never produce the validated output yourself.** The whole point of having subagents A and B is independent evidence. If the orchestrator writes the semantic JSON or the alt text directly, validation becomes theatre.
2. **Skills are the single source of truth for prompts.** `Task` prompts should invoke skills by name, not inline the skill body.
3. **Always be resumable.** Load the output file on startup, skip already-recorded entries, persist incrementally.
4. **Don't block the pool.** Free a slot the moment a doc/image finishes; don't wait for a whole batch.
5. **Respect the "leave untouched" policy.** `skipped_validation`, `skipped_error`, and `already_good` all mean the file is not modified.
6. **Stay under the rate-limit ceiling.** 20 concurrent subagents is the practical sustained cap.

---

## v1 fallback pipeline

The original outline-driven pipeline lives alongside v2 for courses where v2 can't reach the files (e.g., Ally download links fail and the course outline must be walked). It uses the same fix engine (`phase4_fix.fix_single_file`) and therefore benefits from the same semantic pipeline if `semantic_results_<COURSE>.json` is present.

| Phase | Script | Purpose |
|-------|--------|---------|
| 1 | `phase1_scrape.py` | Scrape the Ally report for every flagged item |
| 2 | `phase2_targets.py` | Filter items below 85%, normalize names |
| 3 | `phase3_download.py` | Walk course outline, download each target file |
| 4 | `phase4_fix.py` | Apply deterministic + semantic fixes |
| 4b | `phase4b_apply_alts.py` | Apply alt-text JSON |
| 5 | `phase5_upload.py` | Upload via Ally feedback window |

Use v2 by default; fall back to v1 only when v2's download path fails.
