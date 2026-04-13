"""Read-only: Find navigation elements (back buttons, breadcrumbs, tabs) on current page."""
import sys, json
sys.path.insert(0, '.')
from bb_utils import connect, disconnect

p, browser, page = connect()
print(f"URL: {page.url}")

# Find breadcrumbs and back buttons
nav = page.evaluate("""() => {
    const result = [];
    // Breadcrumbs
    const crumbs = document.querySelectorAll('[class*="breadcrumb"] a, [class*="Breadcrumb"] a, [aria-label*="breadcrumb"] a');
    crumbs.forEach(el => {
        result.push({type: "breadcrumb", text: el.innerText.trim().substring(0, 80), tag: el.tagName});
    });
    // Back buttons
    const backs = document.querySelectorAll('[aria-label*="back"], [aria-label*="Back"]');
    backs.forEach(el => {
        result.push({type: "back", text: el.innerText.trim().substring(0, 80), tag: el.tagName, ariaLabel: el.getAttribute("aria-label")});
    });
    // Top nav tabs (Content, Calendar, etc.)
    const links = document.querySelectorAll('a');
    links.forEach(el => {
        const text = el.innerText.trim();
        if (text === 'Content' || text === 'Courses') {
            result.push({type: "navLink", text: text, tag: el.tagName, href: (el.getAttribute("href") || "").substring(0, 100)});
        }
    });
    // Course name in header
    const header = document.querySelector('[class*="courseName"], [class*="course-title"]');
    if (header) result.push({type: "courseHeader", text: header.innerText.trim().substring(0, 80)});
    return result;
}""")

for item in nav:
    print(json.dumps(item))

# Also check the top bar text
top_text = page.evaluate("""() => {
    const topbar = document.querySelector('header') || document.querySelector('[class*="banner"]');
    return topbar ? topbar.innerText.trim().substring(0, 300) : 'no header found';
}""")
print(f"\nHeader text: {top_text}")

disconnect(p, browser)
