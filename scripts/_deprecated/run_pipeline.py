"""Full 4-phase accessibility fix pipeline.

Phase 1: Scrape accessibility report (items + scores)
Phase 2: Navigate course structure and download target files
Phase 3: Fix all downloaded files locally (PDF, DOCX, PPTX, convert .doc/.ppt)
Phase 4: Upload fixed files via accessibility report feedback window

Usage:
    python scripts/run_pipeline.py <course>
    python scripts/run_pipeline.py CYBERINFRA
    python scripts/run_pipeline.py CYBERINFRA --phase 3    # Start from phase 3
    python scripts/run_pipeline.py CYBERINFRA --dry-run
"""
import sys, os, time, json, subprocess, glob, argparse

sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import (connect, disconnect, dismiss_popup, save_json, load_json,
                      DATA_DIR, COURSE_DIR, get_report_items)

LIBREOFFICE = "C:/Program Files/LibreOffice/program/soffice.exe"
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_MB_OFFICE = 20  # Higher limit for PPTX/PPT/DOCX/DOC
MAX_PAGES = 100

COURSES = {
    'CYBERINFRA': {'id': '_1308272_1', 'dir': 'CYBERINFRA-FALL-2025',
                   'report': 'accessibility_report_CYBERINFRA.json'},
    'ITEC493': {'id': '_1308255_1', 'dir': 'ITEC493-001-FALL-2025',
                'report': 'accessibility_report_ITEC493.json'},
    'ITEC445': {'id': '_1328539_1', 'dir': 'ITEC445-001-SPRING-2026',
                'report': 'accessibility_report_ITEC445.json'},
    'ITEC552': {'id': '_1308261_1', 'dir': 'ITEC552-001-FALL-2025',
                'report': 'accessibility_report_ITEC552.json'},
    'ITEC445F': {'id': '_1308248_1', 'dir': 'ITEC445-001-FALL-2025',
                 'report': 'accessibility_report_ITEC445F.json'},
}


# ── Phase 1: Scrape accessibility report ──────────────────────────────────

def phase1_scrape_report(course_key):
    """Scrape the accessibility report and save as JSON."""
    info = COURSES[course_key]
    report_file = info['report']
    report_path = os.path.join(DATA_DIR, report_file)

    print(f"\n{'='*60}")
    print(f"PHASE 1: Scrape accessibility report")
    print(f"{'='*60}")

    # Use load_report.py logic with disconnect/reconnect
    from load_report import load_report_content, find_items_frame, find_report_frame

    # First page
    all_items = load_report_content(info['id'])

    if not all_items:
        print("ERROR: No items found in report")
        return []

    # Check for more pages
    page_num = 1
    while True:
        # See if there's a next page
        p, browser, page = connect()
        items_frame = find_items_frame(page)
        if not items_frame:
            disconnect(p, browser)
            break

        clicked = items_frame.evaluate("""() => {
            const links = document.querySelectorAll('a');
            for (const link of links) {
                if (link.innerText.trim().includes('Next')) {
                    link.click();
                    return true;
                }
            }
            return false;
        }""")
        disconnect(p, browser)

        if not clicked:
            break

        page_num += 1
        time.sleep(5)

        p, browser, page = connect()
        items_frame = find_items_frame(page)
        if items_frame:
            items = get_report_items(items_frame)
            if items:
                all_items.extend(items)
                print(f"  Page {page_num}: {len(items)} items")
            else:
                disconnect(p, browser)
                break
        disconnect(p, browser)

    # Save report
    os.makedirs(DATA_DIR, exist_ok=True)
    save_json(all_items, report_file)
    print(f"\nSaved {len(all_items)} items to data/{report_file}")

    # Show items below 85%
    below = [i for i in all_items
             if i.get('score', '').replace('%', '').isdigit()
             and int(i['score'].replace('%', '')) < 85]
    print(f"Items below 85%: {len(below)}")
    for item in below:
        print(f"  {item['score']:>5}  {item['name']}")

    return all_items


