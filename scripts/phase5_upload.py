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
import sys, os, time, re, json, argparse
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect, load_json, save_json,
                      navigate_to_report_content, reload_report_content,
                      find_items_frame, find_feedback_page, find_feedback_frame,
                      close_feedback_windows, click_item_by_name,
                      get_page_items, fix_manifest_filename, COURSE_DIR, BASE_DIR,
                      DATA_DIR)

# Project-wide download landing dir — must match Chrome's configured default
# (set by scripts/launch_chrome.py). We move files out of here into the course
# folder after download completes.
CHROME_DOWNLOAD_DIR = os.path.join(BASE_DIR, "_downloads")


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
    """Find the report page (the one with the LTI launch URL).
    Returns None if no LTI/report tab is open — caller must then navigate."""
    for pg in browser.contexts[0].pages:
        if 'launchFrame' in pg.url or 'lti' in pg.url.lower():
            return pg
    # Also accept a page that actually has the report items frame
    for pg in browser.contexts[0].pages:
        try:
            for f in pg.frames:
                if f.evaluate('() => document.querySelectorAll("tr.ir-list-item").length') > 0:
                    return pg
        except:
            pass
    return None


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
    elif file_size < 5_000_000:
        wait = 40
    else:
        wait = 55
    time.sleep(wait)

    # Reconnect only to close feedback window
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if fb_page:
        fb_page.close()
    disconnect(p, browser)

    return 'uploaded'


def download_only_from_feedback(item_name, course_key):
    """Click report item, download via Ally feedback, save to disk. NO fix/extract.

    Returns saved file path or None. Used by Stage 1 of the new two-stage Phase 5
    flow: collect downloads first, fix in stage 2, upload in stage 3.
    """
    course = get_course(course_key)
    course_download_dir = os.path.join(COURSE_DIR, course['dir'], '_downloads')
    os.makedirs(course_download_dir, exist_ok=True)
    os.makedirs(CHROME_DOWNLOAD_DIR, exist_ok=True)

    # Step 1: Click item to open feedback window (disconnect/reconnect; clicking
    # while connected can be slow).
    print(f"    [dl] Clicking item...", flush=True)
    p, browser, page = connect()
    report_page = get_report_page(browser)
    items_frame = find_items_frame(report_page)
    if not items_frame:
        print(f"    [dl] FAIL: items frame not found", flush=True)
        disconnect(p, browser)
        return None

    clicked = click_item_by_name(items_frame, item_name)
    if not clicked:
        print(f"    [dl] FAIL: item '{item_name}' not clickable", flush=True)
        disconnect(p, browser)
        return None

    disconnect(p, browser)
    time.sleep(5)

    # Step 2: Reconnect, find feedback window, and use expect_download() — this binds
    # the download event to OUR specific click, so stray files from other downloads or
    # manual Save-As dialogs can't contaminate our result.
    print(f"    [dl] Finding feedback window...", flush=True)
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        print(f"    [dl] FAIL: feedback window not found after 5s", flush=True)
        disconnect(p, browser)
        return None

    download = None
    try:
        with fb_page.expect_download(timeout=120000) as dl_info:
            # Poll for the "Download original" button across all frames (feedback loads lazily)
            clicked_download = False
            poll_deadline = time.time() + 30
            while time.time() < poll_deadline and not clicked_download:
                for frame in fb_page.frames:
                    try:
                        found = frame.evaluate("""() => {
                            const els = document.querySelectorAll('a, button');
                            for (const el of els) {
                                const text = el.innerText.trim().toLowerCase();
                                if (/download\\s+(the\\s+)?original/.test(text)) { el.click(); return true; }
                            }
                            return false;
                        }""")
                        if found:
                            clicked_download = True
                            break
                    except Exception:
                        pass
                if not clicked_download:
                    time.sleep(1)
            if not clicked_download:
                # Raise so expect_download exits its wait immediately instead of hitting its own timeout
                raise RuntimeError("download button not found in any frame within 30s")
            print(f"    [dl] Download button clicked, waiting for download event...", flush=True)
        download = dl_info.value
    except Exception as e:
        print(f"    [dl] FAIL: {e}", flush=True)
        try: fb_page.close()
        except: pass
        disconnect(p, browser)
        return None

    # Step 3: Save download to course _downloads with the suggested filename.
    # suggested_filename comes from server's Content-Disposition. If missing/UUID-ish,
    # fall back to using item_name.
    suggested = download.suggested_filename or ''
    # Detect if it's a useless UUID.tmp style name and replace with item_name
    import re as _re
    if (_re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.tmp',
                      suggested.lower()) or not suggested):
        suggested = item_name  # use the report-visible name

    downloaded_path = os.path.join(course_download_dir, suggested)
    try:
        download.save_as(downloaded_path)
    except Exception as e:
        print(f"    [dl] FAIL: save_as error: {e}", flush=True)
        try: fb_page.close()
        except: pass
        disconnect(p, browser)
        return None

    # Close feedback window
    try: fb_page.close()
    except: pass
    disconnect(p, browser)

    # If filename didn't carry an extension, detect by magic bytes and rename
    cur_ext = os.path.splitext(downloaded_path)[1].lower()
    if cur_ext not in ('.pdf', '.pptx', '.ppt', '.docx', '.doc'):
        def detect_ext(path):
            with open(path, 'rb') as f:
                head = f.read(8)
            if head.startswith(b'%PDF-'):
                return '.pdf'
            if head.startswith(b'PK\x03\x04'):
                import zipfile
                try:
                    with zipfile.ZipFile(path) as zf:
                        names = zf.namelist()
                        if any(n.startswith('ppt/') for n in names): return '.pptx'
                        if any(n.startswith('word/') for n in names): return '.docx'
                except Exception:
                    pass
            if head[:4] == b'\xd0\xcf\x11\xe0':
                return '.ppt'  # OLE2 — could be .doc or .ppt; .ppt more common here
            return None
        detected = detect_ext(downloaded_path)
        if detected:
            new_path = os.path.splitext(downloaded_path)[0] + detected
            try:
                os.rename(downloaded_path, new_path)
                downloaded_path = new_path
                print(f"    [dl] Renamed by magic bytes: {os.path.basename(downloaded_path)}", flush=True)
            except Exception as e:
                print(f"    [dl] WARN: rename to {detected} failed ({e})", flush=True)

    print(f"    [dl] Saved: {os.path.basename(downloaded_path)} ({os.path.getsize(downloaded_path):,} bytes)", flush=True)
    return downloaded_path


