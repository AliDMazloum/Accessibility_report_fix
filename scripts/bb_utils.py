"""Blackboard browser automation utilities."""
from playwright.sync_api import sync_playwright
import time, json, os

BASE_DIR = "C:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report"
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
COURSE_DIR = os.path.join(BASE_DIR, "course_content")
SCREENSHOT_PATH = os.path.join(SCREENSHOTS_DIR, "current_page.png")
CDP_URL = "http://localhost:9222"

def connect():
    """Connect to Chrome via CDP. Returns (playwright, browser, page)."""
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = browser.contexts[0].pages[-1]
    return p, browser, page

def disconnect(p, browser):
    """Clean disconnect."""
    browser.close()
    p.stop()

def screenshot(page, name="current_page"):
    """Take screenshot with font wait disabled."""
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    try:
        page.screenshot(path=path, timeout=10000)
    except:
        # Fallback: use CDP screenshot
        result = page.evaluate("() => { return 'screenshot_fallback'; }")
    return path

def dismiss_popup(page):
    """Dismiss Blackboard course evaluation popup."""
    try:
        page.click("text=Remind Me Later", timeout=3000)
        return True
    except:
        return False

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

def scroll_panel(page):
    """Scroll the Blackboard panel-wrap container to load lazy-loaded items."""
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

def scroll_and_collect_all_items(page):
    """Scroll the course page to load and collect all content items."""
    scroll_panel(page)
    return get_course_content_items(page)

def list_courses(page):
    """Navigate to courses page and return all courses grouped by semester.
    Returns list of dicts with keys: name, semester.
    Blackboard uses JS routing so course IDs aren't in href attributes."""
    page.goto('https://blackboard.sc.edu/ultra/institution-page', wait_until='domcontentloaded', timeout=30000)
    time.sleep(3)
    dismiss_popup(page)
    # Click Courses in sidebar
    page.click('text=Courses', timeout=5000)
    time.sleep(3)
    # Scroll to load all courses
    for _ in range(5):
        page.evaluate('() => window.scrollBy(0, 600)')
        time.sleep(0.5)
    # Extract courses using H3 (semester) and H4 (course name) headings
    courses = page.evaluate("""() => {
        const all = [];
        let semester = '';
        const elems = document.querySelectorAll('h3, h4');
        for (const el of elems) {
            if (el.tagName === 'H3') {
                semester = el.innerText.trim();
            } else {
                const name = el.innerText.trim();
                if (name) all.push({semester: semester, name: name});
            }
        }
        return all;
    }""")
    return courses

def navigate_to_course(page, course_id="_1328539_1"):
    """Navigate to course outline page."""
    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    dismiss_popup(page)

def navigate_to_report(page, course_id="_1328539_1"):
    """Navigate to accessibility report."""
    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline/lti/launchFrame?toolHref=https:~2F~2Fblackboard.sc.edu~2Fwebapps~2Fblackboard~2Fexecute~2Fblti~2FlaunchPlacement%3Fblti_placement_id%3D_393_1%26course_id%3D{course_id}%26from_ultra%3Dtrue&toolTitle=Accessibility%20Report"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    dismiss_popup(page)

def find_report_frame(page):
    """Find the iframe containing the Ally report content list."""
    for i, f in enumerate(page.frames):
        try:
            if f.query_selector('tr.ir-list-item'):
                return f, i
        except:
            pass
    return None, -1

def get_report_items(frame):
    """Extract items from current page of the accessibility report."""
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
    """Get all items across all pages of the report."""
    all_items = []
    items = get_report_items(frame)
    all_items.extend(items)

    for pg in range(2, 20):
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

def click_report_item(frame, row_index, browser):
    """Click a report item and extract its issues from the popup. Closes popup after."""
    pages_before = len(browser.contexts[0].pages)

    frame.evaluate("""(idx) => {
        const rows = document.querySelectorAll('tr.ir-list-item');
        if (rows[idx]) {
            const btn = rows[idx].querySelector('button');
            if (btn) btn.click();
        }
    }""", row_index)

    # Wait for popup
    for _ in range(15):
        time.sleep(0.5)
        if len(browser.contexts[0].pages) > pages_before:
            break
    else:
        return []

    time.sleep(2)

    # Find ally feedback page
    fb_page = None
    for pg in browser.contexts[0].pages:
        if 'ally.ac' in pg.url and 'launchinstructorfeedback' in pg.url:
            fb_page = pg
            break

    if not fb_page:
        return []

    fb_frame = fb_page.frames[-1] if len(fb_page.frames) > 1 else fb_page

    # Click 'Show all issues'
    try:
        fb_frame.evaluate("""() => {
            const toggle = document.querySelector('.ally-if-toggle-all-issues');
            if (toggle) toggle.click();
        }""")
        time.sleep(0.5)
    except:
        pass

    # Extract issues
    try:
        issues = fb_frame.evaluate("""() => {
            const issueEls = document.querySelectorAll('.ally-if-listed-issue');
            const result = [];
            issueEls.forEach(el => {
                const parts = el.innerText.trim().split(String.fromCharCode(10));
                result.push(parts[0] || el.innerText.trim());
            });
            if (result.length === 0) {
                const mainIssue = document.querySelector('.ally-if-issue-summary');
                if (mainIssue) result.push(mainIssue.innerText.trim());
            }
            return result;
        }""")
    except:
        issues = []

    # ALWAYS close the feedback page
    fb_page.close()
    time.sleep(0.5)

    return issues

def save_json(data, filename):
    """Save data as JSON in the project directory."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    return path

def load_json(filename):
    """Load JSON from the data directory."""
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)

def scrape_accessibility_report(page, course_id):
    """Scrape the full accessibility report for a course.
    Returns list of items with name, type, issues, score, contentId.

    Steps:
    1. Navigate to report (LTI launch)
    2. Wait for iframe to load
    3. Click Content tab INSIDE the report frame (not course nav)
    4. Extract all items across all pages
    """
    navigate_to_report(page, course_id)
    time.sleep(10)
    dismiss_popup(page)

    # Find report frame (contains 'Course accessibility' text)
    report_frame = None
    for f in page.frames:
        try:
            is_report = f.evaluate(
                '() => document.body.innerText.includes("Course accessibility")'
            )
            if is_report:
                report_frame = f
                break
        except:
            pass

    if not report_frame:
        return []

    # Click Content tab inside report frame
    report_frame.evaluate("""() => {
        for (const t of document.querySelectorAll('a, button')) {
            if (t.innerText.trim() === 'Content') { t.click(); return; }
        }
    }""")
    time.sleep(5)

    # Find frame with item rows (may be different frame after tab switch)
    items_frame = None
    for f in page.frames:
        try:
            count = f.evaluate(
                '() => document.querySelectorAll("tr.ir-list-item").length'
            )
            if count > 0:
                items_frame = f
                break
        except:
            pass

    if not items_frame:
        return []

    return get_all_report_items(items_frame)
