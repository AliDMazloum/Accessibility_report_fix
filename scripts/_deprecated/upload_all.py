"""Upload all fixed files for a course via the accessibility report.

Reloads report and re-clicks Content tab between each upload.
Handles pagination to find items across multiple pages.

Usage:
    python scripts/upload_all.py <course>
    python scripts/upload_all.py CYBERINFRA
"""
import sys, os, time, json, re

sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import (connect, disconnect, dismiss_popup, navigate_to_report,
                      get_report_items, DATA_DIR, COURSE_DIR)

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


def find_report_frame(page):
    for f in page.frames:
        try:
            if f.evaluate('() => document.body.innerText.includes("Course accessibility")'):
                return f
        except:
            pass
    return None


def find_items_frame(page):
    for f in page.frames:
        try:
            count = f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length')
            if count > 0:
                return f
        except:
            pass
    return None


def find_feedback_page(browser):
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            return pg
    return None


def find_feedback_frame(fb_page):
    for f in fb_page.frames:
        try:
            if f.evaluate('() => !!document.querySelector("input[type=file]")'):
                return f
        except:
            pass
    return fb_page.frames[-1] if len(fb_page.frames) > 1 else fb_page


def close_feedback_windows():
    p, browser, page = connect()
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            pg.close()
    disconnect(p, browser)


def navigate_to_report_content(course_id):
    """Navigate to report from scratch and click Content tab. Uses disconnect/reconnect."""
    p, browser, page = connect()
    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline/lti/launchFrame?toolHref=https:~2F~2Fblackboard.sc.edu~2Fwebapps~2Fblackboard~2Fexecute~2Fblti~2FlaunchPlacement%3Fblti_placement_id%3D_393_1%26course_id%3D{course_id}%26from_ultra%3Dtrue&toolTitle=Accessibility%20Report"
    try:
        page.goto(url, wait_until="commit", timeout=15000)
    except Exception:
        pass
    disconnect(p, browser)
    print("  Navigating to report...")
    time.sleep(10)

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
    time.sleep(5)


def reload_report_content():
    """Reload the current report page and click Content tab. Uses disconnect/reconnect."""
    p, browser, page = connect()
    page.reload()
    disconnect(p, browser)
    print("  Reloading report...")
    time.sleep(5)

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
    time.sleep(5)


