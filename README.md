# Blackboard Accessibility Pipeline

> This project is primarily coded with [Claude](https://claude.com/claude-code), Anthropic's AI coding assistant.

Automated pipeline that fixes Blackboard Ally accessibility issues in PDF, PPTX, and DOCX course materials. Applies meaningful **semantic** fixes (content-derived titles, real heading hierarchy, validated table headers, semantic lists, detected language) plus AI-generated image alt text, then re-uploads the fixed files through the Ally feedback window.

The semantic and alt-text passes use a **two-generator + one-validator** multi-agent pattern per document and per image — two independent subagents produce results in parallel, and a third validator decides whether they agree well enough to commit. This runs under the user's Claude Code subscription via the `Task` tool (no API key required).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed per-step explanation of the entire workflow, contracts, and file layouts.

## Why

Blackboard Ally flags many course documents as low accessibility (under 85%). Fixing them by hand is repetitive and, when done with deterministic tools, passes Ally's checks without producing genuinely accessible documents (filename-derived titles, font-size-based headings, blindly marking every table's first row as header, etc.).

This project combines:

- **Deterministic structural floor** (PDF `/StructTreeRoot` + `/MarkInfo`, filename-title and `en-US` as *last-resort* fallbacks when no semantic entry exists)
- **Semantic fixes** (content-derived titles, real heading hierarchy, validated table headers, semantic lists, detected language) from a 2+1 multi-agent validation loop
- **Image alt text** from a parallel 2+1 validation loop per image
- Full upload automation back to Ally

## Pipeline (v2 workflow)

| Step | Command | What happens |
|------|---------|--------------|
| 1. Collect | `python scripts/v2_collect.py <COURSE>` | Downloads every flagged item from the Ally report |
| 2. Prepare | `python scripts/semantic_agents.py <COURSE>` | Extracts text/structure payloads, prefilters already-good docs, writes `semantic_tasks_<COURSE>.json` |
| 3. Semantic validate | `/semantic-validate <COURSE>` (slash command in Claude Code) | Runs 2 generators + 1 validator per doc via `Task`, writes `semantic_results_<COURSE>.json` |
| 4. Fix | `python scripts/v2_fix.py <COURSE>` | Applies deterministic + semantic fixes per doc, extracts images needing alt text |
| 5. Alt text validate | `/alt-text-validate <COURSE>` (slash command) | Runs 2 generators + 1 validator per image via `Task`, writes `v2_alt_texts_<COURSE>.json` |
| 6. Apply alt text | `python scripts/phase4b_apply_alts.py <COURSE> data/v2_alt_texts_<COURSE>.json` | Writes the validated alt texts into the PPTX/DOCX files |
| 7. Upload | `python scripts/v2_upload.py <COURSE>` | Re-uploads every fixed file through the Ally feedback window |

## v1 pipeline (fallback)

The original outline-driven pipeline remains as a fallback when v2 can't serve a course (e.g., Ally download fails and the course outline must be walked instead).

| Phase | Script | Purpose |
|-------|--------|---------|
| 1 | `scripts/phase1_scrape.py` | Navigate the accessibility report, extract every item with its score |
| 2 | `scripts/phase2_targets.py` | Filter items below 85%, drop unfixable Ultra documents |
| 3 | `scripts/phase3_download.py` | Walk the course outline, expand modules, download each target file |
| 4 | `scripts/phase4_fix.py` | Apply deterministic + semantic fixes (same core engine v2 uses) |
| 4b | `scripts/phase4b_apply_alts.py` | Apply the alt-text JSON to PPTX/DOCX files |
| 5 | `scripts/phase5_upload.py` | Re-upload through the Ally feedback window |

## Multi-agent validation

Both the semantic and alt-text passes use the same pattern per unit of work (document or image):

```
Generator A ──┐
              ├──▶ Validator ──▶ accept (pick one) OR retry once
Generator B ──┘                                     │
                                                    └──▶ second reject → skip
```

Agent prompts live as Claude Code **skills** under [.claude/skills/](.claude/skills/):

- [`semantic-generator`](.claude/skills/semantic-generator/SKILL.md) — analyzes one document payload
- [`semantic-validator`](.claude/skills/semantic-validator/SKILL.md) — compares two generator outputs (single or batch mode)
- [`alt-text-generator`](.claude/skills/alt-text-generator/SKILL.md) — describes one image
- [`alt-text-validator`](.claude/skills/alt-text-validator/SKILL.md) — compares two alt texts

Slash commands in [.claude/commands/](.claude/commands/) orchestrate them:

- [`/semantic-validate`](.claude/commands/semantic-validate.md)
- [`/alt-text-validate`](.claude/commands/alt-text-validate.md)

## Efficiency features

