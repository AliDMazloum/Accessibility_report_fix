"""Fix and upload accessibility files directly from the Blackboard report.

Workflow per item:
1. Click item in report Content tab (opens feedback in new window)
2. Read current score and issues
3. Download original file via "Download original" button
4. Fix the PDF (add tags, language, title as needed)
5. Upload the fixed version
6. Wait for new score
7. Close feedback window

Usage:
    python fix_and_upload.py ITEC493              # Process all items < 85%
    python fix_and_upload.py ITEC493 --item "chapter1.pdf"  # Process single item
    python fix_and_upload.py ITEC493 --dry-run    # Just list items, don't fix
"""
import sys, os, time, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import (connect, disconnect, dismiss_popup, navigate_to_report,
                      save_json, DATA_DIR, COURSE_DIR)
from fix_pdf import fix_pdf

SCORE_THRESHOLD = 85
MAX_FILE_SIZE_MB = 5
MAX_PAGES = 100

COURSES = {
    "ITEC493": {"id": "_1308255_1", "dir": "ITEC493-001-FALL-2025"},
    "ITEC445": {"id": "_1328539_1", "dir": "ITEC445-001-SPRING-2026"},
    "ITEC552": {"id": "_1308261_1", "dir": "ITEC552-001-FALL-2025"},
    "CYBERINFRA": {"id": "_1308272_1", "dir": "CYBERINFRA-FALL-2025"},
}


def open_report_content(page, course_id):
    """Navigate to report and click Content tab. Returns items_frame or None."""
    navigate_to_report(page, course_id)
    time.sleep(10)
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
    # Wait for Content tab items to load (can be slow)
    for attempt in range(12):
        time.sleep(5)
        for f in page.frames:
            try:
                count = f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length')
                if count > 0:
                    return f
            except:
                pass
    return None


def get_visible_items(items_frame):
    """Get all items visible on the current report page."""
    return items_frame.evaluate("""() => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        const data = [];
        rows.forEach(row => {
            const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
            const typeEl = row.querySelector('.ir-content-list-item-name-text-type');
            const issuesEl = row.querySelector('.ir-content-list-item-issues span');
            const scoreEl = row.querySelector('.feedback-score-indicator span');
            if (nameEl) {
                data.push({
                    name: nameEl.innerText.trim(),
                    type: typeEl ? typeEl.innerText.trim() : '',
                    issues: issuesEl ? issuesEl.innerText.trim() : '0',
                    score: scoreEl ? scoreEl.innerText.trim() : ''
                });
            }
        });
        return data;
    }""")


def click_item_by_name(items_frame, name, browser):
    """Click a report item by name. Returns the feedback page or None."""
    # Close any existing feedback windows first
    for pg in list(browser.contexts[0].pages):
        if 'ally.ac' in pg.url and 'launchinstructorfeedback' in pg.url:
            pg.close()
            time.sleep(0.5)

    pages_before = len(browser.contexts[0].pages)

    # Use Playwright's native click on the item name text
    try:
        items_frame.click(f'text="{name}"', timeout=5000)
    except:
        # Fallback to JS click
        items_frame.evaluate("""(targetName) => {
            const rows = document.querySelectorAll('tr.ir-list-item');
            for (const row of rows) {
                const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
                if (nameEl && nameEl.innerText.trim() === targetName) {
                    const btn = row.querySelector('button');
                    if (btn) btn.click();
                    return;
                }
            }
        }""", name)

    # Wait for new window — skip if it takes more than 90 seconds
    for _ in range(90):
        time.sleep(1)
        if len(browser.contexts[0].pages) > pages_before:
            break
    time.sleep(5)

    # Find the feedback page
    for pg in browser.contexts[0].pages:
        if 'ally.ac' in pg.url and 'launchinstructorfeedback' in pg.url:
            return pg
    return None


def get_feedback_frame(fb_page):
    """Find the frame in the feedback page that has the score/upload area."""
    for f in fb_page.frames:
        try:
            text = f.evaluate('() => document.body.innerText')
            if 'Accessibility score' in text or 'Browse' in text:
                return f
        except:
            pass
    return None


def get_feedback_info(fb_frame):
    """Extract score and issues from the feedback frame."""
    text = fb_frame.evaluate('() => document.body.innerText')
    info = {'raw_text': text[:2000]}

    # Extract score
    for line in text.split('\n'):
        line = line.strip()
        if line.endswith('%') and len(line) < 5:
            info['score'] = line
        elif 'Accessibility score' in line:
            info['score_line'] = line

    # Extract issues
    issues = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('This PDF') or line.startswith('This document'):
            issues.append(line)
    info['issues'] = issues

    return info