# ── Phase 2: Download files from course structure ─────────────────────────

def phase2_download(course_key):
    """Download target files by navigating the course structure."""
    info = COURSES[course_key]

    print(f"\n{'='*60}")
    print(f"PHASE 2: Download files from course structure")
    print(f"{'='*60}")

    # Run download_all.py as a subprocess (it has all the course nav logic)
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), 'download_all.py'), course_key],
        cwd=os.path.dirname(__file__),
        timeout=600
    )

    if result.returncode != 0:
        print(f"WARNING: download_all.py exited with code {result.returncode}")

    # List what was downloaded
    course_dir = os.path.join(COURSE_DIR, info['dir'])
    downloaded = []
    for root, dirs, files in os.walk(course_dir):
        for f in files:
            if not f.endswith('_fixed.pdf') and not f.endswith('_fixed.docx') and not f.endswith('_fixed.pptx'):
                downloaded.append(os.path.join(root, f))

    print(f"\nFiles in {info['dir']}/: {len(downloaded)}")
    for f in downloaded:
        size = os.path.getsize(f)
        print(f"  {os.path.basename(f)} ({size:,} bytes)")

    return downloaded


# ── Phase 3: Fix all downloaded files ─────────────────────────────────────

def phase3_fix(course_key):
    """Fix all downloaded files locally. Returns (fixed_files, images_needing_alt).

    Step 1: Convert old formats (.doc/.ppt -> .docx/.pptx)
    Step 2: Apply non-image fixes (title, language, headings)
    Step 3: Extract images needing alt text from PPTX files

    Image alt texts must be generated externally (e.g. via Claude subagents)
    and applied with phase3_apply_alt_texts().
    """
    info = COURSES[course_key]
    course_dir = os.path.join(COURSE_DIR, info['dir'])

    print(f"\n{'='*60}")
    print(f"PHASE 3: Fix downloaded files")
    print(f"{'='*60}")

    from fix_pdf import fix_pdf
    from add_headings import add_headings_to_pdf
    from fix_office import fix_docx, fix_pptx, extract_pptx_images

    fixed_files = []
    skipped = []
    all_images_needing_alt = []  # List of {pptx_path, fixed_path, images: [...]}

    # Find all non-fixed files
    for root, dirs, files in os.walk(course_dir):
        for fname in files:
            # Skip already-fixed files, metadata, and incomplete downloads
            if '_fixed.' in fname or fname.endswith('.json') or fname.endswith('.crdownload') or fname.endswith('.tmp'):
                continue
            # Skip converted files if original still exists
            stem_base = os.path.splitext(fname)[0]
            ext_lower = os.path.splitext(fname)[1].lower()
            if ext_lower in ('.pptx', '.docx'):
                orig_ppt = os.path.join(root, stem_base + '.ppt')
                orig_doc = os.path.join(root, stem_base + '.doc')
                if os.path.exists(orig_ppt) or os.path.exists(orig_doc):
                    continue  # Will be handled when we process the .ppt/.doc

            fpath = os.path.join(root, fname)
            ext = ext_lower
            stem = stem_base
            size_mb = os.path.getsize(fpath) / (1024 * 1024)

            # Skip large files (higher limit for Office files)
            max_size = MAX_FILE_SIZE_MB_OFFICE if ext in ('.pptx', '.ppt', '.docx', '.doc') else MAX_FILE_SIZE_MB
            if size_mb > max_size:
                print(f"  SKIP (too large: {size_mb:.1f}MB): {fname}")
                skipped.append(fname)
                continue

            print(f"\n  Fixing: {fname} ({size_mb:.1f}MB)")

            # Convert old formats first
            working_path = fpath
            if ext in ('.doc', '.ppt'):
                new_ext = '.docx' if ext == '.doc' else '.pptx'
                converted = os.path.join(root, stem + new_ext)

                if os.path.exists(converted):
                    print(f"    Already converted: {stem + new_ext}")
                    working_path = converted
                else:
                    print(f"    Converting {ext} -> {new_ext} with LibreOffice...")
                    try:
                        subprocess.run(
                            [LIBREOFFICE, '--headless', '--convert-to',
                             new_ext[1:], '--outdir', root, fpath],
                            capture_output=True, text=True, timeout=60
                        )
                        if os.path.exists(converted):
                            print(f"    Converted: {os.path.basename(converted)}")
                            working_path = converted
                        else:
                            print(f"    Conversion failed")
                            skipped.append(fname)
                            continue
                    except Exception as e:
                        print(f"    Conversion error: {e}")
                        skipped.append(fname)
                        continue

                ext = os.path.splitext(working_path)[1].lower()
                stem = os.path.splitext(os.path.basename(working_path))[0]

            # Build fixed path
            fixed_path = os.path.join(root, stem + '_fixed' + ext)

            try:
                if ext == '.pdf':
                    # Tags + language + title
                    result = fix_pdf(working_path, fixed_path)
                    print(f"    PDF tags: {result.get('status', 'unknown')}")

                    # Headings
                    source = fixed_path if os.path.exists(fixed_path) else working_path
                    try:
                        result2 = add_headings_to_pdf(source, fixed_path)
                        print(f"    Headings: {result2.get('status', 'unknown')}")
                    except Exception as e:
                        print(f"    Headings error: {e}")

                elif ext == '.docx':
                    result = fix_docx(working_path, fixed_path)
                    print(f"    DOCX: {result}")

                elif ext == '.pptx':
                    # First apply title/language/slide title fixes
                    result = fix_pptx(working_path, fixed_path)
                    print(f"    PPTX basic fixes: {result}")

                    # Extract images needing alt text
                    imgs_dir = os.path.join(root, '_imgs_' + stem)
                    source = fixed_path if os.path.exists(fixed_path) else working_path
                    images = extract_pptx_images(source, imgs_dir)
                    if images:
                        print(f"    Found {len(images)} images needing alt text")
                        all_images_needing_alt.append({
                            'pptx_path': source,
                            'fixed_path': fixed_path,
                            'original_name': fname,
                            'images': images,
                        })
                    else:
                        print(f"    No images need alt text")

                else:
                    print(f"    Unsupported: {ext}")
                    skipped.append(fname)
                    continue

                if os.path.exists(fixed_path):
                    fixed_files.append(fixed_path)
                    print(f"    Saved: {os.path.basename(fixed_path)} ({os.path.getsize(fixed_path):,} bytes)")
                elif ext != '.pptx':
                    # PPTX might not have fixed file yet (waiting for alt texts)
                    print(f"    No fixed file produced")
                    skipped.append(fname)

            except Exception as e:
                print(f"    Error: {e}")
                skipped.append(fname)

    print(f"\nFixed: {len(fixed_files)} files")
    print(f"Skipped: {len(skipped)} files")
    if all_images_needing_alt:
        total_imgs = sum(len(entry['images']) for entry in all_images_needing_alt)
        print(f"Images needing alt text: {total_imgs} across {len(all_images_needing_alt)} PPTX files")

        # Save image metadata for external processing
        img_meta_path = os.path.join(DATA_DIR, f'images_needing_alt_{course_key}.json')
        save_json(all_images_needing_alt, f'images_needing_alt_{course_key}.json')
        print(f"Image metadata saved to: {img_meta_path}")

    return fixed_files, all_images_needing_alt


