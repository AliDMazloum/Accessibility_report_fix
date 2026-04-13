"""Single-pass download script for Blackboard accessibility files.

Combines course mapping and downloading into one pass:
1. Load target files from accessibility report (score < threshold)
2. Navigate to course outline
3. Iterate through every content item (expanding modules/folders)
4. For each item: check if it has a target file -> download immediately
5. Save course structure at the end

Usage:
    python download_all.py ITEC552 _1234567_1
    python download_all.py ITEC445
    python download_all.py ITEC493
"""
import sys, os, json, time, argparse, re
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import (connect, disconnect, dismiss_popup, scroll_panel,
                      scroll_panel_to_top, save_json, COURSE_DIR, DATA_DIR,
                      scrape_accessibility_report)

SCORE_THRESHOLD = 85

COURSES = {
    "ITEC493": {"id": "_1308255_1", "report": "accessibility_report_ITEC493.json",
                "dir": "ITEC493-001-FALL-2025"},
    "ITEC445": {"id": "_1328539_1", "report": "accessibility_report.json",
                "dir": "ITEC445-001-SPRING-2026"},
    "ITEC552": {"id": "_1308261_1", "report": "accessibility_report_ITEC552.json",
                "dir": "ITEC552-001-FALL-2025"},
    "CYBERINFRA": {"id": "_1308272_1", "report": "accessibility_report_CYBERINFRA.json",
                   "dir": "CYBERINFRA-FALL-2025"},
}

SKIP_TYPES = {'Folder', 'Open Folder', 'Learning Module'}


# ── Helpers ────────────────────────────────────────────────────────────────

def strip_suffix(name):
    """Remove all trailing (N) suffixes from filename.
    e.g. 'Lecture 2(1).pptx' -> 'Lecture 2.pptx'
         'file(1)(1).pptx' -> 'file.pptx'"""
    stem, ext = os.path.splitext(name)
    while re.search(r'\(\d+\)$', stem):
        stem = re.sub(r'\(\d+\)$', '', stem).rstrip()
    return stem + ext


def load_target_files(report_file):
    """Load target files and build a normalized lookup for (N) suffix matching.
    Returns (targets, norm_lookup) where:
      targets: {report_name: {score, type}}
      norm_lookup: {stripped_name: report_name} for names that have (N) suffixes
    """
    path = os.path.join(DATA_DIR, report_file)
    with open(path) as f:
        items = json.load(f)
    targets = {}
    norm_lookup = {}
    for item in items:
        score = int(item['score'].replace('%', ''))
        if score < SCORE_THRESHOLD and item['type'] != 'Ultra document':
            name = item['name']
            targets[name] = {'score': score, 'type': item['type']}
            stripped = strip_suffix(name)
            if stripped != name:
                norm_lookup[stripped] = name
    return targets, norm_lookup


def setup_download_dir(browser, page, directory):
    os.makedirs(directory, exist_ok=True)
    cdp = browser.contexts[0].new_cdp_session(page)
    cdp.send("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": os.path.abspath(directory).replace("/", os.sep),
    })


def get_file_from_iframe(page):
    return page.evaluate(r"""() => {
        for (const f of document.querySelectorAll('iframe')) {
            const t = f.getAttribute('title') || '';
            if (/\.(pdf|pptx?|docx?|xlsx?)$/i.test(t)) return t;
        }
        return null;
    }""")


def get_file_from_more_options(page):
    return page.evaluate(r"""() => {
        for (const b of document.querySelectorAll('button')) {
            const label = b.getAttribute('aria-label') || '';
            const m = label.match(/^More options for (.+\.(?:pdf|pptx?|docx?|xlsx?))$/i);
            if (m) return m[1];
        }
        return null;
    }""")


def click_inner_content_link(page):
    return page.evaluate("""() => {
        for (const a of document.querySelectorAll('a')) {
            const rect = a.getBoundingClientRect();
            if (rect.y > 170 && rect.y < 290 && a.innerText.trim().length > 3) {
                a.click();
                return a.innerText.trim();
            }
        }
        return null;
    }""")


def download_via_more_options(page, file_name):
    page.evaluate("""(fname) => {
        for (const b of document.querySelectorAll('button')) {
            if (b.getAttribute('aria-label') === 'More options for ' + fname) {
                b.click(); return;
            }
        }
    }""", file_name)
    time.sleep(2)
    return page.evaluate("""() => {
        for (const el of document.querySelectorAll('a, button, [role=menuitem], li, span')) {
            if (el.innerText.trim() === 'Download original file') {
                el.click(); return true;
            }
        }
        return false;
    }""")


