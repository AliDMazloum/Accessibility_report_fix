"""Phase 4: Fix all downloaded files locally.

Applies deterministic fixes (title, language, headings, table headers) and
extracts images needing AI-generated alt text.

Requires: data/download_manifest_{COURSE}.json from Phase 3.
Produces: data/fix_manifest_{COURSE}.json + data/images_needing_alt_{COURSE}.json

Usage:
    python scripts/phase4_fix.py <course_key>
    python scripts/phase4_fix.py CYBERINFRA
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))

from bb_utils import (get_course, load_json, save_json, download_manifest_filename,
                      fix_manifest_filename, COURSE_DIR)

LIBREOFFICE = "C:/Program Files/LibreOffice/program/soffice.exe"
MAX_FILE_SIZE_MB_PDF = 5
MAX_FILE_SIZE_MB_OFFICE = 20


def convert_old_format(input_path, output_dir):
    """Convert .doc/.ppt to .docx/.pptx using LibreOffice."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in ('.doc', '.ppt'):
        return None

    new_ext = '.docx' if ext == '.doc' else '.pptx'
    stem = os.path.splitext(os.path.basename(input_path))[0]
    converted = os.path.join(output_dir, stem + new_ext)

    if os.path.exists(converted):
        return converted

    result = subprocess.run(
        [LIBREOFFICE, '--headless', '--convert-to', new_ext[1:],
         '--outdir', output_dir, input_path],
        capture_output=True, text=True, timeout=120
    )
    if os.path.exists(converted):
        return converted
    return None


def fix_single_file(fpath, download_entry):
    """Fix a single file. Returns {report_name, fixed_path, fixes, images_need_alt, skipped_reason}."""
    from fix_pdf import fix_pdf
    from add_headings import add_headings_to_pdf
    from fix_office import (fix_docx, fix_pptx, extract_pptx_images,
                            extract_docx_images)

    report_name = download_entry['report_name']
    directory = os.path.dirname(fpath)
    ext = os.path.splitext(fpath)[1].lower()
    stem = os.path.splitext(os.path.basename(fpath))[0]
    size_mb = os.path.getsize(fpath) / (1024 * 1024)

    # Check file size
    max_size = MAX_FILE_SIZE_MB_OFFICE if ext in ('.pptx', '.ppt', '.docx', '.doc') else MAX_FILE_SIZE_MB_PDF
    if size_mb > max_size:
        return {'report_name': report_name, 'fixed_path': None,
                'fixes': [], 'images_need_alt': 0,
                'skipped_reason': f'too large ({size_mb:.1f} MB > {max_size} MB)'}

    # Convert old formats
    working_path = fpath
    if ext in ('.doc', '.ppt'):
        converted = convert_old_format(fpath, directory)
        if not converted:
            return {'report_name': report_name, 'fixed_path': None,
                    'fixes': [], 'images_need_alt': 0,
                    'skipped_reason': 'LibreOffice conversion failed'}
        working_path = converted
        ext = os.path.splitext(working_path)[1].lower()
        stem = os.path.splitext(os.path.basename(working_path))[0]

    # Naming: rename original to backup_*, fix writes to original name
    backup_path = os.path.join(directory, 'backup_' + os.path.basename(working_path))
    fixed_path = os.path.join(directory, os.path.basename(working_path))

    # Create backup if not already backed up
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(working_path, backup_path)
    fixes = []
    images_needing_alt = []

    try:
        if ext == '.pdf':
            result = fix_pdf(backup_path, fixed_path)
            if result.get('status') == 'fixed':
                fixes.extend(result.get('fixed', []))

            try:
                result2 = add_headings_to_pdf(fixed_path, fixed_path)
                if result2.get('status') == 'fixed':
                    fixes.append(f"{result2.get('headings_found', 0)} headings")
            except Exception as e:
                fixes.append(f'headings error: {e}')

        elif ext == '.docx':
            result = fix_docx(backup_path, fixed_path)
            if result.get('status') == 'fixed':
                fixes.extend(result.get('fixed', []))

            # Extract images needing alt text
            imgs_dir = os.path.join(directory, '_imgs_' + stem)
            images = extract_docx_images(fixed_path, imgs_dir)
            if images:
                images_needing_alt = images

        elif ext == '.pptx':
            result = fix_pptx(backup_path, fixed_path)
            if result.get('status') == 'fixed':
                fixes.extend(result.get('fixed', []))

            # Extract images needing alt text
            imgs_dir = os.path.join(directory, '_imgs_' + stem)
            images = extract_pptx_images(fixed_path, imgs_dir)
            if images:
                images_needing_alt = images

        else:
            return {'report_name': report_name, 'fixed_path': None,
                    'fixes': [], 'images_need_alt': 0,
                    'skipped_reason': f'unsupported format: {ext}'}

    except Exception as e:
        return {'report_name': report_name, 'fixed_path': None,
                'fixes': [], 'images_need_alt': 0,
                'skipped_reason': f'error: {e}'}

    actual_fixed = fixed_path if os.path.exists(fixed_path) else None
    return {
        'report_name': report_name,
        'original_path': os.path.normpath(fpath).replace('\\', '/'),
        'fixed_path': os.path.normpath(actual_fixed).replace('\\', '/') if actual_fixed else None,
        'fixes': fixes,
        'images_need_alt': len(images_needing_alt),
        'images_detail': images_needing_alt if images_needing_alt else None,
        'skipped_reason': None,
    }