def fix_pending_downloads(pending, course_key):
    """Stage 2: apply Phase 4 deterministic fixes to each pending download.

    Mutates each entry to add 'fixed_path', 'images_need_alt', 'images_detail',
    and 'fix_skipped_reason' if the fix failed. Returns aggregated images list.
    """
    from phase4_fix import fix_single_file
    print(f"\nStage 2: fixing {len(pending)} downloaded files...", flush=True)
    all_images = []
    for entry in pending:
        if entry.get('uploaded'):
            continue  # Already handled in a previous run
        fpath = entry.get('downloaded_path')
        if not fpath or not os.path.exists(fpath):
            entry['fix_skipped_reason'] = 'downloaded file missing'
            print(f"  SKIP {entry['report_name']}: file missing", flush=True)
            continue
        download_entry = {'report_name': entry['report_name']}
        result = fix_single_file(fpath, download_entry)
        if result.get('skipped_reason'):
            entry['fix_skipped_reason'] = result['skipped_reason']
            print(f"  SKIP {entry['report_name']}: {result['skipped_reason']}", flush=True)
            continue
        entry['fixed_path'] = result.get('fixed_path')
        entry['images_need_alt'] = result.get('images_need_alt', 0)
        fixes_str = ', '.join(result.get('fixes', [])) or 'none needed'
        print(f"  FIXED {entry['report_name']}: {fixes_str}; images={entry['images_need_alt']}", flush=True)
        if result.get('images_detail'):
            all_images.append({
                'report_name': result['report_name'],
                'fixed_path': entry['fixed_path'],
                'images': result['images_detail'],
            })
    return all_images