def click_item_on_current_page(item_name):
    """Find and click an item on the current report page. Returns True if found."""
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        disconnect(p, browser)
        return False

    found = items_frame.evaluate("""(name) => {
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

    disconnect(p, browser)
    return found


def upload_one(item_name, fixed_path):
    """Upload a single fixed file. Returns new score or None."""
    print(f"\n  --- {item_name} ---")
    print(f"  File: {os.path.basename(fixed_path)} ({os.path.getsize(fixed_path):,} bytes)")

    close_feedback_windows()

    # Click the item (search across pages)
    if not click_item_on_current_page(item_name):
        print(f"  SKIP: Item not found in report")
        return None

    # Disconnect to let feedback load
    print("  Waiting for feedback window...")
    time.sleep(15)

    # Find feedback and upload
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        print("  ERROR: Feedback window not found")
        disconnect(p, browser)
        return None

    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        print("  ERROR: No file input found")
        fb_page.close()
        disconnect(p, browser)
        return None

    file_input.set_input_files(os.path.abspath(fixed_path))
    print("  Uploaded.")

    # Close feedback immediately — score will be visible after report reload
    time.sleep(3)  # Brief wait for upload to register
    fb_page.close()
    disconnect(p, browser)

    return "uploaded"


def find_fixed_files(course_dir, report_items):
    """Map report item names to their fixed file paths."""
    # Collect all fixed files
    fixed = {}
    for root, dirs, files in os.walk(course_dir):
        for fname in files:
            if '_fixed.' in fname:
                fixed[fname] = os.path.join(root, fname)

    # Map report names to fixed files
    mapping = {}
    for item in report_items:
        name = item['name']
        score_str = item.get('score', '').replace('%', '')
        if not score_str.isdigit() or int(score_str) >= 85:
            continue

        stem = os.path.splitext(name)[0]
        ext = os.path.splitext(name)[1].lower()

        # Try direct match: name -> stem_fixed.ext
        direct = stem + '_fixed' + ext
        if direct in fixed:
            mapping[name] = fixed[direct]
            continue

        # Try converted format: .ppt -> _fixed.pptx, .doc -> _fixed.docx
        if ext == '.ppt':
            converted = stem + '_fixed.pptx'
            if converted in fixed:
                mapping[name] = fixed[converted]
                continue
        elif ext == '.doc':
            converted = stem + '_fixed.docx'
            if converted in fixed:
                mapping[name] = fixed[converted]
                continue

        # Try matching by stem (for files with _fixed already in name)
        for fname, fpath in fixed.items():
            if stem in fname:
                mapping[name] = fpath
                break

    return mapping


def get_page_items():
    """Get all items on the current report page. Returns list of {name, score}."""
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        disconnect(p, browser)
        return []

    items = items_frame.evaluate("""() => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        const data = [];
        rows.forEach(row => {
            const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
            const scoreEl = row.querySelector('.feedback-score-indicator span');
            if (nameEl) data.push({
                name: nameEl.innerText.trim(),
                score: scoreEl ? scoreEl.innerText.trim() : '?'
            });
        });
        return data;
    }""")
    disconnect(p, browser)
    return items


def click_item_by_name(item_name):
    """Click a specific item by name on the current page. Returns True if found."""
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        disconnect(p, browser)
        return False

    found = items_frame.evaluate("""(name) => {
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
    disconnect(p, browser)
    return found


def upload_all(course_key):
    """Upload all fixed files for a course.

    Strategy: always pick the first item on page 1 (lowest score),
    check if we have a fixed file for it, upload, reload, repeat.
    Stop when the first item is >= 85% or we have no fix for it.
    """
    info = COURSES[course_key]
    course_dir = os.path.join(COURSE_DIR, info['dir'])

    # Build index of all fixed files by stem
    fixed_index = {}  # stem -> path
    for root, dirs, files in os.walk(course_dir):
        for fname in files:
            if '_fixed.' in fname:
                stem = fname.replace('_fixed.', '.').replace('.pptx', '').replace('.docx', '').replace('.pdf', '')
                fixed_index[stem] = os.path.join(root, fname)

    print(f"Fixed files available: {len(fixed_index)}")

    # Navigate to report
    print("\nLoading accessibility report...")
    navigate_to_report_content(info['id'])

    uploaded = 0
    skipped = []

    import re

    while True:
        # Get all items on current page
        items = get_page_items()
        if not items:
            print("No items found on page.")
            break

        # Find first item that's below 85% and not already skipped
        target = None
        for item in items:
            score_str = item['score'].replace('%', '')
            if score_str.isdigit() and int(score_str) >= 85:
                continue  # Above threshold
            if item['name'] in skipped:
                continue  # Already tried and failed
            target = item
            break

        if not target:
            # All items on page are either >= 85% or skipped
            print(f"\nAll items on page 1 are either >= 85% or skipped — done!")
            break

        name = target['name']
        print(f"\n  --- {name} ({target['score']}) ---")

        # Find fixed file for this item
        stem = os.path.splitext(name)[0]
        fixed_path = None

        # Try exact stem match
        if stem in fixed_index:
            fixed_path = fixed_index[stem]
        else:
            # Try without (N) suffixes
            clean_stem = re.sub(r'\(\d+\)$', '', stem).strip()
            if clean_stem in fixed_index:
                fixed_path = fixed_index[clean_stem]

        # Click the target item to open feedback
        close_feedback_windows()
        if not click_item_by_name(name):
            print("  ERROR: Could not click item")
            skipped.append(name)
            continue

        if not fixed_path:
            # No fixed file — try to download from feedback window, fix, then upload
            print(f"  No fixed file — downloading from feedback...")
            time.sleep(20)  # Longer wait since this item wasn't downloaded before

            p, browser, page = connect()
            fb_page = find_feedback_page(browser)
            if not fb_page:
                print("  ERROR: Feedback window not found for download")
                disconnect(p, browser)
                skipped.append(name)
                reload_report_content()
                continue

            # Set download dir
            download_dir = os.path.join(course_dir, '_downloads')
            os.makedirs(download_dir, exist_ok=True)
            try:
                cdp_session = fb_page.context.new_cdp_session(fb_page)
                cdp_session.send('Browser.setDownloadBehavior', {
                    'behavior': 'allow',
                    'downloadPath': os.path.abspath(download_dir).replace('/', os.sep)
                })
            except:
                pass

            # Click download button
            fb_frame = find_feedback_frame(fb_page)
            try:
                fb_frame.evaluate("""() => {
                    const links = document.querySelectorAll('a, button');
                    for (const el of links) {
                        const text = el.innerText.trim().toLowerCase();
                        if (text.includes('download original')) { el.click(); return true; }
                    }
                    const icons = document.querySelectorAll('[class*="get_app"], [aria-label*="download"]');
                    for (const el of icons) { el.click(); return true; }
                    return false;
                }""")
            except:
                pass

            # Wait for download (longer timeout)
            existing = set(os.listdir(download_dir))
            downloaded_path = None
            for _ in range(45):
                time.sleep(1)
                current = set(os.listdir(download_dir))
                new_files = {f for f in (current - existing)
                            if not f.endswith('.crdownload') and not f.endswith('.tmp')}
                if new_files:
                    downloaded_path = os.path.join(download_dir, new_files.pop())
                    break

            fb_page.close()
            disconnect(p, browser)

            if not downloaded_path:
                print("  Download failed — skipping")
                skipped.append(name)
                reload_report_content()
                continue

            print(f"  Downloaded: {os.path.basename(downloaded_path)} ({os.path.getsize(downloaded_path):,} bytes)")

            # Fix the file
            from process_item import fix_file
            fixed_path = fix_file(downloaded_path, download_dir)
            if not fixed_path:
                print("  Fix failed — skipping")
                skipped.append(name)
                reload_report_content()
                continue

            print(f"  Fixed: {os.path.basename(fixed_path)}")
            # Add to index for future
            fix_stem = os.path.splitext(name)[0]
            fixed_index[fix_stem] = fixed_path

            # Re-click the item to upload (need to reload report first)
            reload_report_content()
            close_feedback_windows()
            if not click_item_by_name(name):
                print("  ERROR: Could not re-click item for upload")
                skipped.append(name)
                continue
            time.sleep(15)
        else:
            print(f"  File: {os.path.basename(fixed_path)} ({os.path.getsize(fixed_path):,} bytes)")
            # Wait for feedback
            print("  Waiting for feedback...")
            time.sleep(15)

        # Upload
        p, browser, page = connect()
        fb_page = find_feedback_page(browser)
        if not fb_page:
            print("  ERROR: Feedback window not found")
            disconnect(p, browser)
            skipped.append(name)
            reload_report_content()
            continue

        fb_frame = find_feedback_frame(fb_page)
        file_input = fb_frame.query_selector('input[type="file"]')
        if not file_input:
            file_input = fb_page.query_selector('input[type="file"]')
        if not file_input:
            print("  ERROR: No file input found")
            fb_page.close()
            disconnect(p, browser)
            skipped.append(name)
            reload_report_content()
            continue

        file_input.set_input_files(os.path.abspath(fixed_path))
        print("  Uploading...")
        time.sleep(10)
        fb_page.close()
        disconnect(p, browser)
        uploaded += 1

        # Reload report
        close_feedback_windows()
        reload_report_content()

    print(f"\n{'='*60}")
    print(f"Upload Summary for {course_key}")
    print(f"  Uploaded: {uploaded}")
    print(f"  Skipped (no fix): {len(skipped)}")
    for s in skipped:
        print(f"    - {s}")
    print(f"{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python upload_all.py <course>")
        print(f"Known courses: {', '.join(COURSES.keys())}")
        sys.exit(1)

    course = sys.argv[1].upper()
    if course not in COURSES:
        print(f"Unknown course: {course}")
        sys.exit(1)

    upload_all(course)