def phase3_apply_alt_texts(course_key, alt_texts_by_file):
    """Apply generated alt texts to PPTX files.

    alt_texts_by_file: dict mapping fixed_path -> list of {slide, shape_idx, alt_text}
    """
    from fix_office import apply_pptx_alt_texts, fix_pptx

    print(f"\n{'='*60}")
    print(f"PHASE 3b: Apply image alt texts")
    print(f"{'='*60}")

    for fixed_path, alt_texts in alt_texts_by_file.items():
        source = fixed_path if os.path.exists(fixed_path) else fixed_path.replace('_fixed.', '.')
        result = apply_pptx_alt_texts(source, fixed_path, alt_texts)
        print(f"  {os.path.basename(fixed_path)}: applied {result['applied']}/{result['total']} alt texts")

    print("Done applying alt texts.")


# ── Phase 4: Upload fixed files via report feedback ──────────────────────

def find_items_frame(page):
    """Find the frame containing report item rows."""
    for f in page.frames:
        try:
            count = f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length')
            if count > 0:
                return f
        except:
            pass
    return None


def find_report_frame(page):
    """Find the frame containing 'Course accessibility' text."""
    for f in page.frames:
        try:
            if f.evaluate('() => document.body.innerText.includes("Course accessibility")'):
                return f
        except:
            pass
    return None