def fix_all(course_key):
    """Fix all downloaded files for a course."""
    course = get_course(course_key)
    manifest = load_json(download_manifest_filename(course_key))
    downloads = manifest['downloads']

    print(f"Phase 4: Fixing {len(downloads)} files for {course_key}")

    fixed_results = []
    skipped = []
    all_images = []

    for entry in downloads:
        fpath = entry['local_path']
        if not os.path.exists(fpath):
            # Try with backslashes
            fpath = fpath.replace('/', '\\')
        if not os.path.exists(fpath):
            print(f"  MISSING: {entry['report_name']} ({fpath})")
            skipped.append({'report_name': entry['report_name'], 'reason': 'file not found'})
            continue

        print(f"  Fixing: {entry['report_name']} ({os.path.getsize(fpath) / 1024 / 1024:.1f} MB)")
        result = fix_single_file(fpath, entry)

        if result.get('skipped_reason'):
            print(f"    SKIP: {result['skipped_reason']}")
            skipped.append({'report_name': result['report_name'], 'reason': result['skipped_reason']})
        else:
            fixes_str = ', '.join(result['fixes']) if result['fixes'] else 'none needed'
            print(f"    Fixed: {fixes_str}")
            if result['images_need_alt'] > 0:
                print(f"    Images needing alt text: {result['images_need_alt']}")
                all_images.append({
                    'report_name': result['report_name'],
                    'pptx_path': result.get('original_path', ''),
                    'fixed_path': result['fixed_path'],
                    'images': result['images_detail'],
                })
            fixed_results.append(result)

    # Save fix manifest
    fix_manifest = {
        'course': course_key,
        'fixed_count': len(fixed_results),
        'skipped_count': len(skipped),
        'total_images_needing_alt': sum(len(e['images']) for e in all_images),
        'fixed': [{k: v for k, v in r.items() if k != 'images_detail'} for r in fixed_results],
        'skipped': skipped,
    }

    # Save images needing alt text
    if all_images:
        imgs_filename = f"images_needing_alt_{course_key}.json"
        save_json(all_images, imgs_filename)
        print(f"\nImages metadata saved to data/{imgs_filename}")

    return fix_manifest


def main():
    if len(sys.argv) < 2:
        from bb_utils import load_courses
        print("Usage: python phase4_fix.py <course_key>")
        print(f"Known courses: {', '.join(load_courses().keys())}")
        sys.exit(1)

    course_key = sys.argv[1].upper()
    manifest = fix_all(course_key)

    filename = fix_manifest_filename(course_key)
    save_json(manifest, filename)
    print(f"\nSaved fix manifest to data/{filename}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Phase 4 Results: {course_key}")
    print(f"{'='*60}")
    print(f"  Fixed:   {manifest['fixed_count']}")
    print(f"  Skipped: {manifest['skipped_count']}")
    print(f"  Images needing alt text: {manifest['total_images_needing_alt']}")

    if manifest['skipped']:
        print(f"\n  Skipped files:")
        for s in manifest['skipped']:
            print(f"    - {s['report_name']}: {s['reason']}")

    if manifest['total_images_needing_alt'] > 0:
        print(f"\n  *** Run phase4b_apply_alts.py after generating alt texts ***")


if __name__ == '__main__':
    main()
