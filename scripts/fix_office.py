"""Fix accessibility issues in PowerPoint (.pptx) and Word (.docx) files.

Fixes:
- Set document title and language
- PPTX: ensure all slides have titles
- PPTX: add alt text to images (extract images for external description)

Usage:
    python fix_office.py <input.pptx>              # Fix in place (_fixed.pptx)
    python fix_office.py <input.docx> --scan        # Just show issues
    python fix_office.py <input.pptx> --title "My Slides"
    python fix_office.py <input.pptx> --extract-images /tmp/imgs  # Extract images for alt text
    python fix_office.py <input.pptx> --alt-texts alt.json        # Apply alt texts from JSON
"""
import os
import sys
import json
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
                    './/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
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


def extract_docx_images(path, output_dir):
    """Extract images without alt text from DOCX. Returns list of image info dicts.
    Each dict: {index, image_path, context}"""
    from lxml import etree
    doc = Document(path)
    os.makedirs(output_dir, exist_ok=True)
    images = []

    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    }

    body = doc.element.body
    drawings = body.findall('.//w:drawing', ns)

    for i, drawing in enumerate(drawings):
        # Find docPr for alt text check
        doc_pr = drawing.find('.//wp:docPr', ns)
        if doc_pr is not None and doc_pr.get('descr', '').strip():
            continue  # Already has alt text

        # Get image data via relationship
        blip = drawing.find('.//a:blip', ns)
        if blip is None:
            continue

        embed = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
        if not embed or embed not in doc.part.rels:
            continue

        rel = doc.part.rels[embed]
        img_data = rel.target_part.blob
        ext = rel.target_part.content_type.split('/')[-1]
        if ext == 'jpeg':
            ext = 'jpg'

        img_name = f'image_{i}.{ext}'
        img_path = os.path.join(output_dir, img_name)
        with open(img_path, 'wb') as f:
            f.write(img_data)

        # Get surrounding text for context
        parent_para = drawing.getparent()
        context = ''
        if parent_para is not None:
            # Get text from nearby paragraphs
            all_paras = list(body.findall('.//w:p', ns))
            try:
                idx = all_paras.index(parent_para)
                nearby = all_paras[max(0, idx-2):idx+3]
                for p in nearby:
                    text = ''.join(t.text or '' for t in p.findall('.//w:t', ns))
                    if text.strip():
                        context += text.strip() + ' '
            except ValueError:
                pass

        images.append({
            'index': i,
            'image_path': img_path,
            'context': context.strip()[:500],
        })

    return images


def apply_docx_alt_texts(input_path, output_path, alt_texts):
    """Apply alt texts to images in a DOCX file.
    alt_texts: list of {index, alt_text} dicts."""
    from lxml import etree
    doc = Document(input_path)

    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    }

    # Build lookup
    texts = {}
    for item in alt_texts:
        texts[item['index']] = item['alt_text']

    body = doc.element.body
    drawings = body.findall('.//w:drawing', ns)

    applied = 0
    for i, drawing in enumerate(drawings):
        if i not in texts:
            continue

        doc_pr = drawing.find('.//wp:docPr', ns)
        if doc_pr is not None:
            doc_pr.set('descr', texts[i])
            applied += 1

    if applied > 0:
        doc.save(output_path)

    return {'applied': applied, 'total': len(texts)}


