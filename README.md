# Blackboard Accessibility Pipeline

> This project is primarily coded with [Claude](https://claude.com/claude-code), Anthropic's AI coding assistant.

Automated pipeline to fix Blackboard Ally accessibility issues in PDF, PPTX, and DOCX course materials. Adds document tags, language, headings, table headers, and AI generated image alt text, then re uploads the fixed files through the Ally feedback window.

## Why

Blackboard Ally flags many course documents as low accessibility (under 85%). Fixing them by hand is repetitive: open Ally, download original, edit metadata, add alt text, upload back, repeat for hundreds of files per course. This project automates the whole loop.

## How it works

Two workflows are available. The v2 report-driven workflow is the preferred path; the v1 five-phase pipeline remains as a fallback when v2 cannot serve a course.

### v2 workflow (recommended)

Drives the entire process from the accessibility report itself: download every flagged item directly through the Ally feedback window, fix locally, then upload. No course-outline navigation needed.

| Step | Script | Purpose |
|-------|--------|---------|
| 1 + 2 | `scripts/v2_collect.py` | Iterate the report Content tab and download every item below 85% via Playwright `expect_download`. Uses a sticky page pointer so progress through the report is monotonic. |
| 3 | `scripts/v2_fix.py` | Apply deterministic fixes (title, language, headings, table headers) to every downloaded file and extract images that need alt text. |
| (alt text) | parallel agents | One Claude Haiku subagent per document writes alt text into a JSON file. |
| (apply) | `scripts/phase4b_apply_alts.py` | Apply the alt text JSON to the fixed files. |
| 4 | `scripts/v2_upload.py` | Re-upload every fixed file through the report. Sticky page pointer only advances when the current page has no remaining candidates. Cleans up extracted image directories when done. |
| | `scripts/v2_run.py` | Orchestrator: runs collect, fix, and (if no alt text needed) upload in one command. |

### v1 five-phase pipeline (fallback)

The original outline-driven pipeline. Each phase has a standalone script and produces a JSON manifest the next phase reads.

| Phase | Script | Purpose |
|-------|--------|---------|
| 1 | `scripts/phase1_scrape.py` | Navigate the accessibility report, extract every item with its score across all pages. |
| 2 | `scripts/phase2_targets.py` | Filter items below 85%, drop unfixable Ultra documents, normalize duplicate names. |
| 3 | `scripts/phase3_download.py` | Walk the course outline, expand modules, download each target file. |
| 4 | `scripts/phase4_fix.py` | Convert old formats (LibreOffice), apply title, language, headings, and table header fixes. Extract images that need alt text. |
| 4b | `scripts/phase4b_apply_alts.py` | Apply AI generated alt text JSON to PPTX / DOCX files. |
| 5 | `scripts/phase5_upload.py` | Re upload fixed files through the Ally feedback window using Playwright `expect_download` for safe download interception. |

Image alt text generation is performed by parallel Claude Haiku agents, one per document.

## Tech

* Python 3.13
* Playwright over Chrome DevTools Protocol (port 9222), driving an existing Chrome session so the user stays logged in
* `python-pptx`, `python-docx`, `pikepdf` for document manipulation
* LibreOffice (headless) for legacy `.doc` and `.ppt` to OOXML conversion
* Anthropic Claude Haiku for image alt text generation (parallel subagents)

## Quick start

### Prerequisites

* Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
* LibreOffice installed at `C:/Program Files/LibreOffice/program/soffice.exe`
* Python 3.13
* `pip install -r requirements.txt`
* `playwright install chromium`

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

### Run the v2 workflow (recommended)

Navigate Chrome to the accessibility report's Content tab, then:

```
python scripts/v2_run.py MY_COURSE
# v2_run executes collect + fix. If documents have images that need alt text,
# it pauses with next-step instructions: launch Claude Code subagents on
# data/v2_images_needing_alt_MY_COURSE.json, then:
python scripts/phase4b_apply_alts.py MY_COURSE data/v2_alt_texts_MY_COURSE.json
python scripts/v2_upload.py MY_COURSE
# (If no alt text is needed, v2_run auto-runs v2_upload.)
```

### Run the v1 pipeline (fallback)

```
python scripts/phase1_scrape.py MY_COURSE
python scripts/phase2_targets.py MY_COURSE
python scripts/phase3_download.py MY_COURSE
python scripts/phase4_fix.py MY_COURSE
# Generate alt text via your preferred method, then:
python scripts/phase4b_apply_alts.py MY_COURSE data/alt_texts_MY_COURSE.json
# Navigate Chrome to the accessibility report's Content tab, then:
python scripts/phase5_upload.py MY_COURSE
```

## Repository layout

```
scripts/
  bb_utils.py              Shared Playwright + Blackboard utilities
  courses.json             Course id and folder mapping
  launch_chrome.py         Launches Chrome with CDP and project profile
  v2_collect.py            v2 step 1+2: download every below-85% item from the report (default)
  v2_fix.py                v2 step 3: apply deterministic fixes to downloaded files
  v2_upload.py             v2 step 4: upload fixed files; auto-cleans image staging dirs
  v2_run.py                v2 orchestrator (default entry point)
  phase1_scrape.py         v1 fallback: scrape report
  phase2_targets.py        v1 fallback: filter targets
  phase3_download.py       v1 fallback: download via course outline
  phase4_fix.py            v1 fallback: apply deterministic fixes
  phase4b_apply_alts.py    apply alt text JSON (used by both v1 and v2)
  phase5_upload.py         v1 fallback: upload fixed files via Ally
  fix_pdf.py               PDF tags, language, title
  add_headings.py          PDF heading detection by font size
  fix_office.py            PPTX / DOCX fixes and image extraction
data/                      (gitignored) per course manifests, JSON outputs
course_content/            (gitignored) downloaded files, organized by course
chrome-profile/            (gitignored) project local Chrome profile
_downloads/                (gitignored) Chrome download landing dir
```

## Notes

* `course_content/`, `data/`, and `chrome-profile/` are gitignored to keep student materials and personal data out of the repository.
* Phase 5 uses Playwright's `expect_download()` to bind each download to its triggering click. This avoids race conditions where a manual Save As dialog from one item leaks into the next download.
* Files larger than 20 MB (any format) or PDFs longer than 150 pages are skipped automatically.
* The v2 workflow is the default. The v1 five-phase pipeline is kept for cases where v2 cannot reach a course (for example, when downloads through Ally fail and the course outline must be walked instead).

## License

MIT.
