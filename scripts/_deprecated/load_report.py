"""Navigate to a course's accessibility report, click Content tab, and list items.

Uses disconnect/reconnect pattern to avoid throttling Chrome during loading.

Usage:
    python scripts/load_report.py <course_id>
    python scripts/load_report.py _1308272_1       # CYBERINFRA
    python scripts/load_report.py _1308255_1       # ITEC493
"""
import sys, time
from bb_utils import connect, disconnect, navigate_to_report, dismiss_popup, get_report_items

COURSES = {
    'CYBERINFRA': '_1308272_1',
    'ITEC493': '_1308255_1',
    'ITEC445': '_1328539_1',
    'ITEC552': '_1308261_1',
}


def find_report_frame(page):
    """Find the frame containing 'Course accessibility' text."""
    for f in page.frames:
        try:
            if f.evaluate('() => document.body.innerText.includes("Course accessibility")'):
                return f
        except:
            pass
    return None


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


def load_report_content(course_id):
    """Navigate to report, click Content tab, return items on current page.

    Uses disconnect/reconnect pattern:
    1. Connect, navigate to report
    2. Disconnect, wait for Chrome to load
    3. Reconnect, click Content tab
    4. Disconnect, wait for content to load
    5. Reconnect, extract items
    """
    # Step 1: Navigate to report (don't wait for full load — disconnect immediately)
    p, browser, page = connect()
    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline/lti/launchFrame?toolHref=https:~2F~2Fblackboard.sc.edu~2Fwebapps~2Fblackboard~2Fexecute~2Fblti~2FlaunchPlacement%3Fblti_placement_id%3D_393_1%26course_id%3D{course_id}%26from_ultra%3Dtrue&toolTitle=Accessibility%20Report"
    try:
        page.goto(url, wait_until="commit", timeout=15000)
    except Exception:
        pass  # OK if it times out — we disconnect anyway
    disconnect(p, browser)
    print("Navigated to report, waiting for load...")
    time.sleep(15)

    # Step 2: Click Content tab
    p, browser, page = connect()
    dismiss_popup(page)
    report_frame = find_report_frame(page)
    if not report_frame:
        print("ERROR: Could not find report frame")
        disconnect(p, browser)
        return []

    report_frame.evaluate("""() => {
        for (const t of document.querySelectorAll('a, button')) {
            if (t.innerText.trim() === 'Content') { t.click(); return true; }
        }
        return false;
    }""")
    print("Clicked Content tab, waiting for items to load...")
    disconnect(p, browser)
    time.sleep(10)

    # Step 3: Extract items
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        print("ERROR: Could not find items frame")
        disconnect(p, browser)
        return []

    items = get_report_items(items_frame)
    disconnect(p, browser)
    return items


def print_items(items):
    """Print items in a formatted table."""
    print(f"\n{'Score':>6}  {'Type':<20}  {'Name'}")
    print("-" * 70)
    for item in items:
        print(f"{item.get('score', '?'):>6}  {item.get('type', ''):.<20}  {item['name']}")
    print(f"\nTotal: {len(items)} items on this page")

    # Count items below 85%
    below = [i for i in items if i.get('score', '').replace('%', '').isdigit()
             and int(i['score'].replace('%', '')) < 85]
    print(f"Below 85%: {len(below)} items")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python load_report.py <course_id or name>")
        print(f"Known courses: {', '.join(COURSES.keys())}")
        sys.exit(1)

    arg = sys.argv[1]
    course_id = COURSES.get(arg.upper(), arg)

    print(f"Loading accessibility report for course {course_id}...")
    items = load_report_content(course_id)
    if items:
        print_items(items)
    else:
        print("No items found.")