def download_original(fb_page, fb_frame, download_dir):
    """Click 'Download original' and wait for the file. Returns filepath or None."""
    os.makedirs(download_dir, exist_ok=True)

    # Set download behavior via CDP
    cdp = fb_page.context.new_cdp_session(fb_page)
    cdp.send("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": os.path.abspath(download_dir).replace("/", os.sep),
    })

    # Get files before download
    files_before = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()

    # Click download button
    fb_frame.evaluate("""() => {
        const els = document.querySelectorAll('a, button, span');
        for (const el of els) {
            const text = el.innerText.trim();
            const label = el.getAttribute('aria-label') || '';
            if (text === 'Download original' || text === 'get_app' ||
                label.includes('Download original')) {
                el.click();
                return true;
            }
        }
        // Try icon button near download text
        const icons = document.querySelectorAll('mat-icon, .material-icons');
        for (const icon of icons) {
            if (icon.innerText.trim() === 'get_app') {
                icon.click();
                return true;
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
            # Filter out .crdownload temp files
            completed = [f for f in new_files if not f.endswith('.crdownload')]
            if completed:
                return os.path.join(download_dir, completed[0])

    return None


def upload_fixed(fb_page, fixed_path):
    """Upload a fixed file and wait for the new score. Returns new score or None."""
    # Find file input
    for f in fb_page.frames:
        inp = f.query_selector('input[type=file]')
        if inp:
            inp.set_input_files(os.path.abspath(fixed_path))
            break
    else:
        return None

    # Wait for verification to complete
    for attempt in range(15):
        time.sleep(5)
        fb_frame = get_feedback_frame(fb_page)
        if fb_frame:
            try:
                text = fb_frame.evaluate('() => document.body.innerText')
                if 'Verifying' not in text and '_fixed' in text:
                    info = get_feedback_info(fb_frame)
                    return info
            except:
                pass
    return None


def process_item(name, file_type, items_frame, browser, download_dir):
    """Process a single report item: download, fix, upload. Returns result dict."""
    result = {'name': name, 'type': file_type}

    # Click item to open feedback
    fb_page = click_item_by_name(items_frame, name, browser)
    if not fb_page:
        result['status'] = 'feedback not opened'
        return result

    fb_frame = get_feedback_frame(fb_page)
    if not fb_frame:
        fb_page.close()
        time.sleep(0.5)
        result['status'] = 'no feedback frame'
        return result

    # Get current info
    info = get_feedback_info(fb_frame)
    result['original_score'] = info.get('score', '?')
    result['issues'] = info.get('issues', [])
    print(f"  Score: {result['original_score']}, Issues: {result['issues']}")

    # Only fix PDFs for now
    if not name.lower().endswith('.pdf'):
        print(f"  Skipping non-PDF: {name}")
        fb_page.close()
        time.sleep(0.5)
        result['status'] = 'skipped (not PDF)'
        return result

    # Click "Show all issues" to get the full list from the report
    try:
        fb_frame.evaluate("""() => {
            const toggle = document.querySelector('.ally-if-toggle-all-issues');
            if (toggle) toggle.click();
        }""")
        time.sleep(1)
        # Re-read issues after expanding
        info = get_feedback_info(fb_frame)
        result['issues'] = info.get('issues', result['issues'])
    except:
        pass

    # Check if the report lists fixable issues
    fixable = any('untagged' in i.lower() or 'language' in i.lower() or 'title' in i.lower()
                  for i in result['issues'])
    if not fixable:
        print(f"  No programmatically fixable issues (per report)")
        fb_page.close()
        time.sleep(0.5)
        result['status'] = 'no fixable issues'
        return result

    # Download original
    print(f"  Downloading original...")
    orig_path = download_original(fb_page, fb_frame, download_dir)
    if not orig_path:
        print(f"  Download failed")
        fb_page.close()
        time.sleep(0.5)
        result['status'] = 'download failed'
        return result
    file_size = os.path.getsize(orig_path)
    print(f"  Downloaded: {os.path.basename(orig_path)} ({file_size:,} bytes)")

    # Skip large files
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        print(f"  Skipping: file too large ({file_size / 1024 / 1024:.1f} MB > {MAX_FILE_SIZE_MB} MB)")
        fb_page.close()
        time.sleep(0.5)
        result['status'] = 'skipped (too large)'
        return result

    # Check page count
    try:
        import pikepdf
        with pikepdf.open(orig_path) as pdf_check:
            page_count = len(pdf_check.pages)
        if page_count > MAX_PAGES:
            print(f"  Skipping: too many pages ({page_count} > {MAX_PAGES})")
            fb_page.close()
            time.sleep(0.5)
            result['status'] = f'skipped ({page_count} pages)'
            return result
    except:
        pass

    # Fix the PDF
    title = os.path.splitext(os.path.basename(orig_path))[0].replace('_', ' ')
    fix_result = fix_pdf(orig_path, title=title)
    if fix_result.get('error') or fix_result.get('status') == 'no issues found':
        print(f"  Fix result: {fix_result.get('status', fix_result.get('error'))}")
        fb_page.close()
        time.sleep(0.5)
        result['status'] = 'nothing to fix'
        return result

    fixed_path = fix_result['output']
    print(f"  Fixed: {', '.join(fix_result['fixed'])}")

    # Upload fixed version
    print(f"  Uploading fixed version...")
    upload_result = upload_fixed(fb_page, fixed_path)
    if upload_result:
        result['new_score'] = upload_result.get('score', '?')
        result['remaining_issues'] = upload_result.get('issues', [])
        result['status'] = 'fixed'
        print(f"  New score: {result['new_score']}")
        if result['remaining_issues']:
            print(f"  Remaining: {result['remaining_issues']}")
    else:
        result['status'] = 'upload timeout'
        print(f"  Upload verification timed out")

    # Close feedback window
    fb_page.close()
    time.sleep(0.5)

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fix and upload accessibility files from report')
    parser.add_argument('course', help='Course key (e.g., ITEC493)')
    parser.add_argument('--item', help='Process single item by name')
    parser.add_argument('--dry-run', action='store_true', help='List items without fixing')
    args = parser.parse_args()

    course_key = args.course.upper()
    if course_key not in COURSES:
        print(f"Unknown course '{course_key}'. Known: {list(COURSES.keys())}")
        sys.exit(1)

    course_id = COURSES[course_key]['id']
    course_dir = COURSES[course_key]['dir']
    download_dir = os.path.join(COURSE_DIR, course_dir, '_downloads')

    p, browser, page = connect()
    print(f"Connected. URL: {page.url}")

    # Open report Content tab
    print(f"Opening accessibility report for {course_key}...")
    items_frame = open_report_content(page, course_id)
    if not items_frame:
        print("ERROR: Could not find report items")
        disconnect(p, browser)
        sys.exit(1)

    # Get all visible items
    items = get_visible_items(items_frame)
    print(f"\nReport has {len(items)} items on this page")

    # Filter to items below threshold
    targets = []
    for item in items:
        score = int(item['score'].replace('%', ''))
        if score < SCORE_THRESHOLD:
            targets.append(item)

    print(f"Items below {SCORE_THRESHOLD}%: {len(targets)}\n")

    if args.dry_run:
        for item in targets:
            print(f"  {item['score']:>4s}  [{item['type']}]  {item['name']}")
        disconnect(p, browser)
        sys.exit(0)

    # Process items
    results = []
    if args.item:
        # Single item mode
        target = next((t for t in targets if t['name'] == args.item), None)
        if not target:
            # Check all items, not just targets
            target = next((i for i in items if i['name'] == args.item), None)
        if not target:
            print(f"Item '{args.item}' not found in report")
            disconnect(p, browser)
            sys.exit(1)
        print(f"[1/1] {target['name']} ({target['score']})")
        result = process_item(target['name'], target['type'], items_frame, browser, download_dir)
        results.append(result)
    else:
        # Process all targets
        for i, target in enumerate(targets):
            print(f"\n[{i+1}/{len(targets)}] {target['name']} ({target['score']})")
            result = process_item(target['name'], target['type'], items_frame, browser, download_dir)
            results.append(result)

    # Summary
    print(f"\n{'='*50}")
    print(f"  RESULTS")
    print(f"{'='*50}")
    fixed = [r for r in results if r['status'] == 'fixed']
    skipped = [r for r in results if 'skip' in r['status'] or 'no fix' in r['status']]
    failed = [r for r in results if r['status'] not in ('fixed',) and 'skip' not in r['status'] and 'no fix' not in r['status']]

    if fixed:
        print(f"\n  Fixed ({len(fixed)}):")
        for r in fixed:
            print(f"    {r['name']}: {r.get('original_score','?')} -> {r.get('new_score','?')}")
    if skipped:
        print(f"\n  Skipped ({len(skipped)}):")
        for r in skipped:
            print(f"    {r['name']}: {r['status']}")
    if failed:
        print(f"\n  Failed ({len(failed)}):")
        for r in failed:
            print(f"    {r['name']}: {r['status']}")

    disconnect(p, browser)
    print("\nDone!")
