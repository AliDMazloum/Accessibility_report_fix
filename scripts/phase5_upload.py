"""Phase 5: Upload all fixed files back to Blackboard via accessibility report.

Reads the fix manifest, navigates to the report Content tab, and for each item:
1. Searches pages for the item by name
2. Clicks item to open feedback window (disconnect/reconnect)
3. Uploads the fixed file
4. Navigates back to report from scratch (full reload)

No download-on-the-fly fallback — only uploads what Phase 4 already fixed.

Requires: data/fix_manifest_{COURSE}.json from Phase 4.
Produces: data/upload_results_{COURSE}.json

Usage:
    python scripts/phase5_upload.py <course_key>
    python scripts/phase5_upload.py CYBERINFRA
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect, load_json, save_json,
                      navigate_to_report_content, find_items_frame,
                      find_feedback_page, find_feedback_frame,
                      close_feedback_windows, get_page_items, click_item_by_name,
                      click_next_page, fix_manifest_filename)


def find_and_click_item(item_name, max_pages=5):
    """Search across report pages for an item and click it.
    Returns True if found and clicked."""
    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        disconnect(p, browser)
        return False

    # Check current page
    if click_item_by_name(items_frame, item_name):
        disconnect(p, browser)
        return True

    # Check subsequent pages
    for _ in range(max_pages - 1):
        if not click_next_page(items_frame):
            break
        if click_item_by_name(items_frame, item_name):
            disconnect(p, browser)
            return True

    disconnect(p, browser)
    return False


def upload_single_item(course_id, item_name, fixed_path):
    """Upload a single fixed file for a report item.
    Returns 'uploaded', 'not found', or 'error: ...'."""

    close_feedback_windows()

    # Find and click the item
    if not find_and_click_item(item_name):
        return 'not found'

    # Disconnect to let feedback window load
    time.sleep(15)

    # Find feedback window and upload
    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    if not fb_page:
        disconnect(p, browser)
        return 'error: feedback window not found'

    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    if not file_input:
        fb_page.close()
        disconnect(p, browser)
        return 'error: no file input found'

    file_input.set_input_files(os.path.abspath(fixed_path))
    time.sleep(10)  # Wait for upload to register

    fb_page.close()
    disconnect(p, browser)
    return 'uploaded'


def upload_all(course_key):
    """Upload all fixed files for a course."""
    course = get_course(course_key)
    course_id = course['id']

    manifest = load_json(fix_manifest_filename(course_key))
    fixed_items = [f for f in manifest['fixed'] if f.get('fixed_path')]

    print(f"Phase 5: Uploading {len(fixed_items)} files for {course_key}")

    # Navigate to report content tab
    navigate_to_report_content(course_id)

    results = []
    uploaded = 0
    not_found = 0
    errors = 0

    for i, item in enumerate(fixed_items):
        report_name = item['report_name']
        fixed_path = item['fixed_path']

        if not os.path.exists(fixed_path):
            fixed_path = fixed_path.replace('/', '\\')
        if not os.path.exists(fixed_path):
            print(f"  [{i+1}/{len(fixed_items)}] SKIP: File missing: {fixed_path}")
            results.append({'report_name': report_name, 'status': 'file missing'})
            errors += 1
            continue

        size = os.path.getsize(fixed_path)
        print(f"  [{i+1}/{len(fixed_items)}] {report_name} ({size:,} bytes)")

        status = upload_single_item(course_id, report_name, fixed_path)

        if status == 'uploaded':
            print(f"    -> Uploaded")
            uploaded += 1
        elif status == 'not found':
            print(f"    -> Not found in report")
            not_found += 1
        else:
            print(f"    -> {status}")
            errors += 1

        results.append({'report_name': report_name, 'status': status})

        # Navigate back to report from scratch (not just reload)
        close_feedback_windows()
        navigate_to_report_content(course_id, nav_wait=5, tab_wait=5)

    return {
        'course': course_key,
        'total': len(fixed_items),
        'uploaded': uploaded,
        'not_found': not_found,
        'errors': errors,
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

    # Save results
    filename = f"upload_results_{course_key}.json"
    save_json(results, filename)
    print(f"\nSaved results to data/{filename}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Phase 5 Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Uploaded:  {results['uploaded']}/{results['total']}")
    print(f"  Not found: {results['not_found']}")
    print(f"  Errors:    {results['errors']}")

    if results['not_found'] > 0 or results['errors'] > 0:
        print(f"\n  Issues:")
        for r in results['results']:
            if r['status'] != 'uploaded':
                print(f"    - {r['report_name']}: {r['status']}")

    success_rate = results['uploaded'] / results['total'] * 100 if results['total'] > 0 else 0
    if success_rate == 100:
        print(f"\n  SUCCESS: All {results['total']} files uploaded (100%)")
    else:
        print(f"\n  WARNING: {success_rate:.0f}% uploaded — review issues above")


if __name__ == '__main__':
    main()
