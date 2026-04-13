"""Upload a fixed file to Blackboard via the accessibility report feedback window.

Navigates to the item in the report, opens feedback, uploads the fixed file.
Uses disconnect/reconnect pattern.

Usage:
    python scripts/upload_item.py <course> <item_name> <fixed_file_path>
    python scripts/upload_item.py CYBERINFRA "Lec2.ppt" path/to/Lec2_fixed.pptx
    python scripts/upload_item.py CYBERINFRA "F24-DSci523-Lec5(1).ppt" path/to/fixed.pptx
"""
import sys, os, time

sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, dismiss_popup

COURSES = {
    'CYBERINFRA': '_1308272_1',
    'ITEC493': '_1308255_1',
    'ITEC445': '_1328539_1',
    'ITEC552': '_1308261_1',
}


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


def find_feedback_page(browser):
    """Find the Ally feedback page among open tabs."""
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            return pg
    return None


def find_feedback_frame(fb_page):
    """Find the frame with feedback content."""
    for f in fb_page.frames:
        try:
            has = f.evaluate('() => !!document.querySelector("input[type=file]")')
            if has:
                return f
        except:
            pass
    return fb_page.frames[-1] if len(fb_page.frames) > 1 else fb_page


def close_feedback_windows():
    """Close any open feedback windows."""
    p, browser, page = connect()
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            pg.close()
    disconnect(p, browser)


def upload_item(course_id, item_name, fixed_path):
    """Click item in report, open feedback, upload fixed file.
    Returns new score or None."""

    fixed_path = os.path.abspath(fixed_path)
    if not os.path.exists(fixed_path):
        print(f"ERROR: Fixed file not found: {fixed_path}")
        return None

    print(f"Uploading: {item_name}")
    print(f"  File: {os.path.basename(fixed_path)} ({os.path.getsize(fixed_path):,} bytes)")

    # Close any leftover feedback windows
    close_feedback_windows()

    # Step 1: Click the item in the report
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        print("  ERROR: Items frame not found. Is the report loaded on Content tab?")
        disconnect(p, browser)
        return None

    # Get current score
    current_score = items_frame.evaluate("""(name) => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        for (const row of rows) {
            const el = row.querySelector('.ir-content-list-item-name-text-name');
            if (el && el.innerText.trim() === name) {
                const score = row.querySelector('.feedback-score-indicator span');
                return score ? score.innerText.trim() : '?';
            }
        }
        return null;
    }""", item_name)

    if current_score is None:
        print(f"  ERROR: Item '{item_name}' not found in current report page")
        disconnect(p, browser)
        return None

    print(f"  Current score: {current_score}")

    # Click the item
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
        print(f"  ERROR: Could not click item")
        disconnect(p, browser)
        return None

    # Disconnect to let feedback window load
    disconnect(p, browser)
    print("  Waiting for feedback window...")
    time.sleep(15)

    # Step 2: Find feedback window and upload
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        print("  ERROR: Feedback window not found")
        disconnect(p, browser)
        return None

    fb_frame = find_feedback_frame(fb_page)

    # Find file input
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        print("  ERROR: No file input found in feedback window")
        fb_page.close()
        disconnect(p, browser)
        return None

    # Upload
    file_input.set_input_files(fixed_path)
    print(f"  Uploading...")

    # Wait for new score
    new_score = None
    for _ in range(90):
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

    # Close feedback window
    fb_page.close()
    disconnect(p, browser)

    if new_score:
        print(f"  NEW SCORE: {new_score}")
    else:
        print(f"  Upload completed (score not verified)")

    return new_score


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python upload_item.py <course> <item_name> <fixed_file_path>")
        print(f"Known courses: {', '.join(COURSES.keys())}")
        sys.exit(1)

    course = sys.argv[1].upper()
    item_name = sys.argv[2]
    fixed_path = sys.argv[3]

    course_id = COURSES.get(course, course)

    result = upload_item(course_id, item_name, fixed_path)
    if result:
        print(f"\nDone! {item_name}: {result}")
    else:
        print(f"\nUpload completed for {item_name}")
