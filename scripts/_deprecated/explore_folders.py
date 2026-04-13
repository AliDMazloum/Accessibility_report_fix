"""Read-only: Explore folder contents by clicking through the UI.
Expands modules, clicks into folders, reads contents, navigates back."""
import sys, json, time
sys.path.insert(0, '.')
from bb_utils import connect, disconnect, save_json, scroll_panel, scroll_panel_to_top

p, browser, page = connect()
print(f"Starting URL: {page.url}")

# Make sure we're on the course outline
page.evaluate("""() => {
    const links = document.querySelectorAll('a');
    for (const link of links) {
        if (link.innerText.trim() === 'Content') { link.click(); return; }
    }
}""")
time.sleep(3)

# Scroll panel to load all items
scroll_panel(page)
scroll_panel_to_top(page)

def get_all_items(page):
    return page.evaluate("""() => {
        const divs = document.querySelectorAll('div[data-content-id]');
        const result = [];
        divs.forEach(div => {
            const id = div.getAttribute('data-content-id');
            const iconSvg = div.querySelector('svg[aria-label]');
            const type = iconSvg ? iconSvg.getAttribute('aria-label') : 'unknown';
            const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
            const h3 = div.querySelector('h3');
            const title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
            const parentContent = div.parentElement ? div.parentElement.closest('div[data-content-id]') : null;
            const parentId = parentContent ? parentContent.getAttribute('data-content-id') : 'root';
            result.push({id: id, type: type, title: title.substring(0, 200), parentId: parentId});
        });
        return result;
    }""")

def toggle_module(page, cid):
    page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (div) {
            div.scrollIntoView({behavior: 'instant', block: 'center'});
            const ct = div.querySelector('.click-to-invoke-container');
            if (ct) ct.click();
        }
    }""", cid)
    time.sleep(2)

def is_expanded(page, cid):
    return page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (!div) return false;
        const el = div.querySelector('[aria-expanded]');
        return el ? el.getAttribute('aria-expanded') === 'true' : false;
    }""", cid)

def click_item(page, cid):
    page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (div) {
            div.scrollIntoView({behavior: 'instant', block: 'center'});
            const ct = div.querySelector('.click-to-invoke-container');
            if (ct) ct.click();
        }
    }""", cid)
    time.sleep(3)

def go_back_to_outline(page):
    """Click Content tab to go back to course outline."""
    page.evaluate("""() => {
        const links = document.querySelectorAll('a');
        for (const link of links) {
            if (link.innerText.trim() === 'Content') { link.click(); return true; }
        }
        return false;
    }""")
    time.sleep(3)
    return True

# Test with Module 1 -> Exercises folder
# First, expand Module 1
module1_id = "_27756640_1"
toggle_module(page, module1_id)

# Scroll to load children
for _ in range(5):
    page.evaluate("""() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }""")
    time.sleep(0.3)

# Find the folder inside Module 1
items = get_all_items(page)
module1_children = [i for i in items if i['parentId'] == module1_id]
print(f"\nModule 1 children: {len(module1_children)}")
for c in module1_children:
    print(f"  [{c['type']}] {c['title']} ({c['id']})")

# Find the folder
folder = [c for c in module1_children if c['type'] == 'Folder']
if folder:
    folder = folder[0]
    print(f"\nClicking into folder: {folder['title'] or '(untitled)'} ({folder['id']})")
    click_item(page, folder['id'])
    
    print(f"URL after folder click: {page.url}")
    
    # Scroll to load items in folder
    scroll_panel(page)
    
    # Read folder contents
    folder_items = get_all_items(page)
    print(f"\nFolder contents: {len(folder_items)} items")
    for item in folder_items:
        print(f"  [{item['type']}] {item['title']} ({item['id']})")
    
    # Check for navigation elements in folder view
    nav_info = page.evaluate("""() => {
        const result = [];
        // Look for breadcrumbs or back button
        const allLinks = document.querySelectorAll('a, button');
        allLinks.forEach(el => {
            const text = el.innerText.trim();
            const ariaLabel = el.getAttribute('aria-label') || '';
            if (text === 'Content' || ariaLabel.includes('back') || ariaLabel.includes('Back')
                || text.includes('Module 1') || text.includes('Back')) {
                result.push({text: text.substring(0, 60), tag: el.tagName, ariaLabel: ariaLabel.substring(0, 60)});
            }
        });
        return result;
    }""")
    print(f"\nNavigation elements in folder view:")
    for n in nav_info:
        print(f"  {json.dumps(n)}")
    
    # Navigate back to outline
    print("\nNavigating back to course outline...")
    go_back_to_outline(page)
    print(f"URL after back: {page.url}")

disconnect(p, browser)
