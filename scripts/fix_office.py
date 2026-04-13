"""Fix accessibility issues in PowerPoint (.pptx) and Word (.docx) files.

Fixes:
- Set document title and language
- PPTX: ensure all slides have titles
- (Alt text for images requires separate vision step)

Usage:
    python fix_office.py <input.pptx>              # Fix in place (_fixed.pptx)
    python fix_office.py <input.docx> --scan        # Just show issues
    python fix_office.py <input.pptx> --title "My Slides"
"""
import os
import sys
import argparse
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.enum.text import PP_ALIGN
from docx import Document


def scan_pptx(path):
    """Scan a PPTX for accessibility issues."""
    prs = Presentation(path)
    issues = {}

    if not prs.core_properties.title:
        issues['no_title'] = True
    if not prs.core_properties.language:
        issues['no_language'] = True

    slides_without_title = 0
    images_without_alt = 0
    total_images = 0

    for slide in prs.slides:
        has_title = slide.shapes.title is not None and slide.shapes.title.text.strip()
        if not has_title:
            slides_without_title += 1

        for shape in slide.shapes:
            if hasattr(shape, 'image'):
                total_images += 1
                nv = shape._element.find(
                    './/{http://schemas.openxmlformats.org/drawingml/2006/main}cNvPr')
                if nv is not None:
                    if not nv.get('descr', ''):
                        images_without_alt += 1
                else:
                    images_without_alt += 1

    if slides_without_title > 0:
        issues['slides_without_title'] = slides_without_title
    if images_without_alt > 0:
        issues['images_without_alt'] = images_without_alt
    issues['total_images'] = total_images
    issues['total_slides'] = len(prs.slides)

    return issues


def scan_docx(path):
    """Scan a DOCX for accessibility issues."""
    doc = Document(path)
    issues = {}

    if not doc.core_properties.title:
        issues['no_title'] = True
    if not doc.core_properties.language:
        issues['no_language'] = True

    # Check for headings
    has_headings = False
    for para in doc.paragraphs:
        if para.style.name.startswith('Heading'):
            has_headings = True
            break
    if not has_headings:
        issues['no_headings'] = True

    # Check images
    images_without_alt = 0
    total_images = 0
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            total_images += 1

    issues['total_images'] = total_images

    return issues


def fix_pptx(input_path, output_path=None, title=None, lang='en-US'):
    """Fix accessibility issues in a PPTX file."""
    if output_path is None:
        stem, ext = os.path.splitext(input_path)
        if stem.endswith('_fixed'):
            output_path = input_path
        else:
            output_path = stem + '_fixed' + ext

    prs = Presentation(input_path)
    fixed = []

    # Set title
    doc_title = title or os.path.splitext(os.path.basename(input_path))[0].replace('_', ' ')
    if not prs.core_properties.title:
        prs.core_properties.title = doc_title
        fixed.append('title')

    # Set language
    if not prs.core_properties.language:
        prs.core_properties.language = lang
        fixed.append('language')

    # Ensure all slides have titles
    slides_fixed = 0
    for i, slide in enumerate(prs.slides):
        has_title = slide.shapes.title is not None and slide.shapes.title.text.strip()
        if not has_title:
            # Try to find a text box that looks like a title (largest text)
            best_text = ''
            best_size = 0
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        for run in para.runs:
                            if run.font.size and run.font.size > best_size:
                                best_size = run.font.size
                                best_text = para.text.strip()
                            elif not run.font.size and para.text.strip() and not best_text:
                                best_text = para.text.strip()

            # If slide has a title placeholder but it's empty, fill it
            if slide.shapes.title is not None and best_text:
                slide.shapes.title.text = best_text
                slides_fixed += 1

    if slides_fixed > 0:
        fixed.append(f'{slides_fixed} slide titles')

    if not fixed:
        return {'status': 'no issues found'}

    prs.save(output_path)

    return {
        'status': 'fixed',
        'fixed': fixed,
        'output': output_path,
        'size': os.path.getsize(output_path),
    }


