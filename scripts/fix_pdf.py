"""Fix PDF accessibility issues: tagging, language, and title.

Applies the following fixes to a PDF:
1. Add structure tags (StructTreeRoot + MarkInfo) if missing
2. Set document language to en-US if missing
3. Set document title from filename if missing

Usage:
    python fix_pdf.py <input.pdf>                   # Fix in place (saves to <input>_fixed.pdf)
    python fix_pdf.py <input.pdf> -o <output.pdf>   # Fix to specific output
    python fix_pdf.py <input.pdf> --title "My Title" # Set custom title
    python fix_pdf.py <input.pdf> --lang fr          # Set custom language
    python fix_pdf.py --scan <directory>             # Scan directory and report issues
"""
import pikepdf
import os
import sys
import argparse
import re


def scan_pdf(pdf_path):
    """Check a PDF for accessibility issues. Returns dict of issues found."""
    issues = {}
    try:
        pdf = pikepdf.open(pdf_path)
    except Exception as e:
        return {'error': str(e)}

    # Check tags
    has_struct = '/StructTreeRoot' in pdf.Root
    has_mark = '/MarkInfo' in pdf.Root and bool(pdf.Root['/MarkInfo'].get('/Marked'))
    if not has_struct or not has_mark:
        issues['untagged'] = True

    # Check language
    if '/Lang' not in pdf.Root:
        issues['no_language'] = True

    # Check title
    has_title = False
    if '/Info' in pdf.trailer and '/Title' in pdf.trailer['/Info']:
        title = str(pdf.trailer['/Info']['/Title'])
        if title and title.strip():
            has_title = True
    # Also check XMP metadata
    try:
        with pdf.open_metadata() as meta:
            xmp_title = meta.get('dc:title', '')
            if xmp_title and xmp_title.strip():
                has_title = True
    except:
        pass
    if not has_title:
        issues['no_title'] = True

    issues['pages'] = len(pdf.pages)
    pdf.close()
    return issues