def find_feedback_page(browser):
    """Find the Ally feedback page."""
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            return pg
    return None


def find_feedback_frame(fb_page):
    """Find feedback content frame."""
    for f in fb_page.frames:
        try:
            has = f.evaluate('() => !!document.querySelector(".ally-if-feedback-panel, .ally-feedback, input[type=file]")')
            if has:
                return f
        except:
            pass
    return fb_page.frames[-1] if len(fb_page.frames) > 1 else fb_page


def navigate_to_report_content(course_id):
    """Navigate to report and click Content tab. Uses disconnect/reconnect."""
    from bb_utils import navigate_to_report

    p, browser, page = connect()
    navigate_to_report(page, course_id)
    disconnect(p, browser)
    print("  Navigated to report, waiting...")
    time.sleep(15)

    # Click Content tab
    p, browser, page = connect()
    dismiss_popup(page)
    rf = find_report_frame(page)
    if rf:
        rf.evaluate("""() => {
            for (const t of document.querySelectorAll('a, button')) {
                if (t.innerText.trim() === 'Content') { t.click(); return true; }
            }
            return false;
        }""")
    disconnect(p, browser)
    print("  Clicked Content tab, waiting...")
    time.sleep(10)


def upload_one_item(course_id, item_name, fixed_path):
    """Click item in report, upload fixed file via feedback window.
    Returns new score or None."""

    # Click the item
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        print(f"    Items frame not found")
        disconnect(p, browser)
        return None

    clicked = items_frame.evaluate("""(name) => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        for (const row of rows) {
            const el = row.querySelector('.ir-content-list-item-name-text-name');
            if (el && el.innerText.trim() === name) {
                const btn = row.querySelector('button');
                if (btn) { btn.click(); return true; }
            }
        }
        return false;
    }""", item_name)

    if not clicked:
        print(f"    Item '{item_name}' not found in report")
        disconnect(p, browser)
        return None

    disconnect(p, browser)
    print(f"    Clicked, waiting for feedback window...")
    time.sleep(15)

    # Find feedback window and upload
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        print(f"    Feedback window not found")
        disconnect(p, browser)
        return None

    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        print(f"    No file input found")
        fb_page.close()
        disconnect(p, browser)
        return None

    file_input.set_input_files(fixed_path)
    print(f"    Uploading {os.path.basename(fixed_path)}...")

    # Wait for new score
    new_score = None
    for _ in range(60):
        time.sleep(1)
        try:
            score_text = fb_frame.evaluate("""() => {
                const el = document.querySelector('.ally-if-score-value, .feedback-score-indicator span');
                return el ? el.innerText.trim() : '';
            }""")
            if score_text and '%' in score_text:
                new_score = score_text
                break
        except:
            pass

    # Close feedback
    fb_page.close()
    disconnect(p, browser)
    time.sleep(2)

    return new_score


