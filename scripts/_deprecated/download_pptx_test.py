"""Download a .pptx file from ITEC493 Module 6 Slides.
Uses CDP to set auto-download directory, then clicks the Download SVG button
inside the file viewer iframe."""
import sys, os, time, glob
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, screenshot, dismiss_popup, COURSE_DIR

COURSE_ID = "_1308255_1"  # ITEC493
SAVE_DIR = os.path.join(COURSE_DIR, "ITEC493-001-FALL-2025", "Module 6")
os.makedirs(SAVE_DIR, exist_ok=True)

p, browser, page = connect()
print(f"Current URL: {page.url}")

# Use CDP to set automatic download directory (no Save As dialog)
cdp = browser.contexts[0].new_cdp_session(page)
cdp.send("Page.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": SAVE_DIR.replace("/", "\\")
})
print(f"Download directory set to: {SAVE_DIR}")

# Navigate to file view if needed
if '/file/_27111187_1' not in page.url:
    if COURSE_ID not in page.url:
        page.goto(f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
    dismiss_popup(page)
    page.goto(f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline/file/_27111187_1",
              wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)
dismiss_popup(page)

print(f"File page: {page.url}")

# Wait for the viewer frame to load with the Download button
viewer_frame = None
for attempt in range(15):
    for frame in page.frames:
        try:
            has_download = frame.evaluate("""() => {
                const btn = document.querySelector('button[aria-label="Download"]');
                return btn ? true : false;
            }""")
            if has_download:
                viewer_frame = frame
                break
        except:
            pass
    if viewer_frame:
        break
    time.sleep(1)

if not viewer_frame:
    print("ERROR: Could not find viewer frame with Download button!")
    screenshot(page, "no_download_btn")
    disconnect(p, browser)
    sys.exit(1)

print("Found Download button in viewer frame")

# Get file title
file_title = page.evaluate("""() => {
    const iframes = document.querySelectorAll('iframe');
    for (const f of iframes) {
        const title = f.getAttribute('title') || '';
        if (title.includes('.pptx') || title.includes('.pdf') || title.includes('.docx')) {
            return title;
        }
    }
    return 'downloaded_file';
}""")
print(f"File: {file_title}")

# Click the Download button
print("Clicking Download button...")
viewer_frame.click('button[aria-label="Download"]')

# Wait for download to complete (check for file appearing in directory)
save_path = os.path.join(SAVE_DIR, file_title)
print(f"Waiting for file: {save_path}")

for i in range(30):
    time.sleep(1)
    # Check for the file or any new .pptx/.crdownload files
    if os.path.exists(save_path):
        # Make sure it's not still downloading (.crdownload)
        crdownload = save_path + ".crdownload"
        if not os.path.exists(crdownload):
            break
    # Also check for file with different name
    new_files = glob.glob(os.path.join(SAVE_DIR, "*.pptx"))
    if new_files:
        save_path = new_files[0]
        break
else:
    print("WARNING: Timed out waiting for file")
    # List what's in the directory
    print(f"Files in {SAVE_DIR}:")
    for f in os.listdir(SAVE_DIR):
        print(f"  {f}")

if os.path.exists(save_path):
    file_size = os.path.getsize(save_path)
    print(f"\nSUCCESS!")
    print(f"  File: {save_path}")
    print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    with open(save_path, 'rb') as f:
        header = f.read(4)
    if header[:2] == b'PK':
        print("  Valid PPTX (PK/ZIP signature)")
    elif header[:4] == b'%PDF':
        print("  Got PDF format")
    else:
        print(f"  File header: {header!r}")
else:
    print(f"\nFAILED: File not found at {save_path}")

disconnect(p, browser)
print("\nDone!")
