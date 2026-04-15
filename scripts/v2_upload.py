"""Version 2 workflow, step 4: upload every fixed file via the report.

Reads data/v2_fixed_<COURSE>.json. Maintains a sticky page pointer so the
loop does not re-scan earlier pages. Only advances to the next page when
every below-85% item on the current page is either uploaded or skipped.

Usage:
    python scripts/v2_upload.py <course_key>
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect,
                      navigate_to_report_content, reload_report_content,
                      find_items_frame, get_page_items, click_next_page,
                      close_feedback_windows, DATA_DIR, COURSE_DIR)
from phase5_upload import upload_item, get_report_page


def cleanup_extracted_images(course_key):
    """Remove all _imgs_* directories under the course's content folder
    and any per-course alt-task staging folders under data/.

    Called at the end of v2_upload once the course has been processed.
    Keeps backup_* files and fixed documents in place for reference.
    """
    import shutil, stat
    course = get_course(course_key)
    course_dir = os.path.join(COURSE_DIR, course['dir'])

    def _rm_readonly(func, path, _exc):
        """onexc handler: clear read-only flag (common on OneDrive-synced files) and retry."""
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    def _safe_rmtree(path):
        try:
            shutil.rmtree(path, onerror=_rm_readonly)
            return not os.path.exists(path)
        except Exception:
            return False

    removed = 0
    total_bytes = 0
    if os.path.exists(course_dir):
        for root, dirs, _files in os.walk(course_dir):
            for d in list(dirs):
                if d.startswith('_imgs_'):
                    path = os.path.join(root, d)
                    try:
                        size = sum(os.path.getsize(os.path.join(r, fn))
                                   for r, _, fs in os.walk(path) for fn in fs)
                    except Exception:
                        size = 0
                    if _safe_rmtree(path):
                        removed += 1
                        total_bytes += size
                        dirs.remove(d)
                    else:
                        print(f"  WARN: could not remove {path}", flush=True)

    # Also clean per-course alt-task staging dirs under data/
    for name in (f'v2_alt_tasks_{course_key}', f'alt_tasks_{course_key}',
                 f'alt_tasks_phase5_{course_key}'):
        staging = os.path.join(DATA_DIR, name)
        if os.path.isdir(staging):
            if _safe_rmtree(staging):
                print(f"  Removed staging dir: {staging}", flush=True)
            else:
                print(f"  WARN: could not remove {staging}", flush=True)

    print(f"\nCleanup: removed {removed} _imgs_* directories ({total_bytes/1024/1024:.1f} MB freed).", flush=True)


def goto_page(items_frame, target_page):
    for _ in range(target_page - 1):
        if not click_next_page(items_frame):
            return False
        time.sleep(1)
    return True


def upload_all(course_key):
    src = os.path.join(DATA_DIR, f'v2_fixed_{course_key}.json')
    if not os.path.exists(src):
        print(f"Missing: {src}. Run v2_fix first.")
        sys.exit(1)

    with open(src, encoding='utf-8') as f:
        fixed_entries = json.load(f)

    # Lookup by report_name for O(1) match during pagination.
    lookup = {e['report_name']: e for e in fixed_entries if e.get('fixed_path')}
    print(f"v2 Upload: {len(lookup)} pending uploads", flush=True)

    course = get_course(course_key)
    course_id = course['id']

    # Reset to page 1 of Content tab.
    p, browser, page = connect()
    report_page = get_report_page(browser)
    disconnect(p, browser)
    if report_page:
        reload_report_content(reload_wait=10, tab_wait=5)
    else:
        navigate_to_report_content(course_id, nav_wait=10, tab_wait=5)

    current_page = 1
    attempted = set()  # names already tried this run

    while True:
        # Jump to current_page.
        p, browser, page = connect()
        report_page = get_report_page(browser)
        items_frame = find_items_frame(report_page) if report_page else None
        if not items_frame:
            print("ERROR: items frame not found", flush=True)
            disconnect(p, browser)
            break
        if current_page > 1:
            if not goto_page(items_frame, current_page):
                print(f"Could not reach page {current_page}; stopping.", flush=True)
                disconnect(p, browser)
                break
        items = get_page_items(items_frame)
        disconnect(p, browser)

        if not items:
            print(f"Page {current_page} is empty; stopping.", flush=True)
            break

        # Find candidate: below 85%, in lookup, not attempted.
        target = None
        reached_threshold = False
        for item in items:
            score_str = item['score'].replace('%', '')
            if score_str.isdigit() and int(score_str) >= 85:
                reached_threshold = True
                break
            if item['name'] in attempted:
                continue
            entry = lookup.get(item['name'])
            if not entry:
                continue
            target = (item['name'], item['score'], entry)
            break

        if reached_threshold:
            print(f"\nPage {current_page}: reached >= 85% item; done.", flush=True)
            break
        if not target:
            # Current page has no more upload candidates; advance.
            print(f"\nPage {current_page} done; advancing to page {current_page + 1}.", flush=True)
            current_page += 1
            continue

        name, score, entry = target
        fixed_path = entry['fixed_path']
        print(f"\n[page {current_page}] {name} ({score}) -> {os.path.basename(fixed_path)}", flush=True)

        close_feedback_windows()
        status = upload_item(name, fixed_path)
        attempted.add(name)
        entry['upload_status'] = status
        entry['uploaded'] = 'uploaded' in status
        print(f"  -> {status}", flush=True)

        # Persist progress after every attempt.
        with open(src, 'w', encoding='utf-8') as f:
            json.dump(fixed_entries, f, indent=2)

        close_feedback_windows()
        if 'uploaded' in status:
            # Report re-sorts after upload; reload resets us to page 1 but we
            # loop back and jump to current_page again.
            reload_report_content(reload_wait=5, tab_wait=5)

    uploaded_count = sum(1 for e in fixed_entries if e.get('uploaded'))
    skipped = [e for e in fixed_entries if e.get('fixed_path') and not e.get('uploaded')
               and e['report_name'] in attempted]
    out_path = os.path.join(DATA_DIR, f'v2_upload_results_{course_key}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_entries, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  v2 Upload Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Uploaded:   {uploaded_count}")
    print(f"  Skipped:    {len(skipped)}")
    print(f"  Saved:      {out_path}")

    # Clean up extracted image directories now that the course is done.
    cleanup_extracted_images(course_key)


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python v2_upload.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)
    upload_all(sys.argv[1].upper())


if __name__ == '__main__':
    main()
