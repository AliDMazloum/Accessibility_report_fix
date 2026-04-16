"""Version 2 workflow orchestrator.

Chains all 7 steps of the v2 pipeline. Detects which steps have already
completed (by checking for their output files) and resumes from where the
last run left off. Pauses with clear instructions when a Claude Code slash
command is needed (/semantic-validate, /alt-text-validate), then picks up
again on re-run once the output file appears.

Usage:
    python scripts/v2_run.py <course_key>          # run / resume
    python scripts/v2_run.py <course_key> --clean   # wipe stale data, start fresh
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import DATA_DIR


def _exists(course_key, name):
    return os.path.exists(os.path.join(DATA_DIR, name.format(c=course_key)))


def _path(course_key, name):
    return os.path.join(DATA_DIR, name.format(c=course_key))


def _has_images(course_key):
    path = _path(course_key, 'v2_images_needing_alt_{c}.json')
    if not os.path.exists(path):
        return False
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return bool(data) and sum(len(e.get('images', [])) for e in data) > 0


def run_all(course_key):
    # ── Step 1+2: Collect ────────────────────────────────────────────────
    if not _exists(course_key, 'v2_collected_{c}.json'):
        print("=" * 60)
        print(f"  Step 1+2: Collect (download) for {course_key}")
        print("=" * 60)
        from v2_collect import collect_all
        collect_all(course_key)
    else:
        print(f"Step 1+2: v2_collected_{course_key}.json already exists, skipping collect.", flush=True)

    # ── Step 2b: Prepare semantic tasks ──────────────────────────────────
    if not _exists(course_key, 'semantic_tasks_{c}.json'):
        print("\n" + "=" * 60)
        print(f"  Step 2b: Prepare semantic tasks for {course_key}")
        print("=" * 60)
        try:
            from semantic_agents import prepare_tasks
            prepare_tasks(course_key)
        except ImportError:
            print("  semantic_agents.py not found; skipping semantic preparation.")
    else:
        print(f"Step 2b: semantic_tasks_{course_key}.json already exists, skipping prepare.", flush=True)

    # ── Step 3: Semantic validate (slash command) ────────────────────────
    # Check if there are tasks that still need validation (not just whether
    # the results file exists — prepare_tasks seeds it with "already_good"
    # entries, which creates the file before validation has actually run).
    needs_semantic = False
    tasks_path = _path(course_key, 'semantic_tasks_{c}.json')
    results_path = _path(course_key, 'semantic_results_{c}.json')
    if os.path.exists(tasks_path):
        with open(tasks_path, encoding='utf-8') as f:
            tasks = json.load(f)
        results_names = set()
        if os.path.exists(results_path):
            with open(results_path, encoding='utf-8') as f:
                results_names = {e.get('report_name') for e in json.load(f)}
        pending_tasks = [t for t in tasks if t.get('report_name') not in results_names]
        if pending_tasks:
            needs_semantic = True

    if needs_semantic and not _exists(course_key, 'v2_fixed_{c}.json'):
        print(f"\n{'='*60}")
        print(f"  PAUSED: {len(pending_tasks)} docs need semantic validation for {course_key}")
        print(f"{'='*60}")
        print(f"  Run this in Claude Code:")
        print(f"    /semantic-validate {course_key}")
        print(f"  Then re-run: python scripts/v2_run.py {course_key}")
        return 'paused_semantic'
    elif needs_semantic:
        print(f"Step 3: {len(pending_tasks)} semantic tasks pending, but v2_fixed already exists. Skipping.", flush=True)
    else:
        print(f"Step 3: All semantic tasks resolved for {course_key}, continuing.", flush=True)

    # ── Step 4: Fix ──────────────────────────────────────────────────────
    if not _exists(course_key, 'v2_fixed_{c}.json'):
        print("\n" + "=" * 60)
        print(f"  Step 4: Fix for {course_key}")
        print("=" * 60)
        from v2_fix import fix_all
        fix_all(course_key)
    else:
        print(f"Step 4: v2_fixed_{course_key}.json already exists, skipping fix.", flush=True)

    # ── Step 5: Alt-text validate (slash command, if images present) ─────
    if _has_images(course_key):
        alt_texts_path = _path(course_key, 'v2_alt_texts_{c}.json')
        imgs_path = _path(course_key, 'v2_images_needing_alt_{c}.json')
        # Count how many docs still need alt text generation
        alt_done = set()
        if os.path.exists(alt_texts_path):
            with open(alt_texts_path, encoding='utf-8') as f:
                alt_done = {os.path.basename(e.get('fixed_path', '')) for e in json.load(f)}
        with open(imgs_path, encoding='utf-8') as f:
            imgs_data = json.load(f)
        pending_alt = [e for e in imgs_data
                       if os.path.basename(e.get('fixed_path', '')) not in alt_done]
        if pending_alt:
            total_imgs = sum(len(e.get('images', [])) for e in pending_alt)
            print(f"\n{'='*60}")
            print(f"  PAUSED: {len(pending_alt)} docs ({total_imgs} images) need alt-text for {course_key}")
            print(f"{'='*60}")
            print(f"  Run this in Claude Code:")
            print(f"    /alt-text-validate {course_key}")
            print(f"  Then re-run: python scripts/v2_run.py {course_key}")
            return 'paused_alt_text'
        else:
            print(f"Step 5: All alt texts generated for {course_key}, continuing.", flush=True)

        # ── Step 6: Apply alt texts ──────────────────────────────────────
        print("\n" + "=" * 60)
        print(f"  Step 6: Apply alt texts for {course_key}")
        print("=" * 60)
        from phase4b_apply_alts import apply_all_alt_texts
        alt_path = _path(course_key, 'v2_alt_texts_{c}.json')
        apply_all_alt_texts(alt_path)
    else:
        print("Steps 5+6: No images need alt text, skipping.", flush=True)

    # ── Step 7: Upload ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  Step 7: Upload for {course_key}")
    print("=" * 60)
    from v2_upload import upload_all
    upload_all(course_key)
    return 'complete'


def main():
    parser = argparse.ArgumentParser(description="v2 workflow orchestrator (resume-friendly)")
    parser.add_argument('course_key')
    parser.add_argument('--clean', action='store_true',
                        help='Remove all stale v2 data files for this course before starting')
    args = parser.parse_args()
    course_key = args.course_key.upper()

    if args.clean:
        from v2_collect import clean_v2_data
        clean_v2_data(course_key)

    status = run_all(course_key)
    if status and status.startswith('paused'):
        print(f"\nOrchestrator paused ({status}). Re-run after completing the slash command.")
    elif status == 'complete':
        print(f"\nv2 pipeline complete for {course_key}.")


if __name__ == '__main__':
    main()
