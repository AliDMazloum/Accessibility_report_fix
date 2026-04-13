"""Master orchestrator: run all phases for a course.

Usage:
    python scripts/run_all.py <course_key>                # Run all phases 1-5
    python scripts/run_all.py <course_key> --phase 3      # Start from phase 3
    python scripts/run_all.py <course_key> --phase 4b     # Just apply alt texts
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python run_all.py <course_key> [--phase N]")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        print("\nPhases:")
        print("  1  - Scrape accessibility report")
        print("  2  - Extract target items (offline)")
        print("  3  - Download files from course structure")
        print("  4  - Fix files locally")
        print("  4b - Apply AI-generated alt texts")
        print("  5  - Upload fixed files")
        sys.exit(1)

    course_key = sys.argv[1].upper()
    start_phase = '1'
    if '--phase' in sys.argv:
        idx = sys.argv.index('--phase')
        if idx + 1 < len(sys.argv):
            start_phase = sys.argv[idx + 1]

    phases = ['1', '2', '3', '4', '4b', '5']
    start_idx = phases.index(start_phase) if start_phase in phases else 0

    for phase in phases[start_idx:]:
        if phase == '1':
            print(f"\n{'='*60}")
            print(f"  PHASE 1: Scrape accessibility report")
            print(f"{'='*60}")
            from phase1_scrape import scrape_report, main as p1_main
            sys.argv = ['phase1_scrape.py', course_key]
            p1_main()

        elif phase == '2':
            print(f"\n{'='*60}")
            print(f"  PHASE 2: Extract targets")
            print(f"{'='*60}")
            from phase2_targets import main as p2_main
            sys.argv = ['phase2_targets.py', course_key]
            p2_main()

        elif phase == '3':
            print(f"\n{'='*60}")
            print(f"  PHASE 3: Download files")
            print(f"{'='*60}")
            from phase3_download import main as p3_main
            sys.argv = ['phase3_download.py', course_key]
            p3_main()

        elif phase == '4':
            print(f"\n{'='*60}")
            print(f"  PHASE 4: Fix files")
            print(f"{'='*60}")
            from phase4_fix import main as p4_main
            sys.argv = ['phase4_fix.py', course_key]
            p4_main()

        elif phase == '4b':
            alt_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                    f'alt_texts_{course_key}.json')
            if os.path.exists(alt_path):
                print(f"\n{'='*60}")
                print(f"  PHASE 4b: Apply alt texts")
                print(f"{'='*60}")
                from phase4b_apply_alts import main as p4b_main
                sys.argv = ['phase4b_apply_alts.py', course_key, alt_path]
                p4b_main()
            else:
                print(f"\n  Phase 4b: No alt texts file found at {alt_path}")
                print(f"  Generate alt texts and save to data/alt_texts_{course_key}.json")
                print(f"  Then run: python run_all.py {course_key} --phase 4b")

        elif phase == '5':
            print(f"\n{'='*60}")
            print(f"  PHASE 5: Upload fixed files")
            print(f"{'='*60}")
            from phase5_upload import main as p5_main
            sys.argv = ['phase5_upload.py', course_key]
            p5_main()

    print(f"\n{'='*60}")
    print(f"  Pipeline complete for {course_key}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
