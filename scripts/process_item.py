"""Process a single item from the accessibility report.

Full workflow: click item → download original → fix → upload fixed version.
Uses disconnect/reconnect pattern throughout.

Usage:
    python scripts/process_item.py <course_id> <item_name>
    python scripts/process_item.py _1308272_1 "ITEC 760 - Cyberinfra and IA.doc"
    python scripts/process_item.py CYBERINFRA "ITEC 760 - Cyberinfra and IA.doc"
"""
import sys, os, time, subprocess, shutil, glob
from bb_utils import (connect, disconnect, dismiss_popup, BASE_DIR, COURSE_DIR,
                      get_report_items)

LIBREOFFICE = "C:/Program Files/LibreOffice/program/soffice.exe"
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_MB_OFFICE = 20  # Higher limit for PPTX/PPT/DOCX/DOC
MAX_PAGES = 100

COURSES = {
    'CYBERINFRA': ('_1308272_1', 'CYBERINFRA-FALL-2025'),
    'ITEC493': ('_1308255_1', 'ITEC493-001-FALL-2025'),
    'ITEC445': ('_1328539_1', 'ITEC445-001-SPRING-2026'),
    'ITEC552': ('_1308261_1', 'ITEC552-001-FALL-2025'),
}


def get_course_info(arg):
    """Resolve course argument to (course_id, folder_name)."""
    if arg.upper() in COURSES:
        return COURSES[arg.upper()]
    # Assume it's a course_id, derive folder name
    return arg, arg


def ensure_dirs(course_folder):
    """Create course download directory if needed."""
    download_dir = os.path.join(COURSE_DIR, course_folder, '_downloads')
    os.makedirs(download_dir, exist_ok=True)
    return download_dir


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


def click_item_by_name(items_frame, item_name):
    """Click a report item by its name. Returns True if clicked."""
    clicked = items_frame.evaluate("""(name) => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        for (const row of rows) {
            const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
            if (nameEl && nameEl.innerText.trim() === name) {
                const btn = row.querySelector('button');
                if (btn) { btn.click(); return true; }
            }
        }
        return false;
    }""", item_name)
    return clicked


def find_feedback_page(browser):
    """Find the Ally feedback page among open tabs."""
    for pg in browser.contexts[0].pages:
        if 'ally.ac' in pg.url and 'feedback' in pg.url.lower():
            return pg
    return None


def find_feedback_frame(fb_page):
    """Find the frame with feedback content inside the feedback page."""
    for f in fb_page.frames:
        try:
            has_content = f.evaluate(
                '() => !!document.querySelector(".ally-if-feedback-panel, .ally-feedback")'
            )
            if has_content:
                return f
        except:
            pass
    # Fallback: last frame
    return fb_page.frames[-1] if len(fb_page.frames) > 1 else fb_page


