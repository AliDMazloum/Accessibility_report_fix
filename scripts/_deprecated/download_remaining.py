"""Download the remaining 7 ITEC493 files that are in top-level/folders.
These weren't picked up by the module-based iteration."""
import sys, os, time, glob
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, dismiss_popup, COURSE_DIR

COURSE_ID = "_1308255_1"  # ITEC493
BASE_DIR = os.path.join(COURSE_DIR, "ITEC493-001-FALL-2025")

# Remaining files and their content item IDs from course_structure_ITEC493.json
# Mapped by looking at the course structure
REMAINING = [
    # Top-level items
    {"id": "_26485873_1", "title": "ITEC 493 Syllabus", "section": "Syllabus",
     "target_file": "syllabus.pdf"},
    {"id": "_26724812_1", "title": "Overview Cybersecurity Labs", "section": "Top Level",
     "target_file": "Overview Cybersecurity Labs.pdf"},
    {"id": "_26866489_1", "title": "Cybersecurity Lab Manuals", "section": "Top Level",
     "target_file": "cybersecurity_fundamentals.pdf"},
    # Final Project folder
    {"id": "_27154754_1", "title": "Final Project - ITEC 493", "section": "Final Project",
     "target_file": "Final Project - ITEC 493.pdf"},
    # Resources folder
    {"id": "_27301612_1", "title": "Security Guide PDF", "section": "Resources",
     "target_file": "Security _Guide_to_Network_Security_Fundamentals_7edition.pdf"},
    {"id": "_27301670_1", "title": "Ciampa Mod10", "section": "Resources",
     "target_file": "Ciampa_CompTIASec _7e_PPT_Mod10.pptx"},
    {"id": "_27301673_1", "title": "Ciampa Mod13", "section": "Resources",
     "target_file": "Ciampa_CompTIASec _7e_PPT_Mod13.pptx"},
]

p, browser, page = connect()
print(f"Connected: {page.url}")

# Navigate to course first
page.goto(f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline",
          wait_until="domcontentloaded", timeout=30000)
time.sleep(4)
dismiss_popup(page)

downloaded = []
failed = []

for item in REMAINING:
    item_id = item['id']
    section = item['section']
    target = item['target_file']

    print(f"\n--- {section} / {item['title']} ---")

    # Set download directory
    save_dir = os.path.join(BASE_DIR, section.replace(':', ' -').replace('/', '-'))
    os.makedirs(save_dir, exist_ok=True)
    cdp = browser.contexts[0].new_cdp_session(page)
    cdp.send("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": os.path.abspath(save_dir).replace("/", "\\")
    })

    # Navigate to file
    file_url = f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline/file/{item_id}"
    try:
        page.goto(file_url, wait_until="domcontentloaded", timeout=20000)
    except Exception as e:
        print(f"  Navigation failed: {e}")
        failed.append(item)
        continue

    time.sleep(4)
    dismiss_popup(page)

    # Get file name
    file_name = page.evaluate("""() => {
        const iframes = document.querySelectorAll('iframe');
        for (const f of iframes) {
            const title = f.getAttribute('title') || '';
            if (title.includes('.pdf') || title.includes('.pptx') ||
                title.includes('.docx')) {
                return title;
            }
        }
        return null;
    }""")

    if not file_name:
        time.sleep(3)
        file_name = page.evaluate("""() => {
            const iframes = document.querySelectorAll('iframe');
            for (const f of iframes) {
                const title = f.getAttribute('title') || '';
                if (title.includes('.pdf') || title.includes('.pptx') ||
                    title.includes('.docx')) {
                    return title;
                }
            }
            return null;
        }""")

    if not file_name:
        print(f"  No file viewer found")
        failed.append(item)
        continue

    print(f"  File: {file_name}")
    save_path = os.path.join(save_dir, file_name)

    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        print(f"  Already exists ({os.path.getsize(save_path):,} bytes)")
        downloaded.append({'file': file_name, 'status': 'already exists'})
        continue

    # Find Download button in viewer frame
    viewer_frame = None
    for _ in range(15):
        for frame in page.frames:
            try:
                has_btn = frame.evaluate("""() => {
                    const btn = document.querySelector('button[aria-label="Download"]');
                    return btn ? true : false;
                }""")
                if has_btn:
                    viewer_frame = frame
                    break
            except:
                pass
        if viewer_frame:
            break
        time.sleep(1)

    if not viewer_frame:
        print(f"  No Download button found")
        failed.append(item)
        continue

    # Update CDP download path for this specific file
    cdp2 = browser.contexts[0].new_cdp_session(page)
    cdp2.send("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": os.path.abspath(save_dir).replace("/", "\\")
    })

    # Click download
    viewer_frame.click('button[aria-label="Download"]')

    # Wait for file
    for i in range(45):
        time.sleep(1)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            if not os.path.exists(save_path + ".crdownload"):
                break

    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        size = os.path.getsize(save_path)
        print(f"  Downloaded: {size:,} bytes")
        downloaded.append({'file': file_name, 'status': 'downloaded', 'size': size})
    else:
        print(f"  Download timed out")
        failed.append(item)

print(f"\n=== Summary ===")
print(f"Downloaded: {len(downloaded)}")
print(f"Failed: {len(failed)}")
for d in downloaded:
    print(f"  [OK] {d['file']}")
for f in failed:
    print(f"  [FAIL] {f['title']}")

disconnect(p, browser)
print("\nDone!")
