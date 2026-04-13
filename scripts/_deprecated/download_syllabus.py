"""Download syllabus.pdf from ITEC493 Syllabus Text Document.
The syllabus is inside a nested text document item."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, screenshot, dismiss_popup, COURSE_DIR

COURSE_ID = "_1308255_1"
BASE_DIR = os.path.join(COURSE_DIR, "ITEC493-001-FALL-2025", "Syllabus")
os.makedirs(BASE_DIR, exist_ok=True)

p, browser, page = connect()

# Set download dir via CDP
cdp = browser.contexts[0].new_cdp_session(page)
cdp.send("Page.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": os.path.abspath(BASE_DIR).replace("/", os.sep)
})

# Navigate to syllabus folder
page.goto(f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline/file/_26485873_1",
          wait_until="domcontentloaded", timeout=20000)
time.sleep(4)
dismiss_popup(page)

# Click the inner "ITEC 493 Syllabus" content item
click_result = page.evaluate("""() => {
    const links = document.querySelectorAll('a[class*="contentItemTitle"]');
    for (const a of links) {
        if (a.innerText.trim().includes('Syllabus')) {
            a.click();
            return 'clicked: ' + a.innerText.trim();
        }
    }
    // Fallback: any clickable element with Syllabus
    const all = document.querySelectorAll('a, button');
    for (const el of all) {
        if (el.innerText.trim() === 'ITEC 493 Syllabus' && el.tagName === 'A') {
            el.click();
            return 'clicked fallback: ' + el.innerText.trim();
        }
    }
    return 'not found';
}""")
print(f"Click: {click_result}")
time.sleep(5)

print(f"URL: {page.url}")
screenshot(page, "syllabus_inner")

# Check for file viewer iframe
file_name = page.evaluate("""() => {
    const iframes = document.querySelectorAll('iframe');
    for (const f of iframes) {
        const title = f.getAttribute('title') || '';
        if (title.includes('.pdf') || title.includes('.pptx') || title.includes('.docx')) {
            return title;
        }
    }
    return null;
}""")

if file_name:
    print(f"File: {file_name}")

    # Find Download button in viewer frame
    viewer_frame = None
    for _ in range(15):
        for frame in page.frames:
            try:
                has_btn = frame.evaluate("""() => {
                    return document.querySelector('button[aria-label="Download"]') ? true : false;
                }""")
                if has_btn:
                    viewer_frame = frame
                    break
            except:
                pass
        if viewer_frame:
            break
        time.sleep(1)

    if viewer_frame:
        # Re-set CDP download path
        cdp2 = browser.contexts[0].new_cdp_session(page)
        cdp2.send("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": os.path.abspath(BASE_DIR).replace("/", os.sep)
        })

        viewer_frame.click('button[aria-label="Download"]')

        save_path = os.path.join(BASE_DIR, file_name)
        for i in range(45):
            time.sleep(1)
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                if not os.path.exists(save_path + ".crdownload"):
                    break

        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            print(f"Downloaded: {os.path.getsize(save_path):,} bytes")
        else:
            print("Download timed out")
            print(f"Files in dir: {os.listdir(BASE_DIR)}")
    else:
        print("No Download button found")
else:
    print("No file viewer found - checking for attachment links")
    links = page.evaluate("""() => {
        const r = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href') || '';
            const text = a.innerText.trim();
            if (href.includes('bbcswebdav') || text.includes('.pdf')) {
                r.push({text: text.substring(0, 80), href: href.substring(0, 200)});
            }
        });
        return r;
    }""")
    print(f"Links: {json.dumps(links, indent=2)}")

disconnect(p, browser)
print("Done!")
