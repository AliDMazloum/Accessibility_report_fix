"""Test downloading a single ITEC445 file.
Flow:
1. Navigate to wrapper -> click inner document name -> document view page
2. Read the file name from the visible text (e.g., 'Lecture 1 Troubleshooting Tools.pptx')
3. Click the chevron (aria-expanded button) to expand the file viewer
4. Set CDP download path, click Download button, wait for file
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, screenshot, dismiss_popup, COURSE_DIR

COURSE_ID = "_1328539_1"
SAVE_DIR = os.path.join(COURSE_DIR, "ITEC445-001-SPRING-2026", "test")
os.makedirs(SAVE_DIR, exist_ok=True)

TEST_ITEM_ID = "_27756737_1"  # Lecture 1: Troubleshooting Tools (Module 14)

p, browser, page = connect()

# Step 1: Navigate to wrapper, click inner link
page.goto(f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline/file/{TEST_ITEM_ID}",
          wait_until="domcontentloaded", timeout=20000)
time.sleep(4)
dismiss_popup(page)
print(f"Step 1: wrapper page")

# Click inner document name
page.evaluate("""() => {
    for (const a of document.querySelectorAll('a')) {
        const rect = a.getBoundingClientRect();
        if (rect.y > 170 && rect.y < 290 && a.innerText.trim().length > 3) {
            a.click(); return;
        }
    }
}""")
time.sleep(5)
dismiss_popup(page)
print(f"Step 2: document view - {page.url}")

# Step 3: Read file name from visible text
file_name = page.evaluate(r"""() => {
    const all = document.querySelectorAll('span, div, p, a');
    for (const el of all) {
        const t = el.innerText.trim();
        if (/\.(pdf|pptx?|docx?)$/i.test(t) && t.length < 200 && !t.includes('\n')) {
            return t;
        }
    }
    return null;
}""")
print(f"Step 3: file name = {file_name}")

if not file_name:
    print("No file name found")
    screenshot(page, "test_fail")
    disconnect(p, browser)
    sys.exit(1)

# Step 4: Click chevron to expand viewer
chevron_clicked = page.evaluate("""() => {
    // Look for button with aria-expanded attribute in the file item area
    for (const b of document.querySelectorAll('button[aria-expanded]')) {
        const rect = b.getBoundingClientRect();
        if (rect.y > 170 && rect.y < 270) {
            b.click();
            return true;
        }
    }
    return false;
}""")
print(f"Step 4: chevron clicked = {chevron_clicked}")
time.sleep(4)

# Step 5: Set CDP download path RIGHT BEFORE clicking Download
cdp = browser.contexts[0].new_cdp_session(page)
cdp.send("Page.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": os.path.abspath(SAVE_DIR).replace("/", os.sep)
})

# Step 6: Find and click Download button
viewer = None
for _ in range(10):
    for frame in page.frames:
        try:
            if frame.evaluate('() => !!document.querySelector(\'button[aria-label="Download"]\')'):
                viewer = frame
                break
        except:
            pass
    if viewer:
        break
    time.sleep(1)

if not viewer:
    print("No Download button found")
    screenshot(page, "test_no_dl")
    disconnect(p, browser)
    sys.exit(1)

print("Step 6: Download button found, clicking...")
viewer.click('button[aria-label="Download"]')

save_path = os.path.join(SAVE_DIR, file_name)
for _ in range(30):
    time.sleep(1)
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        if not os.path.exists(save_path + ".crdownload"):
            break

if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
    print(f"SUCCESS: {file_name} ({os.path.getsize(save_path):,} bytes)")
else:
    # Check if saved with different name
    files = os.listdir(SAVE_DIR)
    print(f"FAILED. Files in dir: {files}")

disconnect(p, browser)
print("Done!")
