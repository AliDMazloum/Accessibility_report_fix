"""Blackboard browser automation utilities.

Central module for all Blackboard automation. All phase scripts import from here.
No other script should define its own navigation, frame-finding, or COURSES logic.
"""
from playwright.sync_api import sync_playwright
import time, json, os

# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR = "C:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report"
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
COURSE_DIR = os.path.join(BASE_DIR, "course_content")
CDP_URL = "http://localhost:9222"

# ── Courses ───────────────────────────────────────────────────────────────

def load_courses():
    """Load courses from the central courses.json config."""
    path = os.path.join(SCRIPTS_DIR, "courses.json")
    with open(path) as f:
        return json.load(f)


def get_course(key):
    """Get a single course config by key. Returns {id, dir}."""
    courses = load_courses()
    key = key.upper()
    if key not in courses:
        raise KeyError(f"Unknown course '{key}'. Known: {', '.join(courses.keys())}")
    return courses[key]


def report_filename(course_key):
    """Standard report filename for a course."""
    return f"report_{course_key.upper()}.json"


def targets_filename(course_key):
    """Standard targets filename for a course."""
    return f"targets_{course_key.upper()}.json"


def download_manifest_filename(course_key):
    """Standard download manifest filename."""
    return f"download_manifest_{course_key.upper()}.json"


def fix_manifest_filename(course_key):
    """Standard fix manifest filename."""
    return f"fix_manifest_{course_key.upper()}.json"


# ── Connection ────────────────────────────────────────────────────────────

def connect():
    """Connect to Chrome via CDP. Returns (playwright, browser, page)."""
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = browser.contexts[0].pages[-1]
    return p, browser, page


def disconnect(p, browser):
    """Clean disconnect from Chrome."""
    browser.close()
    p.stop()


# ── Popups ────────────────────────────────────────────────────────────────

def dismiss_popup(page):
    """Dismiss Blackboard course evaluation popup if present."""
    try:
        page.click("text=Remind Me Later", timeout=3000)
        return True
    except:
        return False


# ── Navigation ────────────────────────────────────────────────────────────

def report_url(course_id):
    """Build the accessibility report URL for a course."""
    return (
        f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline/lti/launchFrame"
        f"?toolHref=https:~2F~2Fblackboard.sc.edu~2Fwebapps~2Fblackboard~2Fexecute~2Fblti"
        f"~2FlaunchPlacement%3Fblti_placement_id%3D_393_1%26course_id%3D{course_id}"
        f"%26from_ultra%3Dtrue&toolTitle=Accessibility%20Report"
    )


def navigate_to_report_content(course_id, nav_wait=10, tab_wait=5):
    """Navigate to accessibility report and click Content tab.

    Uses disconnect/reconnect pattern:
    1. Connect, start navigation (wait_until='commit' to avoid timeout)
    2. Disconnect, wait for Chrome to load freely
    3. Reconnect, click Content tab
    4. Disconnect, wait for content to load
    5. Reconnect — caller gets items frame
    """
    # Step 1: Navigate
    p, browser, page = connect()
    try:
        page.goto(report_url(course_id), wait_until="commit", timeout=15000)
    except Exception:
        pass  # OK — we disconnect anyway
    disconnect(p, browser)
    time.sleep(nav_wait)

    # Step 2: Click Content tab
    p, browser, page = connect()
    dismiss_popup(page)
    rf = find_report_overview_frame(page)
    if rf:
        rf.evaluate("""() => {
            for (const t of document.querySelectorAll('a, button')) {
                if (t.innerText.trim() === 'Content') { t.click(); return true; }
            }
            return false;
        }""")
    disconnect(p, browser)
    time.sleep(tab_wait)


def reload_report_content(reload_wait=5, tab_wait=5):
    """Reload the current report page and re-click Content tab.

    Used between uploads to refresh the report after score changes.
    """
    p, browser, page = connect()
    try:
        page.reload(wait_until="commit", timeout=15000)
    except Exception:
        pass  # OK — we disconnect and wait below
    disconnect(p, browser)
    time.sleep(reload_wait)

    p, browser, page = connect()
    dismiss_popup(page)
    rf = find_report_overview_frame(page)
    if rf:
        rf.evaluate("""() => {
            for (const t of document.querySelectorAll('a, button')) {
                if (t.innerText.trim() === 'Content') { t.click(); return true; }
            }
            return false;
        }""")
    disconnect(p, browser)
    time.sleep(tab_wait)


def navigate_to_course(page, course_id):
    """Navigate to course outline page (stays connected)."""
    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    dismiss_popup(page)


