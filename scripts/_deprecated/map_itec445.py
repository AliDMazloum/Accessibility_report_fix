"""Map ITEC445 course structure and save to course_structure_ITEC445.json.
Same logic as remap_course.py but targets ITEC445."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from bb_utils import connect, disconnect, save_json, scroll_panel, scroll_panel_to_top, dismiss_popup, DATA_DIR

COURSE_ID = "_1328539_1"  # ITEC445

p, browser, page = connect()
print(f"Current URL: {page.url}")

# Navigate to ITEC445
page.goto(f"https://blackboard.sc.edu/ultra/courses/{COURSE_ID}/outline",
          wait_until="domcontentloaded", timeout=30000)
time.sleep(4)
dismiss_popup(page)
print(f"On course: {page.url}")

# --- Helper functions (same as remap_course.py) ---

def scroll_panel_down(page, times=5):
    for _ in range(times):
        page.evaluate("() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }")
        time.sleep(0.3)

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
            let title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
            if (!title) {
                const btn = div.querySelector('button[aria-label*="Reorder"]');
                if (btn) title = btn.getAttribute('aria-label').replace('Reorder ', '').replace('.', '').trim();
            }
            const parentContent = div.parentElement ? div.parentElement.closest('div[data-content-id]') : null;
            const parentId = parentContent ? parentContent.getAttribute('data-content-id') : 'root';
            result.push({id, type, title: title.substring(0, 200), parentId});
        });
        return result;
    }""")

def get_direct_children(page, parent_id):
    return page.evaluate("""(pid) => {
        const parentDiv = document.querySelector('div[data-content-id="' + pid + '"]');
        if (!parentDiv) return [];
        const childDivs = parentDiv.querySelectorAll('div[data-content-id]');
        const result = [];
        childDivs.forEach(div => {
            const id = div.getAttribute('data-content-id');
            if (id === pid) return;
            const iconSvg = div.querySelector('svg[aria-label]');
            const type = iconSvg ? iconSvg.getAttribute('aria-label') : 'unknown';
            const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
            const h3 = div.querySelector('h3');
            let title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
            if (!title) {
                const btn = div.querySelector('button[aria-label*="Reorder"]');
                if (btn) title = btn.getAttribute('aria-label').replace('Reorder ', '').replace('.', '').trim();
            }
            result.push({id, title: title.substring(0, 200), type});
        });
        return result;
    }""", parent_id)

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

def get_item_title(page, cid):
    return page.evaluate("""(cid) => {
        const div = document.querySelector('div[data-content-id="' + cid + '"]');
        if (!div) return '';
        const linkTitle = div.querySelector('a[class*="contentItemTitle"]');
        const h3 = div.querySelector('h3');
        let title = (linkTitle ? linkTitle.innerText.trim() : '') || (h3 ? h3.innerText.trim() : '');
        if (!title) {
            const btn = div.querySelector('button[aria-label*="Reorder"]');
            if (btn) title = btn.getAttribute('aria-label').replace('Reorder ', '').replace('.', '').trim();
        }
        return title;
    }""", cid)

def explore_folder(page, folder_id, depth=0):
    indent = "  " * (depth + 2)
    title = get_item_title(page, folder_id)
    toggle_item(page, folder_id)
    scroll_panel_down(page, 3)
    time.sleep(1)
    children = get_direct_children(page, folder_id)
    print(f"{indent}[Folder] {title or '(untitled)'}: {len(children)} items")

    result = []
    for child in children:
        print(f"{indent}  [{child['type']}] {child['title']}")
        child_data = dict(child)
        if child['type'] in ('Folder', 'Open Folder'):
            folder_children, real_title = explore_folder(page, child['id'], depth + 1)
            child_data['title'] = real_title or child_data['title']
            child_data['children'] = folder_children
        result.append(child_data)

    if is_expanded(page, folder_id):
        toggle_item(page, folder_id)
        time.sleep(0.5)
    return result, title

# --- Main ---
scroll_panel(page)
scroll_panel_to_top(page)

all_items = get_all_items(page)
top_modules = [i for i in all_items if i['parentId'] == 'root' and i['type'] == 'Learning Module']
top_other = [i for i in all_items if i['parentId'] == 'root' and i['type'] != 'Learning Module']

course_name = page.evaluate("""() => {
    const body = document.body.innerText;
    const lines = body.split(String.fromCharCode(10));
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.match && trimmed.match(/^[A-Z]{3,4}\\d{3}/)) return trimmed;
    }
    return '';
}""") or "ITEC445-001-SPRING-2026"

print(f"Course: '{course_name}'")

course = {'_course_name': course_name, '_top_level': top_other}
print(f"\nTop-level: {len(top_other)} items")
for item in top_other:
    print(f"  [{item['type']}] {item['title']}")

# Explore top-level folders
for i, item in enumerate(top_other):
    if item['type'] == 'Folder':
        children, real_title = explore_folder(page, item['id'])
        top_other[i]['title'] = real_title or item['title']
        top_other[i]['children'] = children

# Collapse any expanded modules
for mod in top_modules:
    if is_expanded(page, mod['id']):
        toggle_item(page, mod['id'])

print(f"\nExpanding {len(top_modules)} modules...")

for mod in top_modules:
    print(f"\n{mod['title']}:")
    toggle_item(page, mod['id'])
    scroll_panel_down(page, 8)
    children = get_direct_children(page, mod['id'])

    processed = []
    for child in children:
        child_data = dict(child)
        print(f"  [{child['type']}] {child['title']}")
        if child['type'] in ('Folder', 'Open Folder'):
            folder_children, real_title = explore_folder(page, child['id'])
            child_data['title'] = real_title or child_data['title']
            child_data['children'] = folder_children
        processed.append(child_data)

    course[mod['title']] = processed

    if is_expanded(page, mod['id']):
        toggle_item(page, mod['id'])
    time.sleep(0.3)

# Save as ITEC445 structure
save_json(course, 'course_structure_ITEC445.json')

total = 0
def count_items(items):
    global total
    for item in items:
        total += 1
        if 'children' in item:
            count_items(item['children'])

for key, val in course.items():
    if isinstance(val, list):
        count_items(val)

print(f"\nComplete! {total} items mapped")
print("Saved to data/course_structure_ITEC445.json")
disconnect(p, browser)