def phase4_upload(course_key):
    """Upload all fixed files via accessibility report feedback."""
    info = COURSES[course_key]
    course_dir = os.path.join(COURSE_DIR, info['dir'])
    report_path = os.path.join(DATA_DIR, info['report'])

    print(f"\n{'='*60}")
    print(f"PHASE 4: Upload fixed files")
    print(f"{'='*60}")

    # Load report to map names
    if not os.path.exists(report_path):
        print("ERROR: Report not found. Run phase 1 first.")
        return

    report_items = load_json(info['report'])
    report_names = {item['name'] for item in report_items}

    # Find all fixed files
    fixed_files = {}
    for root, dirs, files in os.walk(course_dir):
        for fname in files:
            if '_fixed.' in fname:
                # Map back to original name in report
                # e.g., "Midterm Review(1)_fixed.docx" -> find matching report name
                stem = fname.replace('_fixed.', '.')
                # Also try without _fixed for converted files
                # e.g., "F24-DSci523-Lec5(1)_fixed.pptx" was originally "F24-DSci523-Lec5(1).ppt"
                base_stem = os.path.splitext(stem)[0]
                fixed_ext = os.path.splitext(fname)[1]

                # Try exact match first
                if stem in report_names:
                    fixed_files[stem] = os.path.join(root, fname)
                else:
                    # Try with original extension (.ppt, .doc)
                    for orig_ext in ['.ppt', '.doc']:
                        orig_name = base_stem + orig_ext
                        if orig_name in report_names:
                            fixed_files[orig_name] = os.path.join(root, fname)
                            break
                    else:
                        # Try matching by base name
                        for rname in report_names:
                            if base_stem in rname or rname.replace('.', '_fixed.') == fname:
                                fixed_files[rname] = os.path.join(root, fname)
                                break

    if not fixed_files:
        print("No fixed files found to upload.")
        return

    print(f"Fixed files to upload: {len(fixed_files)}")
    for name, path in fixed_files.items():
        print(f"  {name} -> {os.path.basename(path)}")

    # Navigate to report content tab
    navigate_to_report_content(info['id'])

    # Upload each file
    uploaded = 0
    failed = 0
    for item_name, fixed_path in fixed_files.items():
        print(f"\n  Uploading: {item_name}")
        new_score = upload_one_item(info['id'], item_name, fixed_path)

        if new_score:
            print(f"    NEW SCORE: {new_score}")
            uploaded += 1
        else:
            print(f"    Upload completed (score not verified)")
            uploaded += 1

        # Refresh report after each upload (re-sorts by score)
        print("    Refreshing report...")
        p, browser, page = connect()
        page.reload()
        disconnect(p, browser)
        time.sleep(15)

        # Re-click Content tab
        p, browser, page = connect()
        rf = find_report_frame(page)
        if rf:
            rf.evaluate("""() => {
                for (const t of document.querySelectorAll('a, button')) {
                    if (t.innerText.trim() === 'Content') { t.click(); return true; }
                }
                return false;
            }""")
        disconnect(p, browser)
        time.sleep(10)

    print(f"\nUploaded: {uploaded}, Failed: {failed}")


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Full accessibility fix pipeline')
    parser.add_argument('course', help='Course key (e.g., CYBERINFRA)')
    parser.add_argument('--phase', type=int, default=1, help='Start from phase (1-4)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()

    course = args.course.upper()
    if course not in COURSES:
        print(f"Unknown course: {course}")
        print(f"Known courses: {', '.join(COURSES.keys())}")
        sys.exit(1)

    start = args.phase

    if start <= 1:
        phase1_scrape_report(course)
    if start <= 2:
        phase2_download(course)
    if start <= 3:
        fixed, images_needing_alt = phase3_fix(course)
        if images_needing_alt:
            print("\n*** PPTX images need alt text descriptions. ***")
            print("Generate descriptions externally (e.g. Claude subagents),")
            print("then run: python run_pipeline.py <course> --phase 4")
            print("Or call phase3_apply_alt_texts() with the descriptions.")
            sys.exit(0)
    if start <= 4:
        phase4_upload(course)

    print(f"\n{'='*60}")
    print(f"Pipeline complete for {course}")
    print(f"{'='*60}")