def download_from_feedback(fb_page, download_dir):
    """Click 'Download original' in feedback window and wait for file.
    Returns path to downloaded file or None."""
    existing = set(os.listdir(download_dir))

    # Find the download button (get_app icon = download original)
    fb_frame = find_feedback_frame(fb_page)
    try:
        fb_frame.evaluate("""() => {
            // Look for 'Download original file' or download icon
            const links = document.querySelectorAll('a, button');
            for (const el of links) {
                const text = el.innerText.trim().toLowerCase();
                if (text.includes('download original')) {
                    el.click();
                    return true;
                }
            }
            // Try icon-based button
            const icons = document.querySelectorAll('[class*="get_app"], [aria-label*="download"], [title*="download"]');
            for (const el of icons) {
                el.click();
                return true;
            }
            return false;
        }""")
    except Exception as e:
        print(f"  Error clicking download: {e}")
        return None

    # Wait for file to appear
    for _ in range(30):
        time.sleep(1)
        current = set(os.listdir(download_dir))
        new_files = current - existing
        # Filter out partial downloads
        new_files = {f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')}
        if new_files:
            downloaded = new_files.pop()
            path = os.path.join(download_dir, downloaded)
            print(f"  Downloaded: {downloaded} ({os.path.getsize(path):,} bytes)")
            return path

    print("  Download timed out")
    return None


def upload_to_feedback(fb_page, fixed_path):
    """Upload fixed file via the feedback window. Returns True on success."""
    fb_frame = find_feedback_frame(fb_page)

    # Find file input element
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        # Try the main page
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        print("  Could not find file input for upload")
        return False

    file_input.set_input_files(fixed_path)
    print(f"  Uploading: {os.path.basename(fixed_path)}")

    # Wait for upload confirmation
    for _ in range(60):
        time.sleep(1)
        try:
            score_text = fb_frame.evaluate("""() => {
                const el = document.querySelector('.ally-if-score-value, .feedback-score-indicator span');
                return el ? el.innerText.trim() : '';
            }""")
            if score_text and '%' in score_text:
                print(f"  New score: {score_text}")
                return True
        except:
            pass

    print("  Upload may have succeeded but could not verify score")
    return True


def convert_old_format(input_path, download_dir):
    """Convert .doc/.ppt to .docx/.pptx using LibreOffice. Returns new path or None."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in ('.doc', '.ppt'):
        return None

    print(f"  Converting {ext} to {ext}x with LibreOffice...")
    result = subprocess.run(
        [LIBREOFFICE, '--headless', '--convert-to',
         'docx' if ext == '.doc' else 'pptx',
         '--outdir', download_dir, input_path],
        capture_output=True, text=True, timeout=60
    )

    if result.returncode != 0:
        print(f"  LibreOffice conversion failed: {result.stderr}")
        return None

    # Find the converted file
    new_ext = '.docx' if ext == '.doc' else '.pptx'
    stem = os.path.splitext(os.path.basename(input_path))[0]
    converted = os.path.join(download_dir, stem + new_ext)
    if os.path.exists(converted):
        print(f"  Converted: {os.path.basename(converted)} ({os.path.getsize(converted):,} bytes)")
        return converted

    print("  Conversion output file not found")
    return None


def fix_file(file_path, download_dir):
    """Fix accessibility issues in a file. Returns path to fixed file or None."""
    ext = os.path.splitext(file_path)[1].lower()
    stem = os.path.splitext(os.path.basename(file_path))[0]

    # Check file size (higher limit for Office files)
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    max_size = MAX_FILE_SIZE_MB_OFFICE if ext in ('.pptx', '.ppt', '.docx', '.doc') else MAX_FILE_SIZE_MB
    if size_mb > max_size:
        print(f"  Skipping: file too large ({size_mb:.1f} MB > {max_size} MB)")
        return None

    # For old formats, convert first
    working_path = file_path
    if ext in ('.doc', '.ppt'):
        working_path = convert_old_format(file_path, download_dir)
        if not working_path:
            return None
        ext = os.path.splitext(working_path)[1].lower()

    if ext == '.pdf':
        return fix_pdf_file(working_path, download_dir)
    elif ext == '.docx':
        return fix_docx_file(working_path, download_dir)
    elif ext == '.pptx':
        return fix_pptx_file(working_path, download_dir)
    else:
        print(f"  Unsupported format: {ext}")
        return None


def fix_pdf_file(file_path, download_dir):
    """Fix PDF accessibility: tags, language, title, headings."""
    # Import here to avoid circular imports
    sys.path.insert(0, os.path.dirname(__file__))
    from fix_pdf import fix_pdf
    from add_headings import add_headings_to_pdf

    stem = os.path.splitext(os.path.basename(file_path))[0]
    if stem.endswith('_fixed'):
        fixed_path = file_path
    else:
        fixed_path = os.path.join(download_dir, stem + '_fixed.pdf')

    # First pass: tags, language, title
    result = fix_pdf(file_path, fixed_path)
    print(f"  PDF fix: {result}")

    # Second pass: headings
    source = fixed_path if os.path.exists(fixed_path) else file_path
    try:
        result2 = add_headings_to_pdf(source, fixed_path)
        print(f"  Headings: {result2}")
    except Exception as e:
        print(f"  Headings failed: {e}")

    return fixed_path if os.path.exists(fixed_path) else None


def fix_docx_file(file_path, download_dir):
    """Fix DOCX accessibility: title, language, headings."""
    from fix_office import fix_docx

    stem = os.path.splitext(os.path.basename(file_path))[0]
    if stem.endswith('_fixed'):
        fixed_path = file_path
    else:
        fixed_path = os.path.join(download_dir, stem + '_fixed.docx')

    result = fix_docx(file_path, fixed_path)
    print(f"  DOCX fix: {result}")

    return fixed_path if result.get('status') == 'fixed' and os.path.exists(fixed_path) else None


def fix_pptx_file(file_path, download_dir):
    """Fix PPTX accessibility: title, language, slide titles."""
    from fix_office import fix_pptx

    stem = os.path.splitext(os.path.basename(file_path))[0]
    if stem.endswith('_fixed'):
        fixed_path = file_path
    else:
        fixed_path = os.path.join(download_dir, stem + '_fixed.pptx')

    result = fix_pptx(file_path, fixed_path)
    print(f"  PPTX fix: {result}")

    return fixed_path if result.get('status') == 'fixed' and os.path.exists(fixed_path) else None


def process_item(course_arg, item_name, dry_run=False):
    """Full workflow: click item → download → fix → upload."""
    course_id, course_folder = get_course_info(course_arg)
    download_dir = ensure_dirs(course_folder)

    print(f"\n=== Processing: {item_name} ===")

    # Step 1: Find the item in the report and click it
    print("Step 1: Clicking item in report...")
    p, browser, page = connect()

    # Set Chrome download dir
    cdp = browser.contexts[0].pages[0]
    try:
        cdp_session = page.context.new_cdp_session(page)
        cdp_session.send('Browser.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_dir.replace('/', '\\')
        })
    except:
        pass

    items_frame = find_items_frame(page)
    if not items_frame:
        print("ERROR: Could not find items frame. Is the report loaded on Content tab?")
        disconnect(p, browser)
        return False

    clicked = click_item_by_name(items_frame, item_name)
    if not clicked:
        print(f"ERROR: Item '{item_name}' not found in current page")
        disconnect(p, browser)
        return False

    print("  Clicked. Disconnecting to let feedback window load...")
    disconnect(p, browser)
    time.sleep(15)

    # Step 2: Find feedback window and download
    print("Step 2: Downloading from feedback window...")
    p, browser, page = connect()

    fb_page = find_feedback_page(browser)
    if not fb_page:
        print("ERROR: Feedback window not found")
        disconnect(p, browser)
        return False

    # Set download path on feedback page too
    try:
        cdp_session = fb_page.context.new_cdp_session(fb_page)
        cdp_session.send('Browser.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_dir.replace('/', '\\')
        })
    except:
        pass

    downloaded = download_from_feedback(fb_page, download_dir)

    # Close feedback window
    fb_page.close()
    disconnect(p, browser)

    if not downloaded:
        print("ERROR: Download failed")
        return False

    # Step 3: Fix the file
    print("Step 3: Fixing accessibility issues...")
    if dry_run:
        print("  [DRY RUN] Would fix file here")
        return True

    fixed_path = fix_file(downloaded, download_dir)
    if not fixed_path:
        print("  No fixes applied or fix failed")
        return False

    # Step 4: Click item again to upload
    print("Step 4: Re-opening feedback for upload...")
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        print("ERROR: Could not find items frame for upload")
        disconnect(p, browser)
        return False

    clicked = click_item_by_name(items_frame, item_name)
    if not clicked:
        print(f"ERROR: Could not re-click item for upload")
        disconnect(p, browser)
        return False

    disconnect(p, browser)
    print("  Waiting for feedback window...")
    time.sleep(15)

    # Step 5: Upload
    print("Step 5: Uploading fixed file...")
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        print("ERROR: Feedback window not found for upload")
        disconnect(p, browser)
        return False

    success = upload_to_feedback(fb_page, fixed_path)

    # Close feedback
    fb_page.close()
    disconnect(p, browser)

    if success:
        print(f"\n=== Done: {item_name} ===")
    else:
        print(f"\n=== Upload may have failed for: {item_name} ===")

    return success


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python process_item.py <course> <item_name> [--dry-run]")
        print(f"Known courses: {', '.join(COURSES.keys())}")
        sys.exit(1)

    course = sys.argv[1]
    item_name = sys.argv[2]
    dry_run = '--dry-run' in sys.argv

    process_item(course, item_name, dry_run=dry_run)
