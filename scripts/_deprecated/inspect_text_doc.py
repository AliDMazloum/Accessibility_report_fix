"""Read-only: Opens a Text Document to see what files are attached inside.
Expands Module 2, clicks 'Slides: Switching Concepts', reads the page content,
then navigates back to course outline via Content tab."""
import sys, json, time
sys.path.insert(0, '.')
from bb_utils import connect, disconnect, scroll_panel, scroll_panel_to_top, screenshot

p, browser, page = connect()
print(f"URL: {page.url}")

def toggle_item(page, cid):
    page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (div) {
            div.scrollIntoView({behavior: 'instant', block: 'center'});
            const ct = div.querySelector('.click-to-invoke-container');
            if (ct) ct.click();
        }
    }""", cid)
    time.sleep(2)

def click_content_tab(page):
    page.evaluate("""() => {
        const links = document.querySelectorAll('a');
        for (const link of links) {
            if (link.innerText.trim() === 'Content') { link.click(); return; }
        }
    }""")
    time.sleep(3)

# Scroll to load all items
scroll_panel(page)
scroll_panel_to_top(page)

# Expand Module 2
module2_id = "_27756641_1"
toggle_item(page, module2_id)
time.sleep(1)

# Click "Slides: Switching Concepts" (_28329869_1)
slides_id = "_28329869_1"
toggle_item(page, slides_id)
time.sleep(2)

print(f"URL after click: {page.url}")

# Take screenshot to see what's displayed
screenshot(page, "text_doc_view")

# Read the page text to understand the structure
body = page.evaluate('() => document.body.innerText')
lines = [l.strip() for l in body.split(chr(10)) if l.strip()]
print(f"\nPage text ({len(lines)} lines):")
for i, line in enumerate(lines[:60]):
    print(f"  {i}: {line[:120]}")

# Look for file attachments, download links, etc.
attachments = page.evaluate("""() => {
    const result = [];
    // Look for file attachment elements
    const links = document.querySelectorAll('a[href*="download"], a[href*="attachment"], a[href*="file"], a[href*="bbcswebdav"]');
    links.forEach(el => {
        result.push({text: el.innerText.trim().substring(0, 100), href: (el.getAttribute('href') || '').substring(0, 150), tag: el.tagName});
    });
    // Look for embedded content items
    const embeds = document.querySelectorAll('[class*="attachment"], [class*="file"], [class*="embed"]');
    embeds.forEach(el => {
        result.push({text: el.innerText.trim().substring(0, 100), cls: el.className.substring(0, 80), tag: el.tagName});
    });
    return result;
}""")

print(f"\nAttachment elements: {len(attachments)}")
for att in attachments:
    print(f"  {json.dumps(att)}")

# Navigate back
click_content_tab(page)
print(f"\nBack to: {page.url}")
disconnect(p, browser)
