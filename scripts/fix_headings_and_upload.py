"""Add headings to PDFs and upload to Blackboard accessibility report.

Reusable script that:
1. Navigates to the accessibility report Content tab
2. For each target item: adds headings, clicks item, uploads fixed version
3. Disconnects/reconnects between items to free Chrome

Usage:
    python fix_headings_and_upload.py ITEC493                          # Process all fixable items on page 1
    python fix_headings_and_upload.py ITEC493 --item "Module 3 Slides.pdf"  # Single item
    python fix_headings_and_upload.py ITEC493 --dry-run                # Just list what would be fixed
    python fix_headings_and_upload.py ITEC493 --page 2                 # Process page 2 of report
"""
import sys, os, time, argparse
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from bb_utils import (connect, disconnect, dismiss_popup, navigate_to_report,
                      COURSE_DIR, CDP_URL)
from add_headings import add_headings_to_pdf, analyze_fonts, detect_heading_sizes, extract_headings

SCORE_THRESHOLD = 85
MAX_FILE_SIZE_MB = 5
MAX_PAGES = 100

COURSES = {
    "ITEC493": {"id": "_1308255_1", "dir": "ITEC493-001-FALL-2025"},
    "ITEC445": {"id": "_1328539_1", "dir": "ITEC445-001-SPRING-2026"},
    "ITEC552": {"id": "_1308261_1", "dir": "ITEC552-001-FALL-2025"},
    "CYBERINFRA": {"id": "_1308272_1", "dir": "CYBERINFRA-FALL-2025"},
}


def load_report_content(browser, p, course_id):
    """Navigate to report, click Content tab, return (items_frame, browser, p).
    Uses disconnect/reconnect to avoid slowing Chrome."""
    page = browser.contexts[0].pages[-1]

    # Check if already on this course's report with Content loaded
    for pg in browser.contexts[0].pages:
        if course_id in pg.url:
            for f in pg.frames:
                try:
                    count = f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length')
                    if count > 0:
                        return f, browser, p
                except:
                    pass

    # Navigate to report, click Content tab, then disconnect to let it load
    navigate_to_report(page, course_id)
    time.sleep(3)
    dismiss_popup(page)

    # Find report frame and click Content tab
    for f in page.frames:
        try:
            if f.evaluate('() => document.body.innerText.includes("Course accessibility")'):
                f.evaluate("""() => {
                    for (const t of document.querySelectorAll('a, button')) {
                        if (t.innerText.trim() === 'Content') { t.click(); return; }
                    }
                }""")
                break
        except:
            pass

    # Disconnect to let Chrome load freely
    browser.close()
    p.stop()
    time.sleep(15)

    # Reconnect and find items
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)

    for pg in browser.contexts[0].pages:
        for f in pg.frames:
            try:
                count = f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length')
                if count > 0:
                    return f, browser, p
            except:
                pass

    return None, browser, p


def get_visible_items(items_frame):
    """Get all items on current report page."""
    return items_frame.evaluate("""() => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        const data = [];
        rows.forEach(row => {
            const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
            const scoreEl = row.querySelector('.feedback-score-indicator span');
            if (nameEl) {
                data.push({
                    name: nameEl.innerText.trim(),
                    score: scoreEl ? scoreEl.innerText.trim() : '?'
                });
            }
        });
        return data;
    }""")


def open_feedback(items_frame, item_name, browser, p):
    """Click item in report, disconnect/reconnect, return feedback page.
    Returns (fb_page, fb_frame, browser, p)."""
    # Close existing feedback windows
    for pg in list(browser.contexts[0].pages):
        if 'ally.ac' in pg.url:
            pg.close()
            time.sleep(0.3)

    # Click item with locator (real mouse event)
    try:
        items_frame.locator(f'text="{item_name}"').click(timeout=10000)
    except:
        items_frame.evaluate("""(name) => {
            const rows = document.querySelectorAll('tr.ir-list-item');
            for (const row of rows) {
                const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
                if (nameEl && nameEl.innerText.trim() === name) {
                    const btn = row.querySelector('button');
                    if (btn) btn.click();
                    return;
                }
            }
        }""", item_name)

    # Disconnect to free Chrome for popup
    browser.close()
    p.stop()
    time.sleep(15)

    # Reconnect
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)

    # Find feedback page
    fb_page = None
    for pg in browser.contexts[0].pages:
        if 'ally.ac' in pg.url and 'launchinstructorfeedback' in pg.url:
            fb_page = pg
            break

    if not fb_page:
        return None, None, browser, p

    # Get feedback frame
    fb_frame = None
    for f in fb_page.frames:
        try:
            text = f.evaluate('() => document.body.innerText')
            if 'Accessibility score' in text or 'Browse' in text:
                fb_frame = f
                break
        except:
            pass

    return fb_page, fb_frame, browser, p