def navigate_to_report(page, course_id):
    """Navigate to accessibility report (stays connected). Use navigate_to_report_content() for disconnect/reconnect version."""
    page.goto(report_url(course_id), wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    dismiss_popup(page)


def list_courses(page):
    """Navigate to courses page and return all courses grouped by semester."""
    page.goto('https://blackboard.sc.edu/ultra/course', wait_until='domcontentloaded', timeout=30000)
    time.sleep(3)
    dismiss_popup(page)
    for _ in range(5):
        page.evaluate('() => window.scrollBy(0, 600)')
        time.sleep(0.5)
    return page.evaluate("""() => {
        const all = [];
        let semester = '';
        const elems = document.querySelectorAll('h3, h4');
        for (const el of elems) {
            if (el.tagName === 'H3') semester = el.innerText.trim();
            else {
                const name = el.innerText.trim();
                if (name) all.push({semester, name});
            }
        }
        return all;
    }""")


# ── Frame Finders ─────────────────────────────────────────────────────────

def find_report_overview_frame(page):
    """Find the frame containing the accessibility report overview ('Course accessibility' text).
    Used to click the Content tab."""
    for f in page.frames:
        try:
            if f.evaluate('() => document.body.innerText.includes("Course accessibility")'):
                return f
        except:
            pass
    return None


def find_items_frame(page):
    """Find the frame containing report item rows (tr.ir-list-item).
    Used to extract and click items after Content tab is active."""
    for f in page.frames:
        try:
            count = f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length')
            if count > 0:
                return f
        except:
            pass
    return None


def find_feedback_page(browser):
    """Find the Ally feedback page among open browser tabs."""
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            return pg
    return None


def find_feedback_frame(fb_page):
    """Find the content frame inside the feedback page (contains file input for upload)."""
    for f in fb_page.frames:
        try:
            if f.evaluate('() => !!document.querySelector("input[type=file]")'):
                return f
        except:
            pass
    return fb_page.frames[-1] if len(fb_page.frames) > 1 else fb_page


def close_feedback_windows():
    """Close any open Ally feedback windows."""
    p, browser, page = connect()
    for pg in browser.contexts[0].pages:
        if 'ally' in pg.url and 'feedback' in pg.url.lower():
            pg.close()
    disconnect(p, browser)


# ── Report Item Operations ────────────────────────────────────────────────

def get_report_items(frame):
    """Extract items from the current page of the accessibility report."""
    return frame.evaluate("""() => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        const data = [];
        rows.forEach(row => {
            const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
            const typeEl = row.querySelector('.ir-content-list-item-name-text-type');
            const issuesEl = row.querySelector('.ir-content-list-item-issues span');
            const scoreEl = row.querySelector('.feedback-score-indicator span');
            const btn = row.querySelector('button');
            const contentId = btn ? btn.getAttribute('data-ally-content-id') : '';
            if (nameEl) {
                data.push({
                    name: nameEl.innerText.trim(),
                    type: typeEl ? typeEl.innerText.trim() : '',
                    issues: issuesEl ? issuesEl.innerText.trim() : '',
                    score: scoreEl ? scoreEl.innerText.trim() : '',
                    contentId: contentId || ''
                });
            }
        });
        return data;
    }""")


def get_all_report_items(frame):
    """Get all items across all pages of the report (clicks 'Next' links)."""
    all_items = []
    items = get_report_items(frame)
    all_items.extend(items)

    for pg in range(2, 30):
        next_links = frame.query_selector_all('a.ng-star-inserted')
        clicked = False
        for link in next_links:
            text = link.inner_text().strip()
            if 'Next' in text:
                link.click()
                clicked = True
                break
        if not clicked:
            break
        time.sleep(1.5)
        items = get_report_items(frame)
        if not items:
            break
        all_items.extend(items)

    return all_items


def click_item_by_name(frame, item_name):
    """Click a report item by its name. Returns True if found and clicked."""
    return frame.evaluate("""(name) => {
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


def get_page_items(frame):
    """Get all items on the current report page with name, type, and score."""
    return frame.evaluate("""() => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        const data = [];
        rows.forEach(row => {
            const nameEl = row.querySelector('.ir-content-list-item-name-text-name');
            const typeEl = row.querySelector('.ir-content-list-item-name-text-type');
            const scoreEl = row.querySelector('.feedback-score-indicator span');
            if (nameEl) data.push({
                name: nameEl.innerText.trim(),
                type: typeEl ? typeEl.innerText.trim() : '',
                score: scoreEl ? scoreEl.innerText.trim() : '?'
            });
        });
        return data;
    }""")


def click_next_page(frame):
    """Click 'Next' on report pagination. Returns True if successful."""
    next_links = frame.query_selector_all('a.ng-star-inserted')
    for link in next_links:
        text = link.inner_text().strip()
        if 'Next' in text:
            link.click()
            time.sleep(1.5)
            return True
    return False


# ── Course Outline Operations ─────────────────────────────────────────────

def scroll_panel(page):
    """Scroll the course panel-wrap to load lazy-loaded items."""
    prev_count = 0
    for i in range(60):
        page.evaluate("""() => {
            const panel = document.querySelector('.panel-wrap');
            if (panel) panel.scrollBy(0, 400);
        }""")
        time.sleep(0.5)
        count = page.evaluate('() => document.querySelectorAll("div[data-content-id]").length')
        if count != prev_count:
            prev_count = count
        elif i > 5:
            break
    return prev_count


def scroll_panel_to_top(page):
    """Scroll the panel-wrap container back to the top."""
    page.evaluate("""() => {
        const panel = document.querySelector('.panel-wrap');
        if (panel) panel.scrollTo(0, 0);
    }""")
    time.sleep(0.5)


def get_course_content_items(page):
    """Get all visible content items on the course outline page."""
    return page.evaluate("""() => {
        const divs = document.querySelectorAll('div[data-content-id]');
        const result = [];
        divs.forEach(div => {
            const id = div.getAttribute('data-content-id');
            const lines = div.innerText.trim().split(String.fromCharCode(10));
            const title = lines[0] || '';
            result.push({id: id, title: title.substring(0, 200), fullText: div.innerText.trim().substring(0, 500)});
        });
        return result;
    }""")


def scroll_and_collect_all_items(page):
    """Scroll course page to load and collect all content items."""
    scroll_panel(page)
    return get_course_content_items(page)


# ── JSON I/O ──────────────────────────────────────────────────────────────

def save_json(data, filename):
    """Save data as JSON in the data directory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    return path


def load_json(filename):
    """Load JSON from the data directory."""
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)
