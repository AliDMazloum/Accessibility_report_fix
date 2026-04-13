"""Read-only: Opens each Text Document to discover attached files.
For each module: expand it, click each Text Document child, read attached file names,
navigate back via 'Contents' breadcrumb, collapse module, move on.
Saves complete file map to file_map.json."""
import sys, json, time
sys.path.insert(0, '.')
from bb_utils import connect, disconnect, save_json, scroll_panel, scroll_panel_to_top

p, browser, page = connect()

with open('course_structure.json') as f:
    course = json.load(f)

def click_content_tab(page):
    page.evaluate("""() => {
        const links = document.querySelectorAll('a');
        for (const link of links) {
            if (link.innerText.trim() === 'Content') { link.click(); return; }
        }
    }""")
    time.sleep(3)

def click_contents_back(page):
    """Click the 'Contents' breadcrumb to go back from document view."""
    page.evaluate("""() => {
        const links = document.querySelectorAll('a, button');
        for (const link of links) {
            const text = link.innerText.trim();
            if (text === 'Contents' || text.startsWith('Contents')) { link.click(); return; }
        }
    }""")
    time.sleep(2)

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

def get_attached_files(page):
    """Read attached file names from a document view."""
    return page.evaluate("""() => {
        const result = [];
        // Files shown in the document view as attachment items
        const fileItems = document.querySelectorAll('[class*="file-viewer"], [class*="attachment"]');
        fileItems.forEach(el => {
            const name = el.querySelector('[class*="fileText"], [class*="fileName"]');
            if (name) {
                const text = name.innerText.trim();
                if (text && text.includes('.')) result.push(text);
            }
        });
        // Also check for file links with extensions
        const links = document.querySelectorAll('a');
        links.forEach(el => {
            const text = el.innerText.trim();
            const href = el.getAttribute('href') || '';
            if (text.match(/\.(pdf|docx|pptx|xlsx|pkt|zip|txt)$/i)) {
                if (!result.includes(text)) result.push(text);
            }
        });
        // Also check for file viewer root elements
        const viewers = document.querySelectorAll('[class*="rootControls"] [class*="fileText"]');
        viewers.forEach(el => {
            const text = el.innerText.trim();
            if (text && !result.includes(text)) result.push(text);
        });
        return result;
    }""")

# Ensure we're on course outline
click_content_tab(page)
scroll_panel(page)
scroll_panel_to_top(page)

file_map = {}  # content_id -> {title, path, files}

# Process top-level Text Documents
top_level = course.get('_top_level', [])
for item in top_level:
    if item['type'] == 'Text Document':
        toggle_item(page, item['id'])
        time.sleep(1)
        files = get_attached_files(page)
        file_map[item['id']] = {'title': item['title'], 'path': item['title'], 'files': files}
        print(f"[top] {item['title']}: {files}")
        click_contents_back(page)
        time.sleep(1)

# Process each module
for section, items in course.items():
    if section == '_top_level' or not isinstance(items, list):
        continue
    
    # Find the module ID
    all_items = page.evaluate("""() => {
        const divs = document.querySelectorAll('div[data-content-id]');
        const result = [];
        divs.forEach(div => {
            const id = div.getAttribute('data-content-id');
            const h3 = div.querySelector('h3');
            const title = h3 ? h3.innerText.trim() : '';
            result.push({id: id, title: title});
        });
        return result;
    }""")
    
    mod_id = None
    for ai in all_items:
        if ai['title'] == section:
            mod_id = ai['id']
            break
    
    if not mod_id:
        print(f"\nSkipping {section}: module not found on page")
        continue
    
    # Expand module
    if not is_expanded(page, mod_id):
        toggle_item(page, mod_id)
        for _ in range(5):
            page.evaluate("""() => { const p = document.querySelector('.panel-wrap'); if (p) p.scrollBy(0, 300); }""")
            time.sleep(0.3)
    
    print(f"\n{section}:")
    
    # Process each Text Document in this module
    for item in items:
        if item['type'] == 'Text Document':
            toggle_item(page, item['id'])
            time.sleep(1)
            files = get_attached_files(page)
            path = f"{section}/{item['title']}"
            file_map[item['id']] = {'title': item['title'], 'path': path, 'files': files}
            print(f"  {item['title']}: {files}")
            click_contents_back(page)
            time.sleep(1)
        
        # Also check children of folders
        if 'children' in item:
            for child in item.get('children', []):
                if child['type'] == 'Text Document':
                    # Need to expand folder first
                    if not is_expanded(page, item['id']):
                        toggle_item(page, item['id'])
                        time.sleep(1)
                    toggle_item(page, child['id'])
                    time.sleep(1)
                    files = get_attached_files(page)
                    path = f"{section}/{item['title']}/{child['title']}"
                    file_map[child['id']] = {'title': child['title'], 'path': path, 'files': files}
                    print(f"    {child['title']}: {files}")
                    click_contents_back(page)
                    time.sleep(1)
    
    # Collapse module
    if is_expanded(page, mod_id):
        toggle_item(page, mod_id)

save_json(file_map, 'file_map.json')
total_files = sum(len(v['files']) for v in file_map.values())
print(f"\nDone! Mapped {len(file_map)} documents containing {total_files} files")
print("Saved to file_map.json")
disconnect(p, browser)