- **Prefilter** — documents that already have non-template title + language + heading structure skip the semantic pipeline entirely (`semantic_status: "already_good"`)
- **A==B shortcut** — if both generators produce byte-identical JSON, the validator is skipped entirely for that doc/image
- **Batched validator** — up to 5 non-trivial A/B pairs are sent to a single validator call
- **Dynamic concurrency** — `N_concurrent = min(N_remaining, 20)` per course; pool semantics (not batched) so free slots dispatch the next pending doc immediately
- **Largest-first ordering** — heavy docs start early so tail slots fill with small work
- **Resume-friendly** — both orchestrators skip entries already written to the output file, so a crashed run resumes from the last persisted completion
- **Dual-path fallback** — semantic fix failure preserves the original file untouched (user policy: no partial fix)
- **Visual preservation for DOCX headings** — the Heading N style's run-property block is stripped before application, and run formatting is snapshotted and restored, so semantic tags get attached without changing the document's visible fonts or colors
- **Unconditional title write** — when a validated semantic title is available, it is written to `/Info/Title` and XMP metadata even if the PDF already has a placeholder title (Ally rejects tooling-generated placeholders like "Microsoft Word - foo.docx")
- **Heading level normalization** — PDF headings are always remapped to start at H1 with no gaps so Ally's "headings do not begin at level 1" and "do not follow a logical order" checks pass

## Tech

* Python 3.12+
* Playwright over Chrome DevTools Protocol (port 9222), for the Collect and Upload stages
* `python-pptx`, `python-docx`, `pikepdf`, `pymupdf` for document manipulation
* LibreOffice (headless) for legacy `.doc` and `.ppt` to OOXML conversion
* Claude Code's `Task` subagent tool for the 2+1 validation pattern (no Anthropic API key required — uses your subscription)

## Quick start

### Prerequisites

* Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
* LibreOffice installed at `C:/Program Files/LibreOffice/program/soffice.exe`
* Python 3.12+
* `pip install -r requirements.txt`
* `playwright install chromium`
* Claude Code (CLI or IDE extension) — the subscription covers all subagent calls

### Setup

1. Add your course to `scripts/courses.json`:
   ```json
   "MY_COURSE": { "id": "_1234567_1", "dir": "MY-COURSE-DIR" }
   ```
2. Launch Chrome with the project local profile and CDP enabled:
   ```
   python scripts/launch_chrome.py
   ```
3. Log in to Blackboard manually in the launched Chrome window.

### Run the v2 workflow

```bash
# 1. Collect — navigate Chrome to the accessibility report's Content tab first
python scripts/v2_collect.py MY_COURSE

# 2. Prepare semantic tasks (extracts payloads, prefilters already-good docs)
python scripts/semantic_agents.py MY_COURSE

# 3. In Claude Code, run the slash command:
#    /semantic-validate MY_COURSE
#    (writes data/semantic_results_MY_COURSE.json)

# 4. Apply semantic + deterministic fixes, extract images
python scripts/v2_fix.py MY_COURSE

# 5. In Claude Code, run:
#    /alt-text-validate MY_COURSE
#    (writes data/v2_alt_texts_MY_COURSE.json)

# 6. Apply alt texts to the files
python scripts/phase4b_apply_alts.py MY_COURSE data/v2_alt_texts_MY_COURSE.json

# 7. Upload — navigate Chrome to the accessibility report first
python scripts/v2_upload.py MY_COURSE
```

## Repository layout

```
scripts/
  bb_utils.py              Shared Playwright + Blackboard utilities
  courses.json             Course id and folder mapping
  launch_chrome.py         Launches Chrome with CDP and project profile
  v2_collect.py            Download every below-85% item from the report
  semantic_agents.py       Prefilter + payload extraction for the semantic pass
  semantic_schema.py       JSON shape normalization helpers
  semantic_prompts.py      Lazy-loaded prompt constants (skills are the source of truth)
  v2_fix.py                Apply deterministic + semantic fixes, extract images
  fix_pdf.py               PDF tagging, language, title, /ActualText on headings
  add_headings.py          PDF heading struct tree — supports semantic override
  fix_office.py            PPTX/DOCX fixes + image extraction + semantic application
  phase4b_apply_alts.py    Apply alt-text JSON to PPTX/DOCX
  v2_upload.py             Upload fixed files via Ally
  phase1_scrape.py → phase5_upload.py   v1 fallback pipeline
.claude/
  skills/                  Reusable subagent prompt bodies (4 skills)
  commands/                Slash commands that orchestrate the skills
data/                      (gitignored) per-course manifests, payloads, results
course_content/            (gitignored) downloaded files, organized by course
chrome-profile/            (gitignored) project local Chrome profile
_downloads/                (gitignored) Chrome download landing dir
docs/
  ARCHITECTURE.md          Detailed per-step workflow reference
```

## Notes

* `course_content/`, `data/`, and `chrome-profile/` are gitignored to keep student materials and personal data out of the repository.
* Files larger than 20 MB (any format) or PDFs longer than 150 pages are skipped automatically.
* The semantic validator uses a "relatively similar" rule — small wording differences are accepted; substantive disagreements trigger one retry, then a skip.
* If the semantic validator rejects a document twice, the Fix stage **leaves the original file untouched** (no partial/deterministic fallback).
* See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full workflow reference with contracts, locator shapes, and rationale for every design decision.

## License

MIT.
