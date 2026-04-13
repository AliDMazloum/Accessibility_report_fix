"""Process all items below 85% from the accessibility report.

Iterates through items on the current page, processes each one (download → fix → upload),
refreshes the report after each upload, and moves to next page when all items >= 85%.

Skips .doc and .ppt files if they fail to load (known Blackboard issue).

Usage:
    python scripts/process_all.py <course>
    python scripts/process_all.py CYBERINFRA
    python scripts/process_all.py CYBERINFRA --dry-run
    python scripts/process_all.py CYBERINFRA --skip-old-formats
"""
import sys, os, time

sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, get_report_items
from process_item import (process_item, get_course_info, find_items_frame,
                          find_feedback_page, COURSES)
from load_report import load_report_content, find_items_frame, find_report_frame, print_items

SKIP_EXTENSIONS = set()  # populated by --skip-old-formats


def close_feedback_windows():
    """Close any open feedback windows."""
    p, browser, page = connect()
    closed = 0
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            pg.close()
            closed += 1
    disconnect(p, browser)
    if closed:
        print(f"  Closed {closed} feedback window(s)")


def refresh_report():
    """Refresh the current report page and wait for reload.
    Uses disconnect/reconnect pattern."""
    p, browser, page = connect()
    page.reload()
    disconnect(p, browser)
    print("  Refreshing report, waiting for reload...")
    time.sleep(15)


def get_current_items():
    """Get items currently visible on the report page."""
    p, browser, page = connect()

    # Click Content tab (in case refresh reset it)
    report_frame = find_report_frame(page)
    if report_frame:
        try:
            report_frame.evaluate("""() => {
                for (const t of document.querySelectorAll('a, button')) {
                    if (t.innerText.trim() === 'Content') { t.click(); return true; }
                }
                return false;
            }""")
        except:
            pass
    disconnect(p, browser)
    time.sleep(5)

    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        disconnect(p, browser)
        return []
    items = get_report_items(items_frame)
    disconnect(p, browser)
    return items


def go_to_next_page():
    """Click 'Next' on the report pagination. Returns True if successful."""
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        disconnect(p, browser)
        return False

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

    if clicked:
        time.sleep(5)
    return clicked


def should_skip(item):
    """Check if an item should be skipped based on extension or score."""
    name = item['name']
    score_str = item.get('score', '').replace('%', '')
    ext = os.path.splitext(name)[1].lower()

    # Already above 85%
    if score_str.isdigit() and int(score_str) >= 85:
        return True, "score >= 85%"

    # Skip old formats if flag is set
    if ext in SKIP_EXTENSIONS:
        return True, f"skipping {ext} (old format)"

    return False, ""


def process_all(course_arg, dry_run=False):
    """Main loop: process all items below 85%."""
    course_id, course_folder = get_course_info(course_arg)

    page_num = 1
    total_processed = 0
    total_skipped = 0
    total_failed = 0

    while True:
        print(f"\n{'='*60}")
        print(f"Page {page_num}")
        print(f"{'='*60}")

        items = get_current_items()
        if not items:
            print("No items found. Done or report not loaded.")
            break

        print(f"Found {len(items)} items on this page:")
        for item in items:
            print(f"  {item.get('score', '?'):>5}  {item['name']}")

        # Check if all items on page are >= 85%
        all_above = True
        for item in items:
            score_str = item.get('score', '').replace('%', '')
            if score_str.isdigit() and int(score_str) < 85:
                all_above = False
                break

        if all_above:
            print(f"\nAll items on page {page_num} are >= 85%.")
            if go_to_next_page():
                page_num += 1
                continue
            else:
                print("No more pages. Done!")
                break

        # Process items below 85%
        for item in items:
            name = item['name']
            skip, reason = should_skip(item)
            if skip:
                if "score" not in reason:  # Don't log score skips, too noisy
                    print(f"\n  Skipping: {name} ({reason})")
                    total_skipped += 1
                continue

            print(f"\n--- Processing: {name} ({item.get('score', '?')}) ---")

            if dry_run:
                print("  [DRY RUN] Would process this item")
                total_processed += 1
                continue

            # Close any leftover feedback windows
            close_feedback_windows()

            # Process the item
            success = process_item(course_arg, name)

            if success:
                total_processed += 1
                print(f"  Successfully processed: {name}")

                # Close feedback and refresh report
                close_feedback_windows()
                refresh_report()

                # Re-read items after refresh (report re-sorts by score)
                break  # Break inner loop, re-read items from the refreshed page
            else:
                total_failed += 1
                print(f"  Failed to process: {name}")

                # Close any leftover feedback windows
                close_feedback_windows()

                # If it's an old format that failed, add to skip list
                ext = os.path.splitext(name)[1].lower()
                if ext in ('.doc', '.ppt'):
                    print(f"  Adding {ext} to skip list (Blackboard loading issue)")
                    SKIP_EXTENSIONS.add(ext)

                continue
        else:
            # If we didn't break (all items processed or skipped), try next page
            if go_to_next_page():
                page_num += 1
            else:
                print("\nNo more pages. Done!")
                break

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Processed: {total_processed}")
    print(f"  Skipped:   {total_skipped}")
    print(f"  Failed:    {total_failed}")
    print(f"{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python process_all.py <course> [--dry-run] [--skip-old-formats]")
        print(f"Known courses: {', '.join(COURSES.keys())}")
        sys.exit(1)

    course = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if '--skip-old-formats' in sys.argv:
        SKIP_EXTENSIONS.update({'.doc', '.ppt'})

    process_all(course, dry_run=dry_run)
