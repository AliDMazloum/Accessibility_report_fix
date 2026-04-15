"""Version 2 workflow, step 3: fix every file downloaded by v2_collect.

Reads data/v2_collected_<COURSE>.json, runs phase4_fix.fix_single_file on
each downloaded path (creates backup_*, applies deterministic fixes in
place, extracts images needing alt text), and writes:
  - data/v2_fixed_<COURSE>.json (pending list with fixed_path per entry)
  - data/v2_images_needing_alt_<COURSE>.json (for subagent alt-text batch)

Usage:
    python scripts/v2_fix.py <course_key>
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import DATA_DIR
from phase4_fix import fix_single_file


def fix_all(course_key):
    src = os.path.join(DATA_DIR, f'v2_collected_{course_key}.json')
    if not os.path.exists(src):
        print(f"Missing: {src}. Run v2_collect first.")
        sys.exit(1)

    with open(src, encoding='utf-8') as f:
        collected = json.load(f)

    print(f"v2 Fix: {len(collected)} entries")
    fixed_entries = []
    all_images = []

    for entry in collected:
        name = entry['report_name']
        fpath = entry.get('downloaded_path')
        if not fpath or not os.path.exists(fpath):
            print(f"  SKIP {name}: downloaded file missing")
            fixed_entries.append({**entry, 'fixed_path': None,
                                  'fix_skipped_reason': 'downloaded file missing'})
            continue

        result = fix_single_file(fpath, {'report_name': name})
        if result.get('skipped_reason'):
            print(f"  SKIP {name}: {result['skipped_reason']}")
            fixed_entries.append({**entry, 'fixed_path': None,
                                  'fix_skipped_reason': result['skipped_reason']})
            continue

        fixes_str = ', '.join(result.get('fixes', [])) or 'none needed'
        imgs = result.get('images_need_alt', 0)
        print(f"  FIXED {name}: {fixes_str}; images={imgs}")
        fixed_entries.append({
            **entry,
            'fixed_path': result.get('fixed_path'),
            'images_need_alt': imgs,
            'fix_skipped_reason': None,
        })
        if result.get('images_detail'):
            all_images.append({
                'report_name': name,
                'fixed_path': result['fixed_path'],
                'images': result['images_detail'],
            })

    out_fixed = os.path.join(DATA_DIR, f'v2_fixed_{course_key}.json')
    with open(out_fixed, 'w', encoding='utf-8') as f:
        json.dump(fixed_entries, f, indent=2)

    total_images = sum(len(e['images']) for e in all_images)
    if all_images:
        out_imgs = os.path.join(DATA_DIR, f'v2_images_needing_alt_{course_key}.json')
        with open(out_imgs, 'w', encoding='utf-8') as f:
            json.dump(all_images, f, indent=2)
        print(f"\nImages needing alt text: {out_imgs} ({total_images} images across {len(all_images)} docs)")
    else:
        print("\nNo images need alt text.")

    fixed_count = sum(1 for e in fixed_entries if e['fixed_path'])
    print(f"\n{'='*60}")
    print(f"  v2 Fix Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Files fixed:           {fixed_count}/{len(collected)}")
    print(f"  Images needing alt:    {total_images}")
    print(f"  Saved list:            {out_fixed}")

    if total_images > 0:
        print(f"\nNext steps:")
        print(f"  1. Launch Claude Code subagents on data/v2_images_needing_alt_{course_key}.json (cap 40 images/doc)")
        print(f"  2. python scripts/phase4b_apply_alts.py {course_key} data/v2_alt_texts_{course_key}.json")
        print(f"  3. python scripts/v2_upload.py {course_key}")
    else:
        print(f"\nNext: python scripts/v2_upload.py {course_key}")


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python v2_fix.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)
    fix_all(sys.argv[1].upper())


if __name__ == '__main__':
    main()