def download_from_feedback(fb_page, fb_frame, download_dir):
    """Download the original file from the feedback window. Returns filepath or None."""
    os.makedirs(download_dir, exist_ok=True)

    # Set download behavior
    cdp = fb_page.context.new_cdp_session(fb_page)
    cdp.send("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": os.path.abspath(download_dir).replace("/", os.sep),
    })

    files_before = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()

    # Click "Download original" (icon text is get_app)
    fb_frame.evaluate("""() => {
        const els = document.querySelectorAll('a, button, span');
        for (const el of els) {
            const text = el.innerText.trim();
            const label = el.getAttribute('aria-label') || '';
            if (text === 'get_app' || text === 'Download original' ||
                label.includes('Download original')) {
                el.click(); return true;
            }
        }
        return false;
    }""")

    # Wait for download
    for _ in range(30):
        time.sleep(1)
        if os.path.exists(download_dir):
            current = set(os.listdir(download_dir))
            new_files = current - files_before
            completed = [f for f in new_files if not f.endswith('.crdownload')]
            if completed:
                return os.path.join(download_dir, completed[0])
    return None


def upload_to_feedback(fb_page, fb_frame, fixed_path):
    """Upload a fixed file and wait for new score. Returns (new_score, remaining)."""
    info_text = fb_frame.evaluate('() => document.body.innerText')
    current_score = '?'
    for line in info_text.split('\n'):
        line = line.strip()
        if line.endswith('%') and len(line) < 5:
            current_score = line
    print(f"  Current score: {current_score}")

    # Upload
    for f in fb_page.frames:
        inp = f.query_selector('input[type=file]')
        if inp:
            inp.set_input_files(os.path.abspath(fixed_path))
            break
    else:
        return current_score, []

    # Wait for verification
    new_score = None
    remaining = []
    for attempt in range(15):
        time.sleep(5)
        try:
            text = fb_frame.evaluate('() => document.body.innerText')
            if 'Verifying' not in text and '_fixed' in text:
                for line in text.split('\n'):
                    line = line.strip()
                    if line.endswith('%') and len(line) < 5:
                        new_score = line
                    if line.startswith('This PDF') or line.startswith('This document'):
                        remaining.append(line)
                break
        except:
            pass

    return new_score, remaining


def close_feedback(browser, p):
    """Close feedback window by disconnecting/reconnecting."""
    browser.close()
    p.stop()
    time.sleep(2)
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)
    return browser, p


def find_local_pdf(name, course_dir):
    """Find the local PDF file matching the report item name."""
    base = os.path.join(COURSE_DIR, course_dir)
    for root, dirs, files in os.walk(base):
        for fname in files:
            if fname == name:
                return os.path.join(root, fname)
            # Also check if the _fixed version's original matches
            if fname.replace('_fixed', '').replace('_tagged', '') == name:
                return os.path.join(root, fname)
    return None


def can_add_headings(pdf_path):
    """Check if a PDF has text with heading hierarchy. Skips large files."""
    import pymupdf
    size_mb = os.path.getsize(pdf_path) / 1024 / 1024
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f'too large ({size_mb:.1f} MB)'
    doc = pymupdf.open(pdf_path)
    pages = len(doc)
    doc.close()
    if pages > MAX_PAGES:
        return False, f'too many pages ({pages})'
    fc = analyze_fonts(pdf_path)
    if not fc:
        return False, 'image-based'
    hmap, body = detect_heading_sizes(fc)
    if not hmap:
        return False, 'single font size'
    headings = extract_headings(pdf_path, hmap)
    return len(headings) > 0, f'{len(headings)} headings'


