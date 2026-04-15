"""Version 2 workflow orchestrator.

Runs v2_collect then v2_fix. If images need alt text, exits with next-step
instructions (launch subagents, apply, then v2_upload). Otherwise runs
v2_upload automatically.

Usage:
    python scripts/v2_run.py <course_key>
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import DATA_DIR
from v2_collect import collect_all
from v2_fix import fix_all
from v2_upload import upload_all


def run_all(course_key):
    print("=" * 60)
    print(f"  v2 Step 1+2: Collect (download) for {course_key}")
    print("=" * 60)
    collect_all(course_key)

    print("\n" + "=" * 60)
    print(f"  v2 Step 3: Fix for {course_key}")
    print("=" * 60)
    fix_all(course_key)

    # Check if alt text is needed before step 4.
    imgs_path = os.path.join(DATA_DIR, f'v2_images_needing_alt_{course_key}.json')
    if os.path.exists(imgs_path):
        with open(imgs_path, encoding='utf-8') as f:
            images = json.load(f)
        if images:
            print(f"\nPaused: {sum(len(e['images']) for e in images)} images need alt text.")
            print(f"  1. Generate via Claude Code subagents on {imgs_path}")
            print(f"  2. python scripts/phase4b_apply_alts.py {course_key} data/v2_alt_texts_{course_key}.json")
            print(f"  3. python scripts/v2_upload.py {course_key}")
            return

    print("\n" + "=" * 60)
    print(f"  v2 Step 4: Upload for {course_key}")
    print("=" * 60)
    upload_all(course_key)


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python v2_run.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)
    run_all(sys.argv[1].upper())


if __name__ == '__main__':
    main()