def upload_pending(course_key):
    """Stage 3: re-navigate the report and upload each pending fixed file."""
    pending_path = os.path.join(DATA_DIR, f'phase5_pending_{course_key}.json')
    if not os.path.exists(pending_path):
        print(f"No pending file found: {pending_path}")
        return None

    with open(pending_path, encoding='utf-8') as f:
        pending = json.load(f)

    course = get_course(course_key)
    course_id = course['id']

    # Always reset to page 1 of the Content tab. Stage 1 may have left the report
    # on a deep page; stage 3 needs to start fresh so pagination finds every item.
    print("Resetting report to page 1...", flush=True)
    p, browser, page = connect()
    report_page = get_report_page(browser)
    disconnect(p, browser)
    if report_page:
        reload_report_content(reload_wait=10, tab_wait=5)
    else:
        navigate_to_report_content(course_id, nav_wait=10, tab_wait=5)

    print(f"\nStage 3: uploading {sum(1 for e in pending if not e.get('uploaded'))} pending files...", flush=True)
    uploaded_count = 0
    for entry in pending:
        if entry.get('uploaded'):
            continue
        name = entry['report_name']
        fixed_path = entry.get('fixed_path')
        if not fixed_path or not os.path.exists(fixed_path):
            entry['upload_status'] = 'fixed file missing'
            print(f"  SKIP {name}: fixed file missing", flush=True)
            continue
        # Search across pages for this item
        from bb_utils import click_next_page
        found_and_uploaded = False
        for page_attempt in range(20):
            close_feedback_windows()
            status = upload_item(name, fixed_path)
            if 'uploaded' in status:
                entry['uploaded'] = True
                entry['upload_status'] = status
                uploaded_count += 1
                print(f"  UPLOADED {name}", flush=True)
                close_feedback_windows()
                reload_report_content(reload_wait=5, tab_wait=5)
                found_and_uploaded = True
                break
            if status == 'not found':
                # Try next page
                p, browser, page = connect()
                report_page = get_report_page(browser)
                items_frame = find_items_frame(report_page) if report_page else None
                advanced = items_frame and click_next_page(items_frame)
                disconnect(p, browser)
                if not advanced:
                    break
                time.sleep(2)
                continue
            entry['upload_status'] = status
            print(f"  FAIL {name}: {status}", flush=True)
            break
        if not found_and_uploaded and 'upload_status' not in entry:
            entry['upload_status'] = 'not found in report'
            print(f"  NOT FOUND {name} after pagination", flush=True)
        # Persist progress after each item so re-runs are idempotent
        with open(pending_path, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=2)

    # Cleanup if everything uploaded
    remaining = [e for e in pending if not e.get('uploaded')]
    if not remaining:
        done_path = pending_path.replace('.json', '_done.json')
        os.replace(pending_path, done_path)
        print(f"\nAll uploaded. Pending file moved to {os.path.basename(done_path)}", flush=True)
    else:
        print(f"\n{uploaded_count} uploaded, {len(remaining)} still pending. Re-run --stage3 after fixing issues.", flush=True)

    return {'uploaded': uploaded_count, 'remaining': len(remaining), 'pending_path': pending_path}