def title_from_filename(filename):
    """Derive a readable title from a filename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    # Remove _tagged, _fixed suffixes
    name = re.sub(r'_(tagged|fixed)$', '', name)
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    return name.strip()


def add_tags(pdf):
    """Add a basic structure tree to an untagged PDF."""
    pdf.Root.MarkInfo = pikepdf.Dictionary({'/Marked': True})

    struct_tree = pdf.make_indirect(pikepdf.Dictionary({
        '/Type': pikepdf.Name('/StructTreeRoot'),
        '/ParentTree': pikepdf.Dictionary({
            '/Nums': pikepdf.Array([]),
        }),
        '/K': pikepdf.Array([]),
    }))

    doc_elem = pdf.make_indirect(pikepdf.Dictionary({
        '/Type': pikepdf.Name('/StructElem'),
        '/S': pikepdf.Name('/Document'),
        '/P': struct_tree,
        '/K': pikepdf.Array([]),
    }))

    parent_tree_nums = []

    for i, page in enumerate(pdf.pages):
        page_ref = page.obj

        page_elem = pdf.make_indirect(pikepdf.Dictionary({
            '/Type': pikepdf.Name('/StructElem'),
            '/S': pikepdf.Name('/Part'),
            '/P': doc_elem,
            '/K': pikepdf.Array([]),
            '/Pg': page_ref,
        }))

        para_elem = pdf.make_indirect(pikepdf.Dictionary({
            '/Type': pikepdf.Name('/StructElem'),
            '/S': pikepdf.Name('/P'),
            '/P': page_elem,
            '/K': pikepdf.Array([pikepdf.Dictionary({
                '/Type': pikepdf.Name('/MCR'),
                '/Pg': page_ref,
                '/MCID': i,
            })]),
            '/Pg': page_ref,
        }))

        page_elem['/K'].append(para_elem)
        doc_elem['/K'].append(page_elem)

        parent_tree_nums.append(i)
        parent_tree_nums.append(pikepdf.Array([para_elem]))

        page['/StructParents'] = i

    struct_tree['/ParentTree']['/Nums'] = pikepdf.Array(parent_tree_nums)
    struct_tree['/K'] = pikepdf.Array([doc_elem])
    pdf.Root.StructTreeRoot = struct_tree


def set_language(pdf, lang='en-US'):
    """Set the document language."""
    pdf.Root['/Lang'] = pikepdf.String(lang)
    try:
        with pdf.open_metadata() as meta:
            meta['dc:language'] = [lang]
    except:
        pass


def set_title(pdf, title):
    """Set the document title."""
    # Set in Info dictionary
    if '/Info' not in pdf.trailer:
        pdf.trailer['/Info'] = pikepdf.Dictionary()
    pdf.trailer['/Info']['/Title'] = pikepdf.String(title)
    # Set in XMP metadata
    try:
        with pdf.open_metadata() as meta:
            meta['dc:title'] = title
    except:
        pass


def fix_pdf(input_path, output_path=None, title=None, lang='en-US', semantic=None):
    """Fix all accessibility issues in a PDF.

    If semantic is provided (dict with semantic_title and/or language), its
    values take precedence over the filename-derived title and the default
    language. The explicit title/lang arguments still win over semantic when
    both are given — this lets callers force a value.

    Returns dict with what was fixed.
    """
    if output_path is None:
        stem, ext = os.path.splitext(input_path)
        output_path = stem + '_fixed' + ext

    if semantic:
        if not title and semantic.get('semantic_title'):
            title = semantic['semantic_title']
        if semantic.get('language'):
            lang = semantic['language']

    issues = scan_pdf(input_path)
    if 'error' in issues:
        return {'error': issues['error']}

    if not any(k in issues for k in ('untagged', 'no_language', 'no_title')):
        return {'status': 'no issues found', 'pages': issues['pages']}

    pdf = pikepdf.open(input_path)
    fixed = []

    if issues.get('untagged'):
        add_tags(pdf)
        fixed.append('tagged')

    if issues.get('no_language'):
        set_language(pdf, lang)
        fixed.append('language')

    # Write title if missing. Also write it unconditionally when the caller
    # supplied an explicit title or a validated semantic title: the existing
    # title may be a tooling placeholder (e.g. "Microsoft PowerPoint - foo")
    # that Ally rejects even though scan_pdf considers it non-empty.
    semantic_title = (semantic or {}).get('semantic_title') if semantic else None
    if issues.get('no_title') or title or semantic_title:
        doc_title = title or semantic_title or title_from_filename(input_path)
        set_title(pdf, doc_title)
        fixed.append('title')

    pdf.save(output_path)
    pdf.close()

    return {
        'status': 'fixed',
        'fixed': fixed,
        'pages': issues['pages'],
        'output': output_path,
        'size': os.path.getsize(output_path),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fix PDF accessibility issues')
    parser.add_argument('input', help='PDF file to fix, or directory to scan with --scan')
    parser.add_argument('-o', '--output', help='Output path (default: <input>_fixed.pdf)')
    parser.add_argument('--title', help='Document title (default: derived from filename)')
    parser.add_argument('--lang', default='en-US', help='Document language (default: en-US)')
    parser.add_argument('--scan', action='store_true', help='Scan directory for issues without fixing')
    args = parser.parse_args()

    if args.scan:
        # Scan mode: report issues for all PDFs in directory
        target = args.input
        if os.path.isfile(target):
            files = [target]
        else:
            files = []
            for root, dirs, fnames in os.walk(target):
                for fn in sorted(fnames):
                    if fn.lower().endswith('.pdf'):
                        files.append(os.path.join(root, fn))

        print(f'Scanning {len(files)} PDF files...\n')
        needs_fix = 0
        for fpath in files:
            issues = scan_pdf(fpath)
            fname = os.path.basename(fpath)
            problems = []
            if issues.get('untagged'):
                problems.append('UNTAGGED')
            if issues.get('no_language'):
                problems.append('NO LANG')
            if issues.get('no_title'):
                problems.append('NO TITLE')
            if problems:
                needs_fix += 1
                print(f'  {fname[:60]:60s}  {issues.get("pages", "?"):>4}pg  {" | ".join(problems)}')
            else:
                print(f'  {fname[:60]:60s}  {issues.get("pages", "?"):>4}pg  OK')

        print(f'\n{needs_fix}/{len(files)} files need fixing')
    else:
        # Fix mode
        result = fix_pdf(args.input, args.output, args.title, args.lang)
        if result.get('error'):
            print(f'ERROR: {result["error"]}')
            sys.exit(1)
        elif result['status'] == 'no issues found':
            print(f'No fixable issues found ({result["pages"]} pages)')
        else:
            print(f'Fixed: {", ".join(result["fixed"])}')
            print(f'Pages: {result["pages"]}')
            print(f'Output: {result["output"]} ({result["size"]:,} bytes)')
