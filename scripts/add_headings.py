"""Add heading structure to PDFs based on font size analysis.

Detects headings by analyzing font sizes across the document:
- Largest font size = H1 (slide/section titles)
- Second largest = H2 (sub-headings)
- Third largest = H3

Usage:
    python add_headings.py <input.pdf>                  # Fix in place (_fixed.pdf)
    python add_headings.py <input.pdf> --scan           # Just show detected headings
    python add_headings.py <input.pdf> -o <output.pdf>  # Custom output path
"""
import pymupdf
import pikepdf
import os
import sys
import argparse
from collections import Counter


def analyze_fonts(pdf_path):
    """Analyze font sizes across the document. Returns sorted list of (size, font, count)."""
    doc = pymupdf.open(pdf_path)
    font_counter = Counter()

    for page in doc:
        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if len(text) < 2:
                        continue
                    size = round(span['size'], 0)
                    font_counter[size] += 1

    doc.close()
    return font_counter


def detect_heading_sizes(font_counter):
    """Determine which font sizes are headings vs body text.
    Returns dict mapping font_size -> heading level (1, 2, 3) or None for body."""
    if not font_counter:
        return {}

    # Sort sizes descending
    sizes = sorted(font_counter.keys(), reverse=True)

    # Body text is the most frequently used size
    body_size = max(font_counter, key=font_counter.get)

    # Sizes larger than body text are headings
    heading_sizes = [s for s in sizes if s > body_size]

    mapping = {}
    for i, size in enumerate(heading_sizes[:3]):
        mapping[size] = i + 1  # H1, H2, H3

    return mapping, body_size


def extract_headings(pdf_path, heading_map):
    """Extract headings from the PDF based on font size mapping.
    Returns list of {page, level, text} dicts."""
    doc = pymupdf.open(pdf_path)
    headings = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                # Check if any span in this line is a heading size
                line_text = ''
                max_size = 0
                for span in line['spans']:
                    text = span['text'].strip()
                    if text:
                        line_text += text + ' '
                        max_size = max(max_size, round(span['size'], 0))

                line_text = line_text.strip()
                if not line_text or len(line_text) < 2:
                    continue

                if max_size in heading_map:
                    level = heading_map[max_size]
                    headings.append({
                        'page': page_num,
                        'level': level,
                        'text': line_text[:200],
                        'size': max_size,
                    })

    doc.close()
    return _normalize_heading_levels(headings)


def _normalize_heading_levels(headings):
    """Ensure headings start at H1 and have no level gaps.

    Ally flags "Headings do not begin at heading level 1" and "do not
    follow a logical order" when there are gaps (e.g., H2 without H1) or
    jumps (H1 to H3 with no H2).

    This function compresses the used levels to a contiguous 1-based
    sequence: the smallest used level becomes H1, the next becomes H2, etc.
    """
    if not headings:
        return headings
    used_levels = sorted(set(h['level'] for h in headings))
    if not used_levels:
        return headings
    remap = {old: new for new, old in enumerate(used_levels, start=1)}
    for h in headings:
        h['level'] = remap[h['level']]
    return headings


def _match_headings_to_pages(pdf_path, heading_list):
    """Given a list of {text, level, locator:{page, anchor_text}} items,
    return list of {page, level, text} matched against the actual PDF text.

    Uses locator.page directly; if anchor_text is present and doesn't appear
    on that page, falls back to scanning neighboring pages (+/-1) for the
    anchor. Headings that can't be located at all are dropped.
    """
    import pymupdf
    doc = pymupdf.open(pdf_path)
    total = len(doc)
    results = []
    try:
        for h in heading_list:
            text = str(h.get('text', '')).strip()
            if not text:
                continue
            try:
                level = int(h.get('level', 1))
            except Exception:
                level = 1
            level = max(1, min(3, level))

            locator = h.get('locator') or {}
            page = locator.get('page')
            anchor = (locator.get('anchor_text') or text).strip()[:40].lower()

            if not isinstance(page, int) or page < 0 or page >= total:
                # Try to find anchor in any page
                found_page = None
                for p in range(total):
                    try:
                        if anchor in doc[p].get_text().lower():
                            found_page = p
                            break
                    except Exception:
                        continue
                if found_page is None:
                    continue
                page = found_page
            else:
                # Verify anchor on that page; fall back to +/-1 if missing.
                try:
                    page_text = doc[page].get_text().lower()
                except Exception:
                    page_text = ''
                if anchor and anchor not in page_text:
                    for delta in (-1, 1):
                        alt = page + delta
                        if 0 <= alt < total:
                            try:
                                if anchor in doc[alt].get_text().lower():
                                    page = alt
                                    break
                            except Exception:
                                pass

            results.append({'page': page, 'level': level, 'text': text[:200]})
    finally:
        doc.close()
    return _normalize_heading_levels(results)


