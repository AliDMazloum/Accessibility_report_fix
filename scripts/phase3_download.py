"""Phase 3: Download all target files from the course structure.

Navigates the course outline, expands modules/folders, identifies target files,
and downloads them. Disconnects/reconnects between modules to avoid timeout.

Requires: data/targets_{COURSE}.json from Phase 2.
Produces: data/download_manifest_{COURSE}.json + files in course_content/{dir}/

Usage:
    python scripts/phase3_download.py <course_key>
    python scripts/phase3_download.py CYBERINFRA
"""
import sys, os, time, re
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect, dismiss_popup,
                      scroll_panel, scroll_panel_to_top, load_json, save_json,
                      targets_filename, download_manifest_filename, COURSE_DIR)


# ── Helpers ───────────────────────────────────────────────────────────────

def setup_download_dir(browser, page, directory):
    """Set Chrome's download directory via CDP."""
    os.makedirs(directory, exist_ok=True)
    cdp = browser.contexts[0].new_cdp_session(page)
    cdp.send("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": os.path.abspath(directory).replace("/", os.sep),
    })


def wait_for_file(path, timeout=45):
    """Wait for a file to appear and finish downloading."""
    for _ in range(timeout):
        time.sleep(1)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            if not os.path.exists(path + ".crdownload"):
                return True
    return os.path.exists(path) and os.path.getsize(path) > 0


def get_file_from_iframe(page):
    """Check if a file is loaded in an iframe viewer (PDF/Presentation)."""
    return page.evaluate(r"""() => {
        for (const f of document.querySelectorAll('iframe')) {
            const t = f.getAttribute('title') || '';
            if (/\.(pdf|pptx?|docx?|xlsx?)$/i.test(t)) return t;
        }
        return null;
    }""")


def get_file_from_more_options(page):
    """Check for file in 'More options for' buttons."""
    return page.evaluate(r"""() => {
        for (const b of document.querySelectorAll('button')) {
            const label = b.getAttribute('aria-label') || '';
            const m = label.match(/^More options for (.+\.(?:pdf|pptx?|docx?|xlsx?))$/i);
            if (m) return m[1];
        }
        return null;
    }""")


def click_inner_content_link(page):
    """Click the inner link in a Text Document item."""
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
    """Click '...' menu then 'Download original file'."""
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
    """Click download button in PDF/presentation viewer."""
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


# ── Course Outline Navigation ─────────────────────────────────────────────