def fix_docx(input_path, output_path=None, title=None, lang='en-US'):
    """Fix accessibility issues in a DOCX file."""
    if output_path is None:
        stem, ext = os.path.splitext(input_path)
        if stem.endswith('_fixed'):
            output_path = input_path
        else:
            output_path = stem + '_fixed' + ext

    doc = Document(input_path)
    fixed = []

    # Set title
    doc_title = title or os.path.splitext(os.path.basename(input_path))[0].replace('_', ' ')
    if not doc.core_properties.title:
        doc.core_properties.title = doc_title
        fixed.append('title')

    # Set language
    if not doc.core_properties.language:
        doc.core_properties.language = lang
        fixed.append('language')

    # Add headings if none exist
    has_headings = any(p.style.name.startswith('Heading') for p in doc.paragraphs)
    if not has_headings:
        headings_added = 0

        # Method 1: Detect by font size hierarchy
        font_sizes = {}
        for para in doc.paragraphs:
            for run in para.runs:
                if run.font.size and para.text.strip():
                    size = run.font.size
                    if size not in font_sizes:
                        font_sizes[size] = 0
                    font_sizes[size] += 1

        if len(font_sizes) > 1:
            body_size = max(font_sizes, key=font_sizes.get)
            heading_sizes = sorted([s for s in font_sizes if s > body_size], reverse=True)

            heading_map = {}
            for i, size in enumerate(heading_sizes[:3]):
                heading_map[size] = f'Heading {i + 1}'

            for para in doc.paragraphs:
                if not para.text.strip():
                    continue
                max_size = 0
                for run in para.runs:
                    if run.font.size and run.font.size > max_size:
                        max_size = run.font.size
                if max_size in heading_map:
                    para.style = doc.styles[heading_map[max_size]]
                    headings_added += 1

        # Method 2: If no font size hierarchy, detect by patterns
        # (short bold text, text ending with ":", numbered sections)
        if headings_added == 0:
            import re
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                is_bold = all(r.bold for r in para.runs if r.text.strip()) and para.runs
                is_short = len(text) < 80
                looks_like_heading = (
                    (is_bold and is_short) or
                    re.match(r'^(Exercise|Question|Problem|Part|Section|Chapter)\s+\d', text, re.I) or
                    (is_short and text.endswith(':') and len(text) < 40)
                )
                if looks_like_heading:
                    para.style = doc.styles['Heading 1']
                    headings_added += 1

        if headings_added > 0:
            fixed.append(f'{headings_added} headings')

    if not fixed:
        return {'status': 'no issues found'}

    doc.save(output_path)

    return {
        'status': 'fixed',
        'fixed': fixed,
        'output': output_path,
        'size': os.path.getsize(output_path),
    }


def fix_office(input_path, output_path=None, title=None, lang='en-US'):
    """Fix any Office file based on extension."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext == '.pptx':
        return fix_pptx(input_path, output_path, title, lang)
    elif ext == '.docx':
        return fix_docx(input_path, output_path, title, lang)
    else:
        return {'status': f'unsupported format: {ext}'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fix Office file accessibility')
    parser.add_argument('input', help='PPTX or DOCX file')
    parser.add_argument('-o', '--output', help='Output path')
    parser.add_argument('--title', help='Document title')
    parser.add_argument('--lang', default='en-US', help='Language')
    parser.add_argument('--scan', action='store_true', help='Just scan for issues')
    args = parser.parse_args()

    ext = os.path.splitext(args.input)[1].lower()

    if args.scan:
        if ext == '.pptx':
            issues = scan_pptx(args.input)
        elif ext == '.docx':
            issues = scan_docx(args.input)
        else:
            print(f'Unsupported: {ext}')
            sys.exit(1)

        print(f'Issues found:')
        for k, v in issues.items():
            print(f'  {k}: {v}')
    else:
        result = fix_office(args.input, args.output, args.title, args.lang)
        if result['status'] == 'fixed':
            print(f"Fixed: {', '.join(result['fixed'])}")
            print(f"Output: {result['output']} ({result['size']:,} bytes)")
        else:
            print(f"Status: {result['status']}")