def add_headings_to_pdf(input_path, output_path=None, title=None, lang='en-US',
                        heading_override=None):
    """Add heading structure elements to a PDF.

    If heading_override (list of {text, level, locator}) is provided, it is
    used instead of the font-size heuristic. Each heading is anchored to a
    page by locator.page (with anchor_text fallback). Font-size detection
    remains the path for uncontrolled input.

    Returns dict with results."""
    if output_path is None:
        stem, ext = os.path.splitext(input_path)
        # If already has _fixed suffix, overwrite it
        if stem.endswith('_fixed'):
            output_path = input_path
        else:
            output_path = stem + '_fixed' + ext

    heading_map = None
    body_size = None
    headings = []

    if heading_override:
        headings = _match_headings_to_pages(input_path, heading_override)
        if not headings:
            return {'status': 'no headings found (override supplied but unmatched)'}
    else:
        # Analyze fonts and detect headings
        font_counter = analyze_fonts(input_path)
        if not font_counter:
            return {'status': 'no text found'}

        heading_map, body_size = detect_heading_sizes(font_counter)
        if not heading_map:
            return {'status': 'no headings detected (single font size)'}

        headings = extract_headings(input_path, heading_map)
        if not headings:
            return {'status': 'no headings found'}

    # Group headings by page
    headings_by_page = {}
    for h in headings:
        pg = h['page']
        if pg not in headings_by_page:
            headings_by_page[pg] = []
        headings_by_page[pg].append(h)

    # Build the tagged PDF with pikepdf
    allow_overwrite = (os.path.abspath(input_path) == os.path.abspath(output_path))
    pdf = pikepdf.open(input_path, allow_overwriting_input=allow_overwrite)

    # Set metadata
    if '/MarkInfo' not in pdf.Root:
        pdf.Root.MarkInfo = pikepdf.Dictionary({'/Marked': True})
    else:
        pdf.Root['/MarkInfo']['/Marked'] = True

    if '/Lang' not in pdf.Root:
        pdf.Root['/Lang'] = pikepdf.String(lang)

    if title:
        if '/Info' not in pdf.trailer:
            pdf.trailer['/Info'] = pikepdf.Dictionary()
        pdf.trailer['/Info']['/Title'] = pikepdf.String(title)
        try:
            with pdf.open_metadata() as meta:
                meta['dc:title'] = title
                meta['dc:language'] = [lang]
        except:
            pass

    # Build structure tree
    struct_tree = pdf.make_indirect(pikepdf.Dictionary({
        '/Type': pikepdf.Name('/StructTreeRoot'),
        '/ParentTree': pikepdf.Dictionary({'/Nums': pikepdf.Array([])}),
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

        mcid_counter = i * 100

        # Add heading elements for this page.
        # NOTE: MCIDs generated here do not correspond to marked content in
        # the page's content stream (adding those would require rewriting
        # every page's content ops). Instead, we attach /ActualText to each
        # heading struct element — screen readers read /ActualText verbatim
        # when they walk the struct tree, so the hierarchy and heading text
        # are both conveyed to AT users without touching content streams.
        if i in headings_by_page:
            for h in headings_by_page[i]:
                h_name = f'/H{h["level"]}'
                h_elem = pdf.make_indirect(pikepdf.Dictionary({
                    '/Type': pikepdf.Name('/StructElem'),
                    '/S': pikepdf.Name(h_name),
                    '/P': page_elem,
                    '/K': pikepdf.Array([pikepdf.Dictionary({
                        '/Type': pikepdf.Name('/MCR'),
                        '/Pg': page_ref,
                        '/MCID': mcid_counter,
                    })]),
                    '/Pg': page_ref,
                    '/ActualText': pikepdf.String(h['text']),
                    '/Alt': pikepdf.String(h['text']),
                }))
                page_elem['/K'].append(h_elem)
                mcid_counter += 1

        # Add a paragraph element for remaining content
        para_elem = pdf.make_indirect(pikepdf.Dictionary({
            '/Type': pikepdf.Name('/StructElem'),
            '/S': pikepdf.Name('/P'),
            '/P': page_elem,
            '/K': pikepdf.Array([pikepdf.Dictionary({
                '/Type': pikepdf.Name('/MCR'),
                '/Pg': page_ref,
                '/MCID': mcid_counter,
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

    pdf.save(output_path)
    pdf.close()

    result = {
        'status': 'fixed',
        'headings_found': len(headings),
        'pages_with_headings': len(headings_by_page),
        'output': output_path,
        'size': os.path.getsize(output_path),
        'source': 'override' if heading_override else 'font-size',
    }
    if heading_map is not None:
        result['heading_sizes'] = {f'H{v}': f'{k}pt' for k, v in heading_map.items()}
        result['body_size'] = f'{body_size}pt'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add heading structure to PDFs')
    parser.add_argument('input', help='PDF file to process')
    parser.add_argument('-o', '--output', help='Output path')
    parser.add_argument('--title', help='Document title')
    parser.add_argument('--lang', default='en-US', help='Language (default: en-US)')
    parser.add_argument('--scan', action='store_true', help='Just show detected headings')
    args = parser.parse_args()

    if args.scan:
        font_counter = analyze_fonts(args.input)
        heading_map, body_size = detect_heading_sizes(font_counter)
        headings = extract_headings(args.input, heading_map)

        print(f'Body text size: {body_size}pt')
        print(f'Heading mapping: {heading_map}')
        print(f'\nDetected {len(headings)} headings:\n')
        for h in headings:
            indent = '  ' * (h['level'] - 1)
            print(f"  pg{h['page']:3d}  H{h['level']}  {indent}{h['text'][:80]}")
    else:
        result = add_headings_to_pdf(args.input, args.output, args.title, args.lang)
        if result['status'] == 'fixed':
            print(f"Added {result['headings_found']} headings across {result['pages_with_headings']} pages")
            if 'heading_sizes' in result:
                print(f"Heading sizes: {result['heading_sizes']}")
                print(f"Body size: {result['body_size']}")
            print(f"Output: {result['output']} ({result['size']:,} bytes)")
        else:
            print(f"Status: {result['status']}")
