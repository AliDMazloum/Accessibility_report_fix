"""Read-only: Maps the full course structure by expanding every module and folder.
Clicks Content tab to ensure we're on course outline, scrolls to load items,
expands each module/folder, reads children, collapses, moves on.
Saves complete tree to course_structure.json."""
import sys, json, time
sys.path.insert(0, '.')
from bb_utils import connect, disconnect, save_json, scroll_panel, scroll_panel_to_top

p, browser, page = connect()

def click_content_tab(page):
    page.evaluate("""() => {
        const links = document.querySelectorAll('a');
        for (const link of links) {
            if (link.innerText.trim() === 'Content') { link.click(); return; }
        }
    }""")
    time.sleep(3)

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

def get_children_of(page, cid):
    return page.evaluate("""(cid) => {
        const parentDiv = document.querySelector('div[data-content-id="' + cid + '"]');
        if (!parentDiv) return [];
        const childDivs = parentDiv.querySelectorAll('div[data-content-id]');
        const result = [];
        childDivs.forEach(div => {
            const id = div.getAttribute('data-content-id');
            if (id === cid) return;
            // Only direct children (not grandchildren)
            const directParent = div.parentElement ? div.parentElement.closest('div[data-content-id]') : null;
            if (directParent && directParent.getAttribute('data-content-id') !== cid) return;
            const iconSvg = div.querySelector('svg[aria-label]');
            const type = iconSvg ? iconSvg.getAttribute('aria-label') : 'unknown';
            const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
            const h3 = div.querySelector('h3');
            const title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
            result.push({id: id, title: title.substring(0, 200), type: type});
        });
        return result;
    }""", cid)

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

def is_expanded(page, cid):
    return page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (!div) return false;
        const el = div.querySelector('[aria-expanded]');
        return el ? el.getAttribute('aria-expanded') === 'true' : false;
    }""", cid)

def scroll_to_load():
    for _ in range(5):
        page.evaluate("""() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }""")
        time.sleep(0.3)

# Ensure we're on course outline
click_content_tab(page)
scroll_panel(page)
scroll_panel_to_top(page)

# Get all top-level items
all_items = get_all_items(page)
top_modules = [i for i in all_items if i['parentId'] == 'root' and i['type'] == 'Learning Module']
top_other = [i for i in all_items if i['parentId'] == 'root' and i['type'] != 'Learning Module']

course = {'_top_level': top_other}
print(f"Top-level: {len(top_other)} items, {len(top_modules)} modules")

# Collapse any already-expanded modules
for mod in top_modules:
    if is_expanded(page, mod['id']):
        toggle_item(page, mod['id'])

# Process each module
for mod in top_modules:
    toggle_item(page, mod['id'])
    scroll_to_load()
    
    children = get_children_of(page, mod['id'])
    
    # Check for folders inside this module and expand them too
    for child in children:
        if child['type'] in ('Folder', 'Open Folder'):
            toggle_item(page, child['id'])
            scroll_to_load()
            grandchildren = get_children_of(page, child['id'])
            child['children'] = grandchildren
            
            # Check for sub-sub-folders
            for gc in grandchildren:
                if gc['type'] in ('Folder', 'Open Folder'):
                    toggle_item(page, gc['id'])
                    scroll_to_load()
                    gc['children'] = get_children_of(page, gc['id'])
                    if is_expanded(page, gc['id']):
                        toggle_item(page, gc['id'])
            
            if is_expanded(page, child['id']):
                toggle_item(page, child['id'])
    
    course[mod['title']] = children
    count = len(children)
    folder_items = sum(len(c.get('children', [])) for c in children)
    print(f"  {mod['title']}: {count} items (+{folder_items} in folders)")
    
    if is_expanded(page, mod['id']):
        toggle_item(page, mod['id'])
    time.sleep(0.3)

# Also check top-level folders
for item in top_other:
    if item['type'] == 'Folder':
        toggle_item(page, item['id'])
        scroll_to_load()
        children = get_children_of(page, item['id'])
        item['children'] = children
        print(f"  Top folder '{item['title']}': {len(children)} items")
        if is_expanded(page, item['id']):
            toggle_item(page, item['id'])

save_json(course, 'course_structure.json')

# Print summary
total = 0
for key, val in course.items():
    if isinstance(val, list):
        total += len(val)
        for item in val:
            total += len(item.get('children', []))

print(f"\nComplete! Total items mapped: {total}")
print("Saved to course_structure.json")
disconnect(p, browser)
