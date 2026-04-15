# Blackboard Accessibility Pipeline

> This project is primarily coded with [Claude](https://claude.com/claude-code), Anthropic's AI coding assistant.

Automated pipeline to fix Blackboard Ally accessibility issues in PDF, PPTX, and DOCX course materials. Adds document tags, language, headings, table headers, and AI generated image alt text, then re uploads the fixed files through the Ally feedback window.

## Why

Blackboard Ally flags many course documents as low accessibility (under 85%). Fixing them by hand is repetitive: open Ally, download original, edit metadata, add alt text, upload back, repeat for hundreds of files per course. This project automates the whole loop.

## How it works

The pipeline runs in five phases. Each phase has a standalone script and produces a JSON manifest the next phase reads. Phases can be re run independently.

| Phase | Script | Purpose |
|-------|--------|---------|
| 1 | `scripts/phase1_scrape.py` | Navigate the accessibility report, extract every item with its score across all pages. |
| 2 | `scripts/phase2_targets.py` | Filter items below 85%, drop unfixable Ultra documents, normalize duplicate names. |
| 3 | `scripts/phase3_download.py` | Walk the course outline, expand modules, download each target file. |
| 4 | `scripts/phase4_fix.py` | Convert old formats (LibreOffice), apply title, language, headings, and table header fixes. Extract images that need alt text. |
| 4b | `scripts/phase4b_apply_alts.py` | Apply AI generated alt text JSON to PPTX / DOCX files. |
| 5 | `scripts/phase5_upload.py` | Re upload fixed files through the Ally feedback window using Playwright `expect_download` for safe download interception. |

Image alt text generation in phase 4b is performed by parallel agents, one per document, capped at a configurable number of images per file.

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

### Run the pipeline

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
  phase1_scrape.py         Phase 1: scrape report
  phase2_targets.py        Phase 2: filter targets
  phase3_download.py       Phase 3: download files from course outline
  phase4_fix.py            Phase 4: apply deterministic fixes
  phase4b_apply_alts.py    Phase 4b: apply alt text JSON
  phase5_upload.py         Phase 5: upload fixed files via Ally
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
* Files larger than 5 MB (PDF) or 20 MB (Office) are skipped automatically.

## License

MIT.