def upload_all(course_key):
    """Upload all fixed files by iterating through report items."""
    course = get_course(course_key)
    course_id = course['id']

    # Build index of fixed files
    fixed_index = build_fixed_index(course_key)
    print(f"Phase 5: Uploading for {course_key}", flush=True)
    print(f"Fixed files available: {len(fixed_index)}", flush=True)

    # Check if report is already loaded with items, otherwise navigate/reload
    p, browser, page = connect()
    report_page = get_report_page(browser)
    items = []
    if report_page:
        items_frame = find_items_frame(report_page)
        if items_frame:
            items = get_page_items(items_frame)
    disconnect(p, browser)

    if items:
        print(f"Report already loaded with {len(items)} items.", flush=True)
    elif report_page:
        print("Report page exists but items empty, reloading...", flush=True)
        reload_report_content(reload_wait=10, tab_wait=5)
        print("Report reloaded.", flush=True)
    else:
        print("Navigating to report...", flush=True)
        navigate_to_report_content(course_id, nav_wait=10, tab_wait=5)
        print("Report loaded.", flush=True)

    results = []
    uploaded = 0
    skipped = set()
    pending_downloads = []  # Stage 1 collects download-fallback items here

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
            print("  No items on page — reloading report...", flush=True)
            reload_report_content(reload_wait=10, tab_wait=5)
            # Re-check
            p, browser, page = connect()
            report_page = get_report_page(browser)
            items_frame = find_items_frame(report_page) if report_page else None
            items = get_page_items(items_frame) if items_frame else []
            disconnect(p, browser)
            if not items:
                print("  Still no items after reload — stopping", flush=True)
                break

        # Find first non-skipped item. Since the report is sorted by score ascending,
        # if the first non-skipped item has score >= 85%, we're done with the entire run.
        target = None
        reached_threshold = False
        for item in items:
            if item['name'] in skipped:
                continue
            score_str = item['score'].replace('%', '')
            if score_str.isdigit() and int(score_str) >= 85:
                reached_threshold = True
                break

            name = item['name']
            ext = os.path.splitext(name)[1].lower()

            # Skip Ultra documents (can't fix)
            if item.get('type', '') == 'Ultra document' or not ext:
                skipped.add(name)
                continue

            # Check if we have a fixed file
            fixed_path = fixed_index.get(name)

            # Try without (N) suffix — also strips preceding whitespace
            if not fixed_path:
                clean = re.sub(r'\s*\(\d+\)(?=\.\w+$)', '', name).strip()
                fixed_path = fixed_index.get(clean)

            if fixed_path and os.path.exists(fixed_path):
                target = (name, item['score'], fixed_path)
                break
            else:
                # No fix available — try to download from feedback
                target = (name, item['score'], None)
                break

        if not target:
            if reached_threshold:
                print("\nReached an item with score >= 85% — done!")
                break
            # No candidates on this page AND haven't hit 85% threshold —
            # try advancing to next page.
            from bb_utils import click_next_page
            p, browser, page = connect()
            report_page = get_report_page(browser)
            items_frame = find_items_frame(report_page) if report_page else None
            advanced = items_frame and click_next_page(items_frame)
            disconnect(p, browser)
            if advanced:
                print("\nNo new candidates on this page — advanced to next page", flush=True)
                time.sleep(2)
                continue
            print("\nNo more candidates and no next page — done!")
            break

        name, score, fixed_path = target

        # If no fixed file, download only and queue for stage 2 (fix) + stage 3 (upload).
        # Don't fix or upload during stage 1; pending list is processed after the loop.
        if not fixed_path:
            print(f"\n  {name} ({score}) — not in fix index, downloading for stage 2...")
            close_feedback_windows()
            downloaded_path = download_only_from_feedback(name, course_key)
            skipped.add(name)
            if not downloaded_path:
                print(f"    -> download failed, skipping", flush=True)
                results.append({'report_name': name, 'status': 'download failed'})
                close_feedback_windows()
                reload_report_content(reload_wait=10, tab_wait=5)
                continue
            pending_downloads.append({
                'report_name': name,
                'score': score,
                'downloaded_path': downloaded_path.replace('\\', '/'),
                'uploaded': False,
            })
            results.append({'report_name': name, 'status': 'downloaded (pending stage 2/3)'})
            close_feedback_windows()
            reload_report_content(reload_wait=5, tab_wait=5)
            continue

        size = os.path.getsize(fixed_path)
        print(f"\n  {name} ({score}) -> {os.path.basename(fixed_path)} ({size:,} bytes)")

        # Close any leftover feedback windows and upload
        close_feedback_windows()
        status = upload_item(name, fixed_path)
        print(f"    -> {status}")

        # Mark every attempted item so we don't re-process it this run,
        # even if the score stays below 85% after upload.
        skipped.add(name)
        if 'uploaded' in status:
            uploaded += 1
            results.append({'report_name': name, 'status': status})
        elif status == 'not found':
            results.append({'report_name': name, 'status': 'not found'})
        else:
            results.append({'report_name': name, 'status': status})

        # Reload report
        close_feedback_windows()
        reload_report_content(reload_wait=5, tab_wait=5)

    return {
        'course': course_key,
        'uploaded': uploaded,
        'skipped': sorted(skipped),
        'results': results,
        'pending_downloads': pending_downloads,
    }