def scan_and_fix_page(items_frame, course_dir, single_item=None):
    """Scan current report page for fixable items. Returns list of fixable items."""
    items = get_visible_items(items_frame)
    targets = []
    for i in items:
        score = int(i['score'].replace('%', ''))
        if score >= SCORE_THRESHOLD:
            break  # Sorted ascending — all remaining are above threshold
        targets.append(i)

    if single_item:
        targets = [t for t in items if t['name'] == single_item]

    fixable = []
    for target in targets:
        name = target['name']
        local = find_local_pdf(name, course_dir)
        if not local:
            base_name = name.replace('_fixed', '').replace('_tagged', '')
            local = find_local_pdf(base_name, course_dir)

        if not local:
            # Not found locally — will download from report if it's a PDF
            if name.lower().endswith('.pdf'):
                fixable.append({'name': name, 'score': target['score'], 'local': None})
                print(f"  {target['score']:>4s}  {name:50s}  WILL DOWNLOAD + FIX")
            else:
                print(f"  {target['score']:>4s}  {name:50s}  SKIP (not PDF, not local)")
            continue

        ok, reason = can_add_headings(local)
        if ok:
            fixable.append({'name': name, 'score': target['score'], 'local': local})
            print(f"  {target['score']:>4s}  {name:50s}  FIXABLE ({reason})")
        else:
            print(f"  {target['score']:>4s}  {name:50s}  SKIP ({reason})")

    return items, targets, fixable


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add headings to PDFs and upload to report')
    parser.add_argument('course', help='Course key (e.g., ITEC493)')
    parser.add_argument('--item', help='Process single item by name')
    parser.add_argument('--dry-run', action='store_true', help='List fixable items without uploading')
    args = parser.parse_args()

    course_key = args.course.upper()
    if course_key not in COURSES:
        print(f"Unknown course '{course_key}'. Known: {list(COURSES.keys())}")
        sys.exit(1)

    course_id = COURSES[course_key]['id']
    course_dir = COURSES[course_key]['dir']

    # Connect and load report
    p, browser, page = connect()
    print(f"Connected. Loading report for {course_key}...")

    items_frame, browser, p = load_report_content(browser, p, course_id)
    if not items_frame:
        print("ERROR: Could not load report items")
        browser.close()
        p.stop()
        sys.exit(1)

    # Scan page 1
    items, targets, fixable = scan_and_fix_page(items_frame, course_dir, args.item)
    print(f"\nPage 1: {len(items)} items, {len(targets)} below {SCORE_THRESHOLD}%, {len(fixable)} fixable\n")

    if args.dry_run:
        # Also check if page 2+ needed
        if len(targets) == 0 or len(targets) < len(items):
            print("All items on page 1 are above threshold or not fixable.")
        disconnect(p, browser)
        sys.exit(0)

    # Process loop: fix items, refresh report, repeat until done
    results = []
    page_num = 1
    item_counter = 0

    while fixable:
        for item in fixable:
            item_counter += 1
            print(f"\n[{item_counter}] {item['name']} ({item['score']})")

            # Open feedback window
            fb_page, fb_frame, browser, p = open_feedback(
                items_frame, item['name'], browser, p
            )
            if not fb_page or not fb_frame:
                print(f"  Feedback not opened")
                results.append({'name': item['name'], 'status': 'feedback not opened'})
                # Refresh report for next item
                items_frame, browser, p = load_report_content(browser, p, course_id)
                continue

            # Download original if not found locally
            local_path = item.get('local')
            if not local_path:
                print(f"  Downloading from report...")
                download_dir = os.path.join(COURSE_DIR, course_dir, '_downloads')
                local_path = download_from_feedback(fb_page, fb_frame, download_dir)
                if not local_path:
                    print(f"  Download failed")
                    results.append({'name': item['name'], 'status': 'download failed'})
                    browser, p = close_feedback(browser, p)
                    items_frame, browser, p = load_report_content(browser, p, course_id)
                    continue
                print(f"  Downloaded: {os.path.basename(local_path)} ({os.path.getsize(local_path):,} bytes)")

            # Add headings
            title = os.path.splitext(item['name'])[0].replace('_fixed', '').replace('_tagged', '').replace('_', ' ')
            fix_result = add_headings_to_pdf(local_path, title=title)
            fixed_path = fix_result.get('output', '')

            if fix_result['status'] != 'fixed':
                print(f"  Heading fix: {fix_result['status']}")
                results.append({'name': item['name'], 'status': fix_result['status']})
                browser, p = close_feedback(browser, p)
                items_frame, browser, p = load_report_content(browser, p, course_id)
                continue

            print(f"  Added {fix_result['headings_found']} headings")

            # Upload fixed version
            new_score, remaining = upload_to_feedback(fb_page, fb_frame, fixed_path)

            if new_score:
                print(f"  NEW SCORE: {new_score}")
                if remaining:
                    print(f"  Remaining: {remaining}")
                results.append({'name': item['name'], 'old': item['score'], 'new': new_score, 'status': 'fixed'})
            else:
                print(f"  Upload failed/timed out")
                results.append({'name': item['name'], 'status': 'upload failed'})

            # Close feedback and refresh report
            browser, p = close_feedback(browser, p)
            items_frame, browser, p = load_report_content(browser, p, course_id)
            if not items_frame:
                print("  ERROR: Lost report connection")
                break

        if not items_frame:
            break

        # Re-scan current page after all items processed
        items, targets, fixable = scan_and_fix_page(items_frame, course_dir, args.item)

        if not targets:
            # All items on this page are >= 85%, try next page
            print(f"\nAll items on page {page_num} are above {SCORE_THRESHOLD}%")
            try:
                items_frame.locator('text="Next"').click(timeout=5000)
                time.sleep(3)
                page_num += 1
                items, targets, fixable = scan_and_fix_page(items_frame, course_dir, args.item)
                print(f"\nPage {page_num}: {len(items)} items, {len(targets)} below {SCORE_THRESHOLD}%, {len(fixable)} fixable\n")
                if not fixable:
                    if not targets:
                        print("No more items below threshold. Done!")
                    else:
                        print("No more fixable items.")
                    break
            except:
                print("No more pages.")
                break
        elif not fixable:
            print(f"\n{len(targets)} items below threshold but none fixable with headings.")
            break

    # Summary
    print(f"\n{'='*50}")
    print(f"  RESULTS")
    print(f"{'='*50}")
    for r in results:
        if r['status'] == 'fixed':
            print(f"  {r['name']:50s}  {r['old']} -> {r['new']}")
        else:
            print(f"  {r['name']:50s}  {r['status']}")

    browser.close()
    p.stop()
    print("\nDone!")
