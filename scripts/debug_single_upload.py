"""Debug script: upload a single item with detailed step-by-step output.

Usage: python debug_single_upload.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from bb_utils import (connect, disconnect, find_items_frame, find_feedback_page,
                      find_feedback_frame, click_item_by_name, close_feedback_windows,
                      get_page_items)
from phase5_upload import build_fixed_index, get_report_page, download_and_fix_from_feedback

ITEM_NAME = "Lecture 1 - Introduction to EtherChannel_fixed.pptx"
COURSE_KEY = "ITEC445F"


def step(n, msg):
    print(f"\n[STEP {n}] {msg}", flush=True)


# ── Step 1: Build fixed index, look up the item ──────────────────────────
step(1, f"Building fixed index for {COURSE_KEY}")
index = build_fixed_index(COURSE_KEY)
print(f"  Total entries: {len(index)}")
fixed_path = index.get(ITEM_NAME)
print(f"  Lookup '{ITEM_NAME}': {fixed_path}")

if fixed_path:
    print(f"  File exists: {os.path.exists(fixed_path)}")
    if os.path.exists(fixed_path):
        print(f"  File size: {os.path.getsize(fixed_path):,} bytes")

# ── Step 2: Connect to Chrome, find report page ──────────────────────────
step(2, "Connecting to Chrome")
p, browser, page = connect()
print(f"  Total tabs: {len(browser.contexts[0].pages)}")
for i, pg in enumerate(browser.contexts[0].pages):
    print(f"    [{i}] {pg.url[:90]}")

step(3, "Finding report page")
report_page = get_report_page(browser)
print(f"  Report page found: {report_page is not None}")
if report_page:
    print(f"  URL: {report_page.url[:100]}")

# ── Step 3: Find items frame ─────────────────────────────────────────────
step(4, "Finding items frame")
items_frame = find_items_frame(report_page)
print(f"  Items frame found: {items_frame is not None}")

if items_frame:
    items = get_page_items(items_frame)
    print(f"  Items on page: {len(items)}")
    target_item = None
    for item in items:
        if item['name'] == ITEM_NAME:
            target_item = item
            print(f"  TARGET FOUND: {item}")
            break
    if not target_item:
        print(f"  TARGET NOT FOUND on this page. First 5 items:")
        for item in items[:5]:
            print(f"    {item['score']}  {item['name']}")
        disconnect(p, browser)
        sys.exit(1)

# ── Step 4: Click the item ───────────────────────────────────────────────
step(5, "Clicking the item")
pages_before = len(browser.contexts[0].pages)
clicked = click_item_by_name(items_frame, ITEM_NAME)
print(f"  Clicked: {clicked}")
print(f"  Tabs before: {pages_before}")

# Disconnect to let feedback open
disconnect(p, browser)
print(f"  Disconnected.")

step(6, "Waiting 10s for feedback window to open")
time.sleep(10)

# ── Step 5: Reconnect, find feedback ─────────────────────────────────────
step(7, "Reconnecting to find feedback window")
p, browser, page = connect()
print(f"  Total tabs: {len(browser.contexts[0].pages)}")
for i, pg in enumerate(browser.contexts[0].pages):
    print(f"    [{i}] {pg.url[:90]}")

fb_page = find_feedback_page(browser)
print(f"  Feedback page found: {fb_page is not None}")
if fb_page:
    print(f"  Feedback URL: {fb_page.url[:100]}")

# ── Step 6: Determine action based on whether we have a fix ──────────────
if fixed_path and os.path.exists(fixed_path):
    step(8, f"Have fixed file → uploading {os.path.basename(fixed_path)}")
    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    if not file_input:
        file_input = fb_page.query_selector('input[type="file"]')
    print(f"  File input found: {file_input is not None}")

    if file_input:
        file_input.set_input_files(os.path.abspath(fixed_path))
        print(f"  File set: {fixed_path}")
        print(f"  Disconnecting and waiting 20s for upload...")
        disconnect(p, browser)
        time.sleep(20)
    else:
        print("  ERROR: Could not find file input")
        disconnect(p, browser)
        sys.exit(1)

else:
    step(8, "No fixed file → downloading from feedback, fixing, then uploading")
    print("  Closing this connection...")
    disconnect(p, browser)
    fixed_path = download_and_fix_from_feedback(ITEM_NAME, COURSE_KEY)
    print(f"  Download/fix result: {fixed_path}")
    if not fixed_path:
        print("  Failed to download/fix")
        sys.exit(1)

    # Now reopen and upload
    print("  Re-clicking item to upload...")
    p, browser, page = connect()
    report_page = get_report_page(browser)
    items_frame = find_items_frame(report_page)
    click_item_by_name(items_frame, ITEM_NAME)
    disconnect(p, browser)
    time.sleep(10)

    p, browser, page = connect()
    fb_page = find_feedback_page(browser)
    fb_frame = find_feedback_frame(fb_page)
    file_input = fb_frame.query_selector('input[type="file"]')
    file_input.set_input_files(os.path.abspath(fixed_path))
    print(f"  Uploaded: {fixed_path}")
    disconnect(p, browser)
    time.sleep(20)

# ── Step 7: Verify and close ─────────────────────────────────────────────
step(9, "Reconnecting to close feedback window")
p, browser, page = connect()
fb_page = find_feedback_page(browser)
if fb_page:
    print(f"  Closing feedback: {fb_page.url[:80]}")
    fb_page.close()
disconnect(p, browser)

print("\n=== DONE ===")
