"""Version 2 workflow, step 1+2: download every report item below 85%.

Iterates the accessibility report Content tab and uses
download_only_from_feedback (from phase5_upload) to save each flagged item
into course_content/<COURSE>/_downloads/. Uses a sticky page pointer so
after each download + reload, the script jumps directly back to the page
it was working on instead of re-scanning earlier pages.

Usage:
    python scripts/v2_collect.py <course_key>
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect,
                      navigate_to_report_content, reload_report_content,
                      find_items_frame, get_page_items, click_next_page,
                      close_feedback_windows, DATA_DIR)
from phase5_upload import download_only_from_feedback, get_report_page


def goto_page(items_frame, target_page):
    """Advance the current items frame from page 1 to target_page by clicking Next."""
    for _ in range(target_page - 1):
        if not click_next_page(items_frame):
            return False
        time.sleep(1)
    return True


def collect_all(course_key):
    course = get_course(course_key)
    course_id = course['id']

    # Navigate to report Content tab (resets to page 1 at end).
    p, browser, page = connect()
    report_page = get_report_page(browser)
    disconnect(p, browser)
    if report_page:
        reload_report_content(reload_wait=10, tab_wait=5)
    else:
        navigate_to_report_content(course_id, nav_wait=10, tab_wait=5)

    collected = []
    attempted = set()  # report_name values already tried this run
    current_page = 1

    while True:
        # Chrome already displays current_page (we either just loaded page 1 above,
        # or we advanced via click_next_page below). Downloads don't change item
        # order, so we don't reload between them. Just re-read the current page.
        p, browser, page = connect()
        report_page = get_report_page(browser)
        items_frame = find_items_frame(report_page) if report_page else None
        if not items_frame:
            print("ERROR: items frame not found", flush=True)
            disconnect(p, browser)
            break
        items = get_page_items(items_frame)
        disconnect(p, browser)

        if not items:
            print(f"Page {current_page} has no items; stopping.", flush=True)
            break

        # Find next item: below 85%, not in attempted, has a usable extension.
        target = None
        reached_threshold = False
        for item in items:
            if item['name'] in attempted:
                continue
            score_str = item['score'].replace('%', '')
            if score_str.isdigit() and int(score_str) >= 85:
                reached_threshold = True
                break
            ext = os.path.splitext(item['name'])[1].lower()
            if item.get('type', '') == 'Ultra document' or not ext:
                attempted.add(item['name'])
                continue
            target = item
            break

        if reached_threshold:
            print(f"\nPage {current_page}: reached >= 85% item; done.", flush=True)
            break

        if not target:
            # Every item on this page already processed or not eligible; advance to next page.
            p, browser, page = connect()
            report_page = get_report_page(browser)
            items_frame = find_items_frame(report_page) if report_page else None
            advanced = items_frame and click_next_page(items_frame)
            disconnect(p, browser)
            if not advanced:
                print(f"\nPage {current_page}: no next page; stopping.", flush=True)
                break
            current_page += 1
            print(f"\nAdvanced to page {current_page}.", flush=True)
            time.sleep(1)
            continue

        name = target['name']
        score = target['score']
        print(f"\n[page {current_page}] {name} ({score}) -> downloading...", flush=True)

        close_feedback_windows()
        downloaded_path = download_only_from_feedback(name, course_key)
        attempted.add(name)

        entry = {
            'report_name': name,
            'score': score,
            'page_number': current_page,
            'downloaded_path': downloaded_path.replace('\\', '/') if downloaded_path else None,
            'error': None if downloaded_path else 'download failed',
        }
        collected.append(entry)

        # Persist progress after every attempt so re-runs can resume manually.
        out_path = os.path.join(DATA_DIR, f'v2_collected_{course_key}.json')
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(collected, f, indent=2)

        # Downloads do not change scores, so the item order stays the same.
        # Just close the feedback window; no need to reload the report between downloads.
        close_feedback_windows()
        time.sleep(1)

    out_path = os.path.join(DATA_DIR, f'v2_collected_{course_key}.json')
    print(f"\n{'='*60}")
    print(f"  v2 Collect Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Items attempted:   {len(collected)}")
    print(f"  Downloaded OK:     {sum(1 for e in collected if e['downloaded_path'])}")
    print(f"  Download failed:   {sum(1 for e in collected if not e['downloaded_path'])}")
    print(f"  Saved list:        {out_path}")
    return collected


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python v2_collect.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)
    collect_all(sys.argv[1].upper())


if __name__ == '__main__':
    main()
