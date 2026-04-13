"""Read-only: Inspects the document view panel DOM to find correct selectors
for attached files. Opens 'Slides: Switching Concepts' in Module 2."""
import sys, json, time, os
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, scroll_panel, scroll_panel_to_top, screenshot

p, browser, page = connect()

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

scroll_panel(page)
scroll_panel_to_top(page)

# Expand Module 2 and click Slides: Switching Concepts
toggle_item(page, "_27756641_1")
time.sleep(1)
toggle_item(page, "_28329869_1")
time.sleep(2)

print(f"URL: {page.url}")

# The document view opens as a side panel (offcanvas or overlay)
# Let's find it by looking for panels with document-specific content
panels = page.evaluate("""() => {
    const result = [];
    // Look for the document view panel specifically
    const panels = document.querySelectorAll('[class*="offcanvas"], [class*="peek"], [class*="panel"], [class*="document-view"]');
    panels.forEach(p => {
        // Only panels that contain file-related elements
        const files = p.querySelectorAll('[class*="file"], [class*="attachment"]');
        if (files.length > 0) {
            result.push({
                cls: p.className.substring(0, 120),
                tag: p.tagName,
                fileCount: files.length,
                text: p.innerText.trim().substring(0, 500)
            });
        }
    });
    return result;
}""")

print(f"\nPanels with file elements: {len(panels)}")
for panel in panels:
    print(f"\n  Class: {panel['cls']}")
    print(f"  Files: {panel['fileCount']}")
    print(f"  Text preview: {panel['text'][:200]}")

# Also get the HTML of the document view area to understand structure
doc_html = page.evaluate("""() => {
    // The document viewer should be in an offcanvas panel
    const docPanels = document.querySelectorAll('[class*="offcanvas-panel"]');
    for (const p of docPanels) {
        if (p.querySelector('[class*="file"]')) {
            return p.innerHTML.substring(0, 5000);
        }
    }
    return 'not found';
}""")

# Search for file names in the panel HTML
import re
# Find anything that looks like a filename with extension
filenames = re.findall(r'[\w\-\s]+\.(pdf|docx|pptx|xlsx|pkt)', doc_html)
print(f"\nFile names found in document panel HTML: {filenames}")

# Navigate back
page.evaluate("""() => {
    const links = document.querySelectorAll('a');
    for (const link of links) {
        if (link.innerText.trim() === 'Content') { link.click(); return; }
    }
}""")
time.sleep(2)

disconnect(p, browser)