def download_via_viewer(page):
    for _ in range(15):
        for frame in page.frames:
            try:
                if frame.evaluate('() => !!document.querySelector(\'button[aria-label="Download"]\')'):
                    frame.click('button[aria-label="Download"]')
                    return True
            except:
                pass
        time.sleep(1)
    return False


def wait_for_file(path, timeout=45):
    for _ in range(timeout):
        time.sleep(1)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            if not os.path.exists(path + ".crdownload"):
                return True
    return os.path.exists(path) and os.path.getsize(path) > 0


# ── Course outline helpers ─────────────────────────────────────────────────

def scroll_down(page, times=5):
    for _ in range(times):
        page.evaluate("() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }")
        time.sleep(0.3)


def get_all_items(page):
    return page.evaluate("""() => {
        const divs = document.querySelectorAll('div[data-content-id]');
        const result = [];
        divs.forEach(div => {
            const id = div.getAttribute('data-content-id');
            const iconSvg = div.querySelector('svg[aria-label]');
            const type = iconSvg ? iconSvg.getAttribute('aria-label') : 'unknown';
            const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
            const h3 = div.querySelector('h3');
            let title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
            if (!title) {
                const btn = div.querySelector('button[aria-label*="Reorder"]');
                if (btn) title = btn.getAttribute('aria-label').replace('Reorder ', '').replace('.', '').trim();
            }
            const parentContent = div.parentElement ? div.parentElement.closest('div[data-content-id]') : null;
            const parentId = parentContent ? parentContent.getAttribute('data-content-id') : 'root';
            result.push({id, type, title: title.substring(0, 200), parentId});
        });
        return result;
    }""")


def get_direct_children(page, parent_id):
    return page.evaluate("""(pid) => {
        const parentDiv = document.querySelector('div[data-content-id="' + pid + '"]');
        if (!parentDiv) return [];
        const result = [];
        parentDiv.querySelectorAll('div[data-content-id]').forEach(div => {
            const id = div.getAttribute('data-content-id');
            if (id === pid) return;
            const iconSvg = div.querySelector('svg[aria-label]');
            const type = iconSvg ? iconSvg.getAttribute('aria-label') : 'unknown';
            const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
            const h3 = div.querySelector('h3');
            let title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
            if (!title) {
                const btn = div.querySelector('button[aria-label*="Reorder"]');
                if (btn) title = btn.getAttribute('aria-label').replace('Reorder ', '').replace('.', '').trim();
            }
            result.push({id, title: title.substring(0, 200), type});
        });
        return result;
    }""", parent_id)


def toggle_item(page, cid):
    page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (div) {
            div.scrollIntoView({behavior: 'instant', block: 'center'});
            const ct = div.querySelector('.click-to-invoke-container');
            if (ct) ct.click();
        }
    }""", cid)
    time.sleep(2)


def is_expanded(page, cid):
    return page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (!div) return false;
        const el = div.querySelector('[aria-expanded]');
        return el ? el.getAttribute('aria-expanded') === 'true' : false;
    }""", cid)