def extract_pptx_images(path, output_dir):
    """Extract images without alt text from PPTX. Returns list of image info dicts.
    Each dict: {slide, shape_idx, image_path, slide_text}"""
    prs = Presentation(path)
    os.makedirs(output_dir, exist_ok=True)
    images = []

    for slide_num, slide in enumerate(prs.slides):
        # Get slide text for context
        slide_text = ''
        for shape in slide.shapes:
            if shape.has_text_frame:
                slide_text += shape.text_frame.text + '\n'
        slide_text = slide_text.strip()[:500]

        for shape_idx, shape in enumerate(slide.shapes):
            if not hasattr(shape, 'image'):
                continue

            # Check if it already has alt text
            nv = shape._element.find(
                './/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
            if nv is not None and nv.get('descr', '').strip():
                continue  # Already has alt text

            # Save image
            image = shape.image
            ext = image.content_type.split('/')[-1]
            if ext == 'jpeg':
                ext = 'jpg'
            img_name = f'slide{slide_num + 1}_shape{shape_idx}.{ext}'
            img_path = os.path.join(output_dir, img_name)

            with open(img_path, 'wb') as f:
                f.write(image.blob)

            images.append({
                'slide': slide_num,
                'shape_idx': shape_idx,
                'image_path': img_path,
                'slide_text': slide_text,
            })

    return images


def apply_pptx_alt_texts(input_path, output_path, alt_texts):
    """Apply alt texts to images in a PPTX file.
    alt_texts: dict mapping 'slideN_shapeM' -> description string,
               or list of {slide, shape_idx, alt_text} dicts."""
    prs = Presentation(input_path)

    # Normalize alt_texts to a dict keyed by (slide, shape_idx)
    texts = {}
    if isinstance(alt_texts, list):
        for item in alt_texts:
            texts[(item['slide'], item['shape_idx'])] = item['alt_text']
    elif isinstance(alt_texts, dict):
        for key, val in alt_texts.items():
            # Parse 'slide1_shape0' format
            parts = key.replace('slide', '').replace('shape', '').split('_')
            if len(parts) == 2:
                texts[(int(parts[0]) - 1, int(parts[1]))] = val

    applied = 0
    for slide_num, slide in enumerate(prs.slides):
        for shape_idx, shape in enumerate(slide.shapes):
            if (slide_num, shape_idx) not in texts:
                continue
            if not hasattr(shape, 'image'):
                continue

            desc = texts[(slide_num, shape_idx)]
            nv = shape._element.find(
                './/{http://schemas.openxmlformats.org/presentationml/2006/main}cNvPr')
            if nv is not None:
                nv.set('descr', desc)
                applied += 1

    if applied > 0:
        prs.save(output_path)

    return {'applied': applied, 'total': len(texts)}


def fix_pptx(input_path, output_path=None, title=None, lang='en-US', alt_texts=None):
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

    # Fix table headers: set firstRow="1" on tblPr for all tables
    tables_fixed = 0
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_table:
                tbl_el = shape.table._tbl
                ns_a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
                tblPr = tbl_el.find(f'{{{ns_a}}}tblPr')
                if tblPr is None:
                    from lxml import etree
                    tblPr = etree.SubElement(tbl_el, f'{{{ns_a}}}tblPr')
                    tbl_el.insert(0, tblPr)
                if tblPr.get('firstRow') != '1':
                    tblPr.set('firstRow', '1')
                    tblPr.set('bandRow', '1')
                    tables_fixed += 1

    if tables_fixed > 0:
        fixed.append(f'{tables_fixed} table headers')

    # Save intermediate if we have changes so far, or just copy for alt text step
    if fixed or alt_texts:
        prs.save(output_path)

    # Apply alt texts if provided (must be done after save since it re-opens the file)
    if alt_texts:
        result = apply_pptx_alt_texts(output_path if os.path.exists(output_path) else input_path,
                                      output_path, alt_texts)
        if result['applied'] > 0:
            fixed.append(f"{result['applied']} image alt texts")

    if not fixed:
        return {'status': 'no issues found'}

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

            # Ensure heading styles exist
            def get_heading_style(doc, level):
                name = f'Heading {level}'
                try:
                    return doc.styles[name]
                except KeyError:
                    from docx.shared import Pt as DPt
                    style = doc.styles.add_style(name, 1)  # 1 = paragraph
                    style.base_style = doc.styles['Normal']
                    style.font.bold = True
                    style.font.size = DPt(16 - (level - 1) * 2)
                    return style

            for para in doc.paragraphs:
                if not para.text.strip():
                    continue
                max_size = 0
                for run in para.runs:
                    if run.font.size and run.font.size > max_size:
                        max_size = run.font.size
                if max_size in heading_map:
                    level = int(heading_map[max_size].split()[-1])
                    para.style = get_heading_style(doc, level)
                    headings_added += 1

        # Method 2: If no font size hierarchy, detect by patterns
        # (short bold text, text ending with ":", numbered sections)
        if headings_added == 0:
            import re

            def get_heading_style_safe(doc, level=1):
                name = f'Heading {level}'
                try:
                    return doc.styles[name]
                except KeyError:
                    from docx.shared import Pt as DPt
                    style = doc.styles.add_style(name, 1)
                    style.base_style = doc.styles['Normal']
                    style.font.bold = True
                    style.font.size = DPt(16 - (level - 1) * 2)
                    return style

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
                    para.style = get_heading_style_safe(doc)
                    headings_added += 1

        if headings_added > 0:
            fixed.append(f'{headings_added} headings')

    # Fix table headers: mark first row of ALL tables (including nested) as header
    from lxml import etree
    from docx.oxml.ns import qn
    tables_fixed = 0
    all_tables = doc.element.body.findall('.//' + qn('w:tbl'))
    for tbl in all_tables:
        rows = tbl.findall(qn('w:tr'))
        if not rows:
            continue
        first_row = rows[0]
        trPr = first_row.find(qn('w:trPr'))
        if trPr is None:
            trPr = etree.SubElement(first_row, qn('w:trPr'))
            first_row.insert(0, trPr)
        tblHeader = trPr.find(qn('w:tblHeader'))
        if tblHeader is None:
            etree.SubElement(trPr, qn('w:tblHeader'))
            tables_fixed += 1

    if tables_fixed > 0:
        fixed.append(f'{tables_fixed} table headers')

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
    parser.add_argument('--extract-images', metavar='DIR',
                        help='Extract images without alt text to DIR (PPTX only)')
    parser.add_argument('--alt-texts', metavar='JSON',
                        help='Apply alt texts from JSON file (PPTX only)')
    args = parser.parse_args()

    ext = os.path.splitext(args.input)[1].lower()

    if args.extract_images:
        if ext != '.pptx':
            print('--extract-images only works with PPTX files')
            sys.exit(1)
        images = extract_pptx_images(args.input, args.extract_images)
        print(f'Extracted {len(images)} images without alt text:')
        for img in images:
            print(f"  Slide {img['slide']+1}, shape {img['shape_idx']}: {img['image_path']}")
        # Save metadata
        meta_path = os.path.join(args.extract_images, 'images_meta.json')
        with open(meta_path, 'w') as f:
            json.dump(images, f, indent=2)
        print(f'Metadata saved to {meta_path}')
    elif args.scan:
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
        alt_texts = None
        if args.alt_texts:
            with open(args.alt_texts) as f:
                alt_texts = json.load(f)

        if ext == '.pptx':
            result = fix_pptx(args.input, args.output, args.title, args.lang, alt_texts)
        elif ext == '.docx':
            result = fix_docx(args.input, args.output, args.title, args.lang)
        else:
            result = fix_office(args.input, args.output, args.title, args.lang)

        if result['status'] == 'fixed':
            print(f"Fixed: {', '.join(result['fixed'])}")
            print(f"Output: {result['output']} ({result['size']:,} bytes)")
        else:
            print(f"Status: {result['status']}")
