"""Phase 5: Upload all fixed files back to Blackboard via accessibility report.

Strategy: Navigate to report Content tab, read items on page 1, for each item
below 85% check if we have a fixed file, upload it. After upload, reload report
(items re-sort). Repeat until all items on page 1 are >= 85% or no more fixes.

Uses the report as source of truth — no duplicate issues.

Requires: data/fix_manifest_{COURSE}.json from Phase 4.
Produces: data/upload_results_{COURSE}.json

Usage:
    python scripts/phase5_upload.py <course_key>
    python scripts/phase5_upload.py CYBERINFRA
"""
import sys, os, time, re
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect, load_json, save_json,
                      navigate_to_report_content, reload_report_content,
                      find_items_frame, find_feedback_page, find_feedback_frame,
                      close_feedback_windows, click_item_by_name,
                      get_page_items, fix_manifest_filename, COURSE_DIR)


def build_fixed_index(course_key):
    """Build an index mapping report names to fixed file paths.
    Deduplicates by keeping the first match."""
    course = get_course(course_key)
    course_dir = os.path.join(COURSE_DIR, course['dir'])

    index = {}  # report_name -> fixed_path
    for root, dirs, files in os.walk(course_dir):
        for fname in files:
            if '_fixed.' not in fname:
                continue
            fpath = os.path.join(root, fname)

            # Map back to possible report names
            # e.g. "IOS-review_fixed.pptx" -> "IOS-review.ppt" or "IOS-review.pptx"
            base = fname.replace('_fixed.', '.')
            stem = os.path.splitext(base)[0]
            fixed_ext = os.path.splitext(fname)[1]

            # Try exact match
            if base not in index:
                index[base] = fpath

            # Try with original extension (.ppt for .pptx, .doc for .docx)
            if fixed_ext == '.pptx':
                orig = stem + '.ppt'
                if orig not in index:
                    index[orig] = fpath
            elif fixed_ext == '.docx':
                orig = stem + '.doc'
                if orig not in index:
                    index[orig] = fpath

    return index


def get_report_page(browser):
    """Find the report page (the one with the LTI launch URL)."""
    for pg in browser.contexts[0].pages:
        if 'launchFrame' in pg.url or 'lti' in pg.url.lower():
            return pg
    # Fallback: first non-ally page
    for pg in browser.contexts[0].pages:
        if 'ally' not in pg.url:
            return pg
    return browser.contexts[0].pages[0]


def upload_item(item_name, fixed_path):
    """Click item, open feedback, upload file. Uses disconnect/reconnect.
    Returns 'uploaded', 'not found', 'error: ...'."""

    # Step 1: Connect, find report page, click item
    p, browser, page = connect()
    report_page = get_report_page(browser)
    items_frame = find_items_frame(report_page)
    if not items_frame:
        disconnect(p, browser)
        return 'error: items frame not found'

    clicked = click_item_by_name(items_frame, item_name)
    if not clicked:
        disconnect(p, browser)
        return 'not found'

    # Disconnect — let Chrome open the feedback window freely
    disconnect(p, browser)
    time.sleep(5)

    # Step 2: Reconnect, find feedback, upload file
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        disconnect(p, browser)
        return 'error: feedback window not found'

    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        fb_page.close()
        disconnect(p, browser)
        return 'error: no file input found'

    file_input.set_input_files(os.path.abspath(fixed_path))

    # Disconnect completely — let Chrome upload without any interference
    disconnect(p, browser)

    # Wait for upload to complete — no reconnection during this time
    # Use generous fixed wait based on file size
    file_size = os.path.getsize(fixed_path)
    if file_size < 500_000:
        wait = 15
    elif file_size < 2_000_000:
        wait = 25
    else:
        wait = 40
    time.sleep(wait)

    # Reconnect only to close feedback window
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if fb_page:
        fb_page.close()
    disconnect(p, browser)

    return 'uploaded'


def upload_all(course_key):
    """Upload all fixed files by iterating through report items."""
    course = get_course(course_key)
    course_id = course['id']

    # Build index of fixed files
    fixed_index = build_fixed_index(course_key)
    print(f"Phase 5: Uploading for {course_key}")
    print(f"Fixed files available: {len(fixed_index)}")

    # Navigate to report content tab
    print("Navigating to report...")
    navigate_to_report_content(course_id)

    results = []
    uploaded = 0
    skipped = set()

    while True:
        # Read items on current page (use report page, not last tab)
        p, browser, page = connect()
        report_page = get_report_page(browser)
        items_frame = find_items_frame(report_page)
        if not items_frame:
            print("  ERROR: Could not find items frame")
            disconnect(p, browser)
            break

        items = get_page_items(items_frame)
        disconnect(p, browser)

        if not items:
            print("  No items found on page")
            break

        # Find first item below 85% that we have a fix for and haven't skipped
        target = None
        for item in items:
            score_str = item['score'].replace('%', '')
            if score_str.isdigit() and int(score_str) >= 85:
                continue
            if item['name'] in skipped:
                continue

            # Check if we have a fixed file
            name = item['name']
            fixed_path = fixed_index.get(name)

            # Try without (N) suffix
            if not fixed_path:
                clean = re.sub(r'\(\d+\)(?=\.\w+$)', '', name).strip()
                fixed_path = fixed_index.get(clean)

            if fixed_path and os.path.exists(fixed_path):
                target = (name, item['score'], fixed_path)
                break
            else:
                skipped.add(name)

        if not target:
            # Check if all items are >= 85% or skipped
            below = [i for i in items
                     if i['score'].replace('%', '').isdigit()
                     and int(i['score'].replace('%', '')) < 85
                     and i['name'] not in skipped]
            if not below:
                print("\nAll items on page are >= 85% or skipped — done!")
            else:
                print(f"\n{len(below)} items below 85% but no fixes available")
            break

        name, score, fixed_path = target
        size = os.path.getsize(fixed_path)
        print(f"\n  {name} ({score}) -> {os.path.basename(fixed_path)} ({size:,} bytes)")

        # Close any leftover feedback windows and upload
        close_feedback_windows()
        status = upload_item(name, fixed_path)
        print(f"    -> {status}")

        if 'uploaded' in status:
            uploaded += 1
            results.append({'report_name': name, 'status': status})
        elif status == 'not found':
            skipped.add(name)
            results.append({'report_name': name, 'status': 'not found'})
        else:
            skipped.add(name)
            results.append({'report_name': name, 'status': status})

        # Reload report
        close_feedback_windows()
        reload_report_content(reload_wait=5, tab_wait=5)

    return {
        'course': course_key,
        'uploaded': uploaded,
        'skipped': sorted(skipped),
        'results': results,
    }


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python phase5_upload.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)

    course_key = sys.argv[1].upper()
    results = upload_all(course_key)

    filename = f"upload_results_{course_key}.json"
    save_json(results, filename)
    print(f"\nSaved to data/{filename}")

    print(f"\n{'='*60}")
    print(f"  Phase 5 Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Uploaded: {results['uploaded']}")
    print(f"  Skipped:  {len(results['skipped'])}")

    if results['skipped']:
        print(f"\n  Skipped items (no fix available):")
        for s in results['skipped'][:20]:
            print(f"    - {s}")


if __name__ == '__main__':
    main()