def get_item_title(page, cid):
    return page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (!div) return '';
        const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
        const h3 = div.querySelector('h3');
        let title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
        if (!title) {
            const btn = div.querySelector('button[aria-label*="Reorder"]');
            if (btn) title = btn.getAttribute('aria-label').replace('Reorder ', '').replace('.', '').trim();
        }
        return title;
    }""", cid)


# ── Try to find and download a file from a content item ────────────────────

def visit_and_download(page, browser, course_id, item_id, section_dir, target_files, norm_lookup=None):
    """Navigate to a content item, check for target file, download if found.
    Returns (file_name, status) or (None, 'no file'/'not target'/'skip').
    file_name returned is the report name (may differ from Blackboard name if (N) suffix)."""

    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline/file/{item_id}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
    except:
        return None, "nav error"
    time.sleep(2)
    dismiss_popup(page)

    # Method A: Direct file viewer (PDF/Presentation items)
    file_name = get_file_from_iframe(page)

    # Method B: Text Document - click inner link, check "More options for" buttons
    if not file_name:
        click_inner_content_link(page)
        time.sleep(3)
        file_name = get_file_from_more_options(page)

    if not file_name:
        return None, "no file"

    # Check exact match first, then try normalized (N) suffix match
    report_name = file_name
    if file_name not in target_files:
        if norm_lookup and file_name in norm_lookup:
            report_name = norm_lookup[file_name]
        else:
            return (file_name, file_name), "not target"

    save_path = os.path.join(section_dir, file_name)

    # Already downloaded?
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return (file_name, report_name), "already exists"

    # Set CDP download dir
    setup_download_dir(browser, page, section_dir)

    # Try downloading: first via direct viewer, then via "..." menu
    downloaded = False

    # Re-check if we're on a page with direct viewer
    if get_file_from_iframe(page):
        downloaded = download_via_viewer(page)
        if downloaded:
            downloaded = wait_for_file(save_path)

    if not downloaded:
        # Navigate back to the item and try "..." menu approach
        found = get_file_from_more_options(page)
        if not found:
            # May need to re-navigate
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
            except:
                return (file_name, report_name), "re-nav error"
            time.sleep(2)
            dismiss_popup(page)
            click_inner_content_link(page)
            time.sleep(3)
            setup_download_dir(browser, page, section_dir)
            found = get_file_from_more_options(page)

        if found:
            if download_via_more_options(page, found):
                actual_path = os.path.join(section_dir, found)
                downloaded = wait_for_file(actual_path)

    if downloaded or (os.path.exists(save_path) and os.path.getsize(save_path) > 0):
        return (file_name, report_name), "downloaded"
    else:
        return (file_name, report_name), "download failed"


# ── Main: single-pass map + download ──────────────────────────────────────

def process_course(course_name, course_id, report_file, course_dir_name, browser, page):
    course_dir = os.path.join(COURSE_DIR, course_dir_name)
    target_files, norm_lookup = load_target_files(report_file)

    print(f"\n{'='*60}")
    print(f"COURSE: {course_name}")
    print(f"Target files (score < {SCORE_THRESHOLD}%): {len(target_files)}")
    print(f"{'='*60}")
    for name, info in sorted(target_files.items(), key=lambda x: x[1]['score']):
        print(f"  {info['score']:3d}%  {name}")

    # Navigate to course outline
    page.goto(f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline",
              wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    dismiss_popup(page)

    # Load all top-level items
    scroll_panel(page)
    scroll_panel_to_top(page)

    all_items = get_all_items(page)
    top_modules = [i for i in all_items if i['parentId'] == 'root' and i['type'] == 'Learning Module']
    top_other = [i for i in all_items if i['parentId'] == 'root' and i['type'] != 'Learning Module']

    # Get course code
    course_code = page.evaluate(r"""() => {
        const lines = document.body.innerText.split('\n');
        for (const line of lines) {
            const t = line.trim();
            if (/^[A-Z]{3,4}\d{3}/.test(t)) return t;
        }
        return '';
    }""") or course_name

    print(f"\nCourse code: {course_code}")
    print(f"Top-level items: {len(top_other)}, Modules: {len(top_modules)}")

    # Build structure and download simultaneously
    course_structure = {'_course_name': course_code, '_top_level': top_other}
    downloaded = []
    failed = []
    remaining = set(target_files.keys())

    def process_item(item, section):
        """Visit a single item, try to download if it's a target."""
        nonlocal remaining
        if not remaining:
            return

        if item['type'] in SKIP_TYPES:
            return

        section_dir = os.path.join(
            course_dir, section.replace(':', ' -').replace('/', '-').strip()
        )
        result, status = visit_and_download(
            page, browser, course_id, item['id'], section_dir, target_files, norm_lookup
        )

        if isinstance(result, tuple):
            file_name, report_name = result
        else:
            file_name, report_name = result, result

        if file_name and status == "downloaded":
            fpath = os.path.join(section_dir, file_name)
            size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
            suffix = f" (matched {report_name})" if report_name != file_name else ""
            print(f"      -> DOWNLOADED {file_name}{suffix} ({size:,} bytes)")
            downloaded.append({'file': file_name, 'report_name': report_name, 'score': target_files[report_name]['score'], 'size': size})
            remaining.discard(report_name)
        elif file_name and status == "already exists":
            fpath = os.path.join(section_dir, file_name)
            size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
            suffix = f" (matched {report_name})" if report_name != file_name else ""
            print(f"      -> exists: {file_name}{suffix} ({size:,} bytes)")
            downloaded.append({'file': file_name, 'report_name': report_name, 'score': target_files[report_name]['score'], 'size': size})
            remaining.discard(report_name)
        elif file_name and status == "not target":
            pass  # Not a target, skip silently
        elif file_name and "failed" in status:
            print(f"      -> FAILED: {file_name} ({status})")
            failed.append({'file': file_name, 'reason': status})

    def explore_folder(folder_id, section, depth=0):
        """Expand folder, process children, collapse."""
        # Need to navigate back to course outline first
        page.goto(f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline",
                  wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        scroll_panel(page)
        scroll_panel_to_top(page)

        title = get_item_title(page, folder_id)
        toggle_item(page, folder_id)
        scroll_down(page, 3)
        time.sleep(1)
        children = get_direct_children(page, folder_id)

        indent = "  " * (depth + 2)
        print(f"{indent}[Folder] {title}: {len(children)} items")

        result = []
        for child in children:
            print(f"{indent}  [{child['type']}] {child['title']}")
            child_data = dict(child)

            if child['type'] in ('Folder', 'Open Folder'):
                folder_children = explore_folder(child['id'], section, depth + 1)
                child_data['children'] = folder_children
            else:
                process_item(child, section)

            result.append(child_data)

        # Collapse
        page.goto(f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline",
                  wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        scroll_panel(page)

        return result

    # Process top-level non-module items
    print(f"\n--- Top-level items ---")
    for item in top_other:
        print(f"  [{item['type']}] {item['title']}")
        if item['type'] in ('Folder', 'Open Folder'):
            children = explore_folder(item['id'], 'Top Level')
            item['children'] = children
        elif item['type'] not in SKIP_TYPES:
            process_item(item, 'Top Level')

    # Process each module
    for mod in top_modules:
        # Navigate back to outline
        page.goto(f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline",
                  wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        scroll_panel(page)
        scroll_panel_to_top(page)

        print(f"\n--- {mod['title']} ---")
        toggle_item(page, mod['id'])
        scroll_down(page, 8)

        children = get_direct_children(page, mod['id'])
        processed = []

        for child in children:
            print(f"  [{child['type']}] {child['title']}")
            child_data = dict(child)

            if child['type'] in ('Folder', 'Open Folder'):
                folder_children = explore_folder(child['id'], mod['title'])
                child_data['children'] = folder_children
            elif child['type'] not in SKIP_TYPES:
                process_item(child, mod['title'])

            processed.append(child_data)

        course_structure[mod['title']] = processed

        if not remaining:
            print(f"\n  All target files downloaded!")
            break

    # Save course structure
    structure_file = f"course_structure_{course_name}.json"
    save_json(course_structure, structure_file)
    print(f"\nCourse structure saved to: data/{structure_file}")

    return downloaded, failed, remaining


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('course', help='Course key (e.g., ITEC552) or known course name')
    parser.add_argument('course_id', nargs='?', help='Blackboard course ID (e.g., _1234567_1)')
    args = parser.parse_args()

    course_key = args.course.upper()

    if course_key in COURSES and not args.course_id:
        info = COURSES[course_key]
        course_id = info['id']
        report_file = info['report']
        course_dir = info['dir']
    elif args.course_id:
        # New course
        course_id = args.course_id
        report_file = f"accessibility_report_{course_key}.json"
        course_dir = f"{course_key}-001-FALL-2025"
    else:
        print(f"Unknown course '{course_key}'. Provide course_id as second argument.")
        print(f"Known courses: {list(COURSES.keys())}")
        sys.exit(1)

    p, browser, page = connect()
    print(f"Connected. URL: {page.url}")

    # Auto-scrape report if it doesn't exist
    if not os.path.exists(os.path.join(DATA_DIR, report_file)):
        print(f"Report not found. Scraping accessibility report for {course_key}...")
        items = scrape_accessibility_report(page, course_id)
        if items:
            save_json(items, report_file)
            print(f"Saved {len(items)} items to data/{report_file}")
        else:
            print(f"ERROR: Could not scrape report for course {course_id}")
            disconnect(p, browser)
            sys.exit(1)

    dl, fl, rem = process_course(course_key, course_id, report_file, course_dir, browser, page)

    print(f"\n{'='*50}")
    print(f"  {course_key} FINAL RESULTS")
    print(f"{'='*50}")
    print(f"  Downloaded/exists: {len(dl)}")
    print(f"  Failed:            {len(fl)}")
    if rem:
        print(f"  Not found:         {len(rem)}")
        for r in sorted(rem):
            print(f"    - {r}")
    for f in fl:
        print(f"    [FAIL] {f['file']} - {f['reason']}")

    with open(os.path.join(DATA_DIR, "download_results.json"), 'w') as f:
        json.dump({course_key: {'downloaded': dl, 'failed': fl, 'remaining': list(rem)}}, f, indent=2)

    disconnect(p, browser)
    print("\nDone!")
