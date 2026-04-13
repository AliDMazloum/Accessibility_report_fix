"""Phase 2: Extract target items (score < 85%) from the report.

Pure offline — no browser needed. Reads report JSON from Phase 1,
filters items below 85%, handles (N) suffix normalization, saves targets JSON.

Usage:
    python scripts/phase2_targets.py <course_key>
    python scripts/phase2_targets.py CYBERINFRA
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import load_json, save_json, report_filename, targets_filename

SCORE_THRESHOLD = 85
SKIP_TYPES = {'Ultra document'}


def strip_suffix(name):
    """Remove all trailing (N) suffixes from a filename.
    e.g. 'Lecture 2(1).pptx' -> 'Lecture 2.pptx'
         'file(1)(1).pptx' -> 'file.pptx'
    """
    stem, ext = os.path.splitext(name)
    while re.search(r'\(\d+\)$', stem):
        stem = re.sub(r'\(\d+\)$', '', stem).rstrip()
    return stem + ext


def extract_targets(course_key):
    """Read report JSON, filter items below threshold, return targets dict."""
    filename = report_filename(course_key)
    items = load_json(filename)

    targets = []
    norm_lookup = {}  # stripped_name -> report_name (for (N) suffix matching)

    for item in items:
        score_str = item.get('score', '').replace('%', '')
        if not score_str.isdigit():
            continue
        score = int(score_str)

        if score >= SCORE_THRESHOLD:
            continue

        if item.get('type', '') in SKIP_TYPES:
            continue

        name = item['name']
        targets.append({
            'name': name,
            'type': item.get('type', ''),
            'score': score,
            'contentId': item.get('contentId', ''),
        })

        # Build normalized lookup for (N) suffix matching
        stripped = strip_suffix(name)
        if stripped != name:
            norm_lookup[stripped] = name

    result = {
        'course': course_key,
        'threshold': SCORE_THRESHOLD,
        'total_report_items': len(items),
        'target_count': len(targets),
        'targets': targets,
        'norm_lookup': norm_lookup,
    }

    return result


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python phase2_targets.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)

    course_key = sys.argv[1].upper()

    print(f"Phase 2: Extracting targets for {course_key}")
    result = extract_targets(course_key)

    # Save
    filename = targets_filename(course_key)
    save_json(result, filename)
    print(f"Saved to data/{filename}")

    # Summary
    print(f"\nReport items: {result['total_report_items']}")
    print(f"Targets (< {SCORE_THRESHOLD}%): {result['target_count']}")
    print(f"Normalized lookups: {len(result['norm_lookup'])}")

    # Print targets sorted by score
    print(f"\nTargets:")
    for t in sorted(result['targets'], key=lambda x: x['score']):
        print(f"  {t['score']:3d}%  {t['type']:<20s}  {t['name']}")


if __name__ == '__main__':
    main()