def get_all_items(page):
    """Get all visible items on the course outline page."""
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
    """Get items nested directly under a parent content item."""
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
    """Expand or collapse a content item (folder/module)."""
    page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (div) {
            div.scrollIntoView({behavior: 'instant', block: 'center'});
            const ct = div.querySelector('.click-to-invoke-container');
            if (ct) ct.click();
        }
    }""", cid)
    time.sleep(2)


def scroll_down(page, times=5):
    """Scroll the course panel down."""
    for _ in range(times):
        page.evaluate("() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }")
        time.sleep(0.3)


# ── File Download ─────────────────────────────────────────────────────────

SKIP_TYPES = {'Folder', 'Open Folder', 'Learning Module'}


def visit_and_download(page, browser, course_id, item_id, section_dir, targets, norm_lookup):
    """Navigate to a content item, check for target file, download if found.
    Returns (report_name, status) where status is 'downloaded', 'already exists',
    'not target', 'no file', or 'download failed'.
    """
    url = f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline/file/{item_id}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
    except:
        return None, "nav error"
    time.sleep(2)
    dismiss_popup(page)

    # Detect file: Method A (iframe viewer) or Method B (More options button)
    file_name = get_file_from_iframe(page)
    if not file_name:
        click_inner_content_link(page)
        time.sleep(3)
        file_name = get_file_from_more_options(page)

    if not file_name:
        return None, "no file"

    # Check if this file is a target
    target_names = {t['name'] for t in targets}
    report_name = file_name
    if file_name not in target_names:
        if norm_lookup and file_name in norm_lookup:
            report_name = norm_lookup[file_name]
        elif file_name not in target_names:
            return file_name, "not target"

    save_path = os.path.join(section_dir, file_name)

    # Already downloaded?
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return report_name, "already exists"

    # Set download directory
    setup_download_dir(browser, page, section_dir)

    # Try downloading: first via viewer, then via "..." menu
    downloaded = False

    if get_file_from_iframe(page):
        downloaded = download_via_viewer(page)
        if downloaded:
            downloaded = wait_for_file(save_path)

    if not downloaded:
        found = get_file_from_more_options(page)
        if not found:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
            except:
                return report_name, "re-nav error"
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
        size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
        return report_name, "downloaded"
    else:
        return report_name, "download failed"


# ── Main Download Logic ───────────────────────────────────────────────────

def download_all(course_key):
    """Download all target files from the course structure."""
    course = get_course(course_key)
    course_id = course['id']
    course_dir = os.path.join(COURSE_DIR, course['dir'])

    # Load targets
    targets_data = load_json(targets_filename(course_key))
    targets = targets_data['targets']
    norm_lookup = targets_data.get('norm_lookup', {})

    print(f"Phase 3: Downloading files for {course_key} ({course_id})")
    print(f"Targets: {len(targets)} files to download")

    # Connect and navigate to course outline
    p, browser, page = connect()
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

    print(f"Top-level items: {len(top_other)}, Modules: {len(top_modules)}")

    # Track results
    downloaded = []
    failed = []
    remaining = {t['name'] for t in targets}

    def process_item(item, section):
        """Visit a single item, try to download if it's a target."""
        nonlocal remaining
        if not remaining:
            return
        if item['type'] in SKIP_TYPES:
            return

        section_dir = os.path.join(course_dir, section.replace(':', ' -').replace('/', '-').strip())
        report_name, status = visit_and_download(
            page, browser, course_id, item['id'], section_dir, targets, norm_lookup
        )

        if report_name and status in ("downloaded", "already exists"):
            fpath = os.path.join(section_dir, report_name if '/' not in str(report_name) else os.path.basename(str(report_name)))
            # Find actual file path
            for f in os.listdir(section_dir):
                if f == report_name or f == os.path.basename(str(report_name)):
                    fpath = os.path.join(section_dir, f)
                    break
            size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
            print(f"      -> {status}: {report_name} ({size:,} bytes)")
            downloaded.append({
                'report_name': report_name,
                'local_path': os.path.normpath(fpath).replace('\\', '/'),
                'section': section,
                'status': status,
                'size': size,
            })
            remaining.discard(report_name)
        elif report_name and "failed" in status:
            print(f"      -> FAILED: {report_name} ({status})")
            failed.append({'report_name': report_name, 'reason': status})

    def explore_folder(folder_id, section, depth=0):
        """Expand folder, process children, collapse."""
        page.goto(f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline",
                  wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        scroll_panel(page)
        scroll_panel_to_top(page)

        toggle_item(page, folder_id)
        scroll_down(page, 3)
        time.sleep(1)
        children = get_direct_children(page, folder_id)

        indent = "  " * (depth + 2)
        for child in children:
            print(f"{indent}[{child['type']}] {child['title']}")
            if child['type'] in ('Folder', 'Open Folder'):
                explore_folder(child['id'], section, depth + 1)
            else:
                process_item(child, section)

        page.goto(f"https://blackboard.sc.edu/ultra/courses/{course_id}/outline",
                  wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        scroll_panel(page)

    # Process top-level non-module items
    print(f"\n--- Top-level items ---")
    for item in top_other:
        print(f"  [{item['type']}] {item['title']}")
        if item['type'] in ('Folder', 'Open Folder'):
            explore_folder(item['id'], 'Top Level')
        elif item['type'] not in SKIP_TYPES:
            process_item(item, 'Top Level')

    # Process each module
    for mod in top_modules:
        if not remaining:
            print(f"\n  All target files found!")
            break

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
        for child in children:
            print(f"  [{child['type']}] {child['title']}")
            if child['type'] in ('Folder', 'Open Folder'):
                explore_folder(child['id'], mod['title'])
            elif child['type'] not in SKIP_TYPES:
                process_item(child, mod['title'])

    disconnect(p, browser)

    # Build manifest
    manifest = {
        'course': course_key,
        'course_id': course_id,
        'target_count': len(targets),
        'downloaded_count': len(downloaded),
        'failed_count': len(failed),
        'not_found': sorted(remaining),
        'downloads': downloaded,
        'failed': failed,
    }

    return manifest


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python phase3_download.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)

    course_key = sys.argv[1].upper()
    manifest = download_all(course_key)

    # Save manifest
    filename = download_manifest_filename(course_key)
    save_json(manifest, filename)
    print(f"\nSaved manifest to data/{filename}")

    # Summary
    total = manifest['target_count']
    got = manifest['downloaded_count']
    fail = manifest['failed_count']
    missing = len(manifest['not_found'])

    print(f"\n{'='*60}")
    print(f"  Phase 3 Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Downloaded: {got}/{total}")
    print(f"  Failed:     {fail}")
    print(f"  Not found:  {missing}")

    if manifest['not_found']:
        print(f"\n  Missing files:")
        for name in manifest['not_found']:
            print(f"    - {name}")

    if manifest['failed']:
        print(f"\n  Failed downloads:")
        for f in manifest['failed']:
            print(f"    - {f['report_name']}: {f['reason']}")

    success_rate = got / total * 100 if total > 0 else 0
    if success_rate == 100:
        print(f"\n  SUCCESS: All {total} files downloaded (100%)")
    else:
        print(f"\n  WARNING: {success_rate:.0f}% downloaded — {total - got} files missing")
        print(f"  Fix issues before proceeding to Phase 4")


if __name__ == '__main__':
    main()
