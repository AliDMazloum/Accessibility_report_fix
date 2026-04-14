"""Phase 1: Scrape the accessibility report for a course.

Navigates to the accessibility report, clicks Content tab, extracts all items
across all pages. Saves to data/report_{COURSE}.json.

Uses disconnect/reconnect pattern to avoid throttling Chrome.

Usage:
    python scripts/phase1_scrape.py <course_key>
    python scripts/phase1_scrape.py CYBERINFRA
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, connect, disconnect, navigate_to_report_content,
                      find_items_frame, get_report_items, click_next_page,
                      save_json, report_filename)


def scrape_report(course_key):
    """Scrape all items from the accessibility report Content tab.

    Returns list of {name, type, issues, score, contentId}.
    """
    course = get_course(course_key)
    course_id = course['id']

    print(f"Phase 1: Scraping accessibility report for {course_key} ({course_id})")

    # Navigate to report and click Content tab
    navigate_to_report_content(course_id)

    # Extract items from all pages
    all_items = []
    page_num = 1

    p, browser, page = connect()
    items_frame = find_items_frame(page)
    if not items_frame:
        print("ERROR: Could not find items frame. Is the report loaded?")
        disconnect(p, browser)
        return []

    # Get first page
    items = get_report_items(items_frame)
    all_items.extend(items)
    print(f"  Page {page_num}: {len(items)} items")

    # Check if last item on page is already >= 85% (items sorted by score)
    def last_item_above_threshold(page_items):
        if not page_items:
            return False
        last_score = page_items[-1].get('score', '').replace('%', '')
        return last_score.isdigit() and int(last_score) >= 85

    # Paginate — stop once we reach a page where the last item is >= 85%
    while not last_item_above_threshold(items):
        if not click_next_page(items_frame):
            break
        page_num += 1
        items = get_report_items(items_frame)
        if not items:
            break
        all_items.extend(items)
        print(f"  Page {page_num}: {len(items)} items")

    disconnect(p, browser)

    print(f"\nTotal items: {len(all_items)}")
    return all_items


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python phase1_scrape.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)

    course_key = sys.argv[1].upper()
    items = scrape_report(course_key)

    if not items:
        print("ERROR: No items scraped.")
        sys.exit(1)

    # Save report
    filename = report_filename(course_key)
    save_json(items, filename)
    print(f"Saved {len(items)} items to data/{filename}")

    # Print summary
    below_85 = sum(1 for i in items
                   if i.get('score', '').replace('%', '').isdigit()
                   and int(i['score'].replace('%', '')) < 85)
    print(f"Items below 85%: {below_85}")
    print(f"Items at or above 85%: {len(items) - below_85}")


if __name__ == '__main__':
    main()
