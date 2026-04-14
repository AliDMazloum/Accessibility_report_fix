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

    Looks for files that have a corresponding backup_* file — meaning they've been fixed.
    Also supports legacy _fixed.* naming from previous runs.
    """
    course = get_course(course_key)
    course_dir = os.path.join(COURSE_DIR, course['dir'])

    index = {}  # report_name -> fixed_path
    for root, dirs, files in os.walk(course_dir):
        for fname in files:
            fpath = os.path.join(root, fname)

            # New naming: file has a backup_* counterpart
            if not fname.startswith('backup_') and ('backup_' + fname) in files:
                # This file has been fixed (backup exists)
                if fname not in index:
                    index[fname] = fpath
                # Also map .ppt/.doc names for converted files
                stem = os.path.splitext(fname)[0]
                ext = os.path.splitext(fname)[1].lower()
                if ext == '.pptx':
                    index[stem + '.ppt'] = fpath
                elif ext == '.docx':
                    index[stem + '.doc'] = fpath

            # Legacy naming: _fixed.* files from previous runs
            elif '_fixed.' in fname:
                base = fname.replace('_fixed.', '.')
                stem = os.path.splitext(base)[0]
                ext = os.path.splitext(fname)[1].lower()

                if base not in index:
                    index[base] = fpath
                if fname not in index:
                    index[fname] = fpath
                if ext == '.pptx' and (stem + '.ppt') not in index:
                    index[stem + '.ppt'] = fpath
                elif ext == '.docx' and (stem + '.doc') not in index:
                    index[stem + '.doc'] = fpath

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
    # Wait proportional to file size
    file_size = os.path.getsize(fixed_path) if fixed_path and os.path.exists(fixed_path) else 500_000
    if file_size < 500_000:
        wait = 10
    elif file_size < 2_000_000:
        wait = 15
    else:
        wait = 20
    disconnect(p, browser)
    time.sleep(wait)

    # Step 2: Reconnect, find feedback, upload file
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        # Try waiting longer — feedback may still be loading
        disconnect(p, browser)
        time.sleep(5)
        p, browser, page = connect()
        fb_page = find_feedback_page(browser)

    if not fb_page:
        disconnect(p, browser)
        return 'error: feedback window not found'

    # Wait for feedback content to fully load
    time.sleep(3)

    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        # Try waiting and checking again
        time.sleep(3)
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


def download_and_fix_from_feedback(item_name, course_key):
    """Click item, download from feedback, fix locally. Returns fixed_path or None."""
    import subprocess

    course = get_course(course_key)
    download_dir = os.path.join(COURSE_DIR, course['dir'], '_downloads')
    os.makedirs(download_dir, exist_ok=True)

    LIBREOFFICE = "C:/Program Files/LibreOffice/program/soffice.exe"

    # Step 1: Click item to open feedback
    p, browser, page = connect()
    report_page = get_report_page(browser)
    items_frame = find_items_frame(report_page)
    if not items_frame:
        disconnect(p, browser)
        return None

    clicked = click_item_by_name(items_frame, item_name)
    if not clicked:
        disconnect(p, browser)
        return None

    disconnect(p, browser)
    time.sleep(5)

    # Step 2: Download from feedback
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        disconnect(p, browser)
        return None

    # Set download dir
    try:
        cdp_session = fb_page.context.new_cdp_session(fb_page)
        cdp_session.send('Browser.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': os.path.abspath(download_dir).replace('/', os.sep)
        })
    except:
        pass

    # Click download button
    fb_frame = find_feedback_frame(fb_page)
    try:
        fb_frame.evaluate("""() => {
            const links = document.querySelectorAll('a, button');
            for (const el of links) {
                const text = el.innerText.trim().toLowerCase();
                if (text.includes('download original')) { el.click(); return true; }
            }
            return false;
        }""")
    except:
        pass

    # Close feedback and disconnect — let Chrome download freely
    fb_page.close()
    disconnect(p, browser)
    time.sleep(15)

    # Find the downloaded file — check target dir first, then default Downloads folder
    downloaded_path = None
    search_dirs = [download_dir, os.path.expanduser('~/Downloads')]
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.endswith('.crdownload') or f.endswith('.tmp'):
                continue
            fpath = os.path.join(search_dir, f)
            # Check if it's a new file (modified in last 30 seconds)
            if os.path.getmtime(fpath) > time.time() - 30:
                # Move to target dir if it's in default Downloads
                if search_dir != download_dir:
                    import shutil
                    target = os.path.join(download_dir, f)
                    shutil.move(fpath, target)
                    fpath = target
                downloaded_path = fpath
                break
        if downloaded_path:
            break

    if not downloaded_path:
        return None

    # Check file size — skip if too large
    size_mb = os.path.getsize(downloaded_path) / (1024 * 1024)
    max_size = 20 if os.path.splitext(downloaded_path)[1].lower() in ('.pptx', '.ppt', '.docx', '.doc') else 5
    if size_mb > max_size:
        print(f"    Skipping: too large ({size_mb:.1f} MB)", flush=True)
        return None

    # Step 3: Fix the file
    ext = os.path.splitext(downloaded_path)[1].lower()
    stem = os.path.splitext(os.path.basename(downloaded_path))[0]

    # Convert old formats
    working_path = downloaded_path
    if ext in ('.doc', '.ppt'):
        new_ext = '.docx' if ext == '.doc' else '.pptx'
        converted = os.path.join(download_dir, stem + new_ext)
        if not os.path.exists(converted):
            try:
                subprocess.run([LIBREOFFICE, '--headless', '--convert-to', new_ext[1:],
                               '--outdir', download_dir, downloaded_path],
                              capture_output=True, timeout=60)
            except:
                pass
        if os.path.exists(converted):
            working_path = converted
            ext = new_ext
            stem = os.path.splitext(os.path.basename(working_path))[0]

    # Backup original, fix writes to original name
    import shutil
    backup_path = os.path.join(download_dir, 'backup_' + os.path.basename(working_path))
    if not os.path.exists(backup_path):
        shutil.copy2(working_path, backup_path)
    fixed_path = working_path  # Fixed file keeps the original name

    try:
        if ext == '.pdf':
            from fix_pdf import fix_pdf
            from add_headings import add_headings_to_pdf
            fix_pdf(backup_path, fixed_path)
            try:
                add_headings_to_pdf(fixed_path, fixed_path)
            except:
                pass
        elif ext == '.docx':
            from fix_office import fix_docx
            fix_docx(backup_path, fixed_path)
        elif ext == '.pptx':
            from fix_office import fix_pptx
            fix_pptx(backup_path, fixed_path)
    except Exception as e:
        print(f"    Fix error: {e}")

    if os.path.exists(fixed_path):
        return fixed_path
    return None


def upload_all(course_key):
    """Upload all fixed files by iterating through report items."""
    course = get_course(course_key)
    course_id = course['id']

    # Build index of fixed files
    fixed_index = build_fixed_index(course_key)
    print(f"Phase 5: Uploading for {course_key}", flush=True)
    print(f"Fixed files available: {len(fixed_index)}", flush=True)

    # Check if report is already loaded, otherwise navigate
    p, browser, page = connect()
    report_page = get_report_page(browser)
    items_frame = find_items_frame(report_page) if report_page else None
    disconnect(p, browser)

    if items_frame:
        print("Report already loaded.", flush=True)
    else:
        print("Navigating to report...", flush=True)
        navigate_to_report_content(course_id, nav_wait=10, tab_wait=5)
        print("Report loaded.", flush=True)

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

        # Find first item below 85% that we haven't permanently skipped
        target = None
        for item in items:
            score_str = item['score'].replace('%', '')
            if score_str.isdigit() and int(score_str) >= 85:
                continue
            if item['name'] in skipped:
                continue

            name = item['name']
            ext = os.path.splitext(name)[1].lower()

            # Skip Ultra documents (can't fix)
            if item.get('type', '') == 'Ultra document' or not ext:
                skipped.add(name)
                continue

            # Check if we have a fixed file
            fixed_path = fixed_index.get(name)

            # Try without (N) suffix
            if not fixed_path:
                clean = re.sub(r'\(\d+\)(?=\.\w+$)', '', name).strip()
                fixed_path = fixed_index.get(clean)

            if fixed_path and os.path.exists(fixed_path):
                target = (name, item['score'], fixed_path)
                break
            else:
                # No fix available — try to download from feedback
                target = (name, item['score'], None)
                break

        if not target:
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

        # If no fixed file, try download-fix-upload from feedback
        if not fixed_path:
            print(f"\n  {name} ({score}) — no fix, attempting download from feedback...")
            close_feedback_windows()
            fixed_path = download_and_fix_from_feedback(name, course_key)
            if not fixed_path:
                print(f"    -> download/fix failed, skipping")
                skipped.add(name)
                results.append({'report_name': name, 'status': 'download failed'})
                reload_report_content(reload_wait=5, tab_wait=5)
                continue
            # Add to index for future
            fixed_index[name] = fixed_path
            print(f"    -> fixed: {os.path.basename(fixed_path)}")

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