def run_stage2_and_persist(pending_downloads, course_key):
    """Run stage 2 (fix) on pending downloads, persist pending JSON + images JSON.
    Returns total images needing alt text across all docs."""
    if not pending_downloads:
        print("\nNo download-fallback items to fix. Stage 2 skipped.", flush=True)
        return 0

    all_images = fix_pending_downloads(pending_downloads, course_key)

    # Persist pending list with fix results
    pending_path = os.path.join(DATA_DIR, f'phase5_pending_{course_key}.json')
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(pending_path, 'w', encoding='utf-8') as f:
        json.dump(pending_downloads, f, indent=2)
    print(f"\nPending list saved: {pending_path}", flush=True)

    if all_images:
        imgs_path = os.path.join(DATA_DIR, f'images_needing_alt_phase5_{course_key}.json')
        with open(imgs_path, 'w', encoding='utf-8') as f:
            json.dump(all_images, f, indent=2)
        total_images = sum(len(e['images']) for e in all_images)
        print(f"Images needing alt text saved: {imgs_path} ({total_images} images across {len(all_images)} docs)", flush=True)
        return total_images
    return 0


def main():
    parser = argparse.ArgumentParser(description="Phase 5: upload fixed files to Blackboard Ally.")
    parser.add_argument('course_key', nargs='?', help='Course key from courses.json')
    parser.add_argument('--stage3', action='store_true',
                        help='Skip stages 1+2; only upload pending fixed files from data/phase5_pending_<COURSE>.json')
    args = parser.parse_args()

    if not args.course_key:
        from bb_utils import load_courses
        print("Usage: python phase5_upload.py <course_key> [--stage3]")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)

    course_key = args.course_key.upper()

    if args.stage3:
        upload_pending(course_key)
        return

    # Stages 1 + 2
    results = upload_all(course_key)

    filename = f"upload_results_{course_key}.json"
    # Strip pending_downloads from saved results (it's persisted separately)
    results_for_save = {k: v for k, v in results.items() if k != 'pending_downloads'}
    save_json(results_for_save, filename)
    print(f"\nSaved to data/{filename}")

    print(f"\n{'='*60}")
    print(f"  Phase 5 Stage 1 Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Uploaded (in fix index):       {results['uploaded']}")
    print(f"  Downloaded (pending stage 2):  {len(results['pending_downloads'])}")
    print(f"  Skipped:                       {len(results['skipped'])}")

    # Stage 2
    pending = results.get('pending_downloads', [])
    total_images = run_stage2_and_persist(pending, course_key)

    fixed_count = sum(1 for e in pending if e.get('fixed_path'))
    print(f"\n{'='*60}")
    print(f"  Phase 5 Stage 2 Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Files fixed:           {fixed_count}/{len(pending)}")
    print(f"  Images needing alt:    {total_images}")

    if total_images > 0:
        print(f"\nNext steps:")
        print(f"  1. Generate alt text JSONs (launch Claude Code subagents on data/images_needing_alt_phase5_{course_key}.json)")
        print(f"  2. python scripts/phase4b_apply_alts.py {course_key} data/alt_texts_phase5_{course_key}.json")
        print(f"  3. python scripts/phase5_upload.py {course_key} --stage3")
    elif fixed_count > 0:
        print(f"\nNo alt text needed. Auto-running stage 3...")
        upload_pending(course_key)
    else:
        print(f"\nNothing to upload in stage 3.")


if __name__ == '__main__':
    main()
