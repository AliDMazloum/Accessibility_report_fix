"""Read-only on browser (except downloading one file locally):
Navigates to ITEC493 Module 1, opens 'Chapter 1' Text Document,
finds the attached file, and downloads it to the local course directory."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, scroll_panel, scroll_panel_to_top, screenshot, COURSE_DIR

p, browser, page = connect()

# Navigate to course content via Content tab
page.evaluate("""() => {
    const links = document.querySelectorAll('a');
    for (const link of links) {
        if (link.innerText.trim() === 'Content') { link.click(); return; }
    }
}""")
time.sleep(3)

# Close any open panel (like the accessibility report)
page.evaluate("""() => {
    const closeBtn = document.querySelector('[class*="offcanvas"] button[class*="close"], [aria-label="Close"]');
    if (closeBtn) closeBtn.click();
}""")
time.sleep(1)

print(f"URL: {page.url}")

# Scroll to load all items
scroll_panel(page)
scroll_panel_to_top(page)

# Expand Module 1
page.evaluate("""() => {
    const divs = document.querySelectorAll('div[data-content-id]');
    for (const div of divs) {
        const btn = div.querySelector('button[aria-label*="Reorder"]');
        if (btn && btn.getAttribute('aria-label').includes('Module 1')) {
            div.scrollIntoView({behavior: 'instant', block: 'center'});
            const ct = div.querySelector('.click-to-invoke-container');
            if (ct) ct.click();
            return;
        }
    }
}""")
time.sleep(2)

# Scroll to load Module 1 children
for _ in range(5):
    page.evaluate("() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }")
    time.sleep(0.3)

# Click "Chapter 1" text document link
page.evaluate("""() => {
    const divs = document.querySelectorAll('div[data-content-id]');
    for (const div of divs) {
        const link = div.querySelector('a[class*="contentItemTitle"]');
        if (link && link.innerText.trim() === 'Chapter 1') {
            link.click();
            return;
        }
    }
}""")
time.sleep(3)

print(f"After click URL: {page.url}")
screenshot(page, "chapter1_view")

# Now look for download options in the document view panel
# The file viewer should have a "..." menu or download button
download_info = page.evaluate("""() => {
    const result = [];
    // Look for download links
    const links = document.querySelectorAll('a[download], a[href*="download"], a[href*="bbcswebdav"]');
    links.forEach(el => {
        result.push({type: 'download_link', text: el.innerText.trim().substring(0, 60), href: (el.getAttribute('href') || '').substring(0, 150)});
    });
    // Look for the three-dot menu button near the file
    const menus = document.querySelectorAll('button[aria-label*="more"], button[aria-label*="More"], button[aria-label*="menu"], button[aria-label*="options"]');
    menus.forEach(el => {
        result.push({type: 'menu_button', ariaLabel: el.getAttribute('aria-label'), cls: (el.className || '').substring(0, 80)});
    });
    // Look for the file name span to confirm we're in the right view
    const fileSpans = document.querySelectorAll('span[class*="fileText"]');
    fileSpans.forEach(el => {
        result.push({type: 'file_name', text: el.innerText.trim()});
    });
    return result;
}""")

print(f"\nDownload-related elements: {len(download_info)}")
for item in download_info:
    print(f"  {json.dumps(item)}")

disconnect(p, browser)
