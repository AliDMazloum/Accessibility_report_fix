"""Apply alt text to PPTX images using Claude's vision capabilities."""

import os
import sys
import json
import base64
from pathlib import Path
from fix_office import apply_pptx_alt_texts
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic()

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def get_image_type(image_path):
    """Get image media type from file extension."""
    ext = Path(image_path).suffix.lower()
    type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    return type_map.get(ext, 'image/png')

def generate_alt_text_batch(image_paths, context=''):
    """Generate alt text for multiple images using Claude with conversation context.
    Returns dict mapping image path to alt text."""

    alt_texts = {}
    conversation = []

    # Start with system context
    system_msg = """You are generating concise, descriptive alt text for technical diagrams and slides from a networking course lecture.

For each image, provide a 1-2 sentence alt text that:
- Describes the main content and purpose of the diagram
- Includes relevant technical terms and labels visible in the image
- Avoids unnecessary details but captures the essential information
- Is clear to someone who cannot see the image

Format your response as JSON with the image filename as key and alt text as value.
Example: {"slide1_shape0.png": "Network topology diagram showing router A connected to router B with a 10Mbps link."}"""

    print(f"Generating alt text for {len(image_paths)} images...")

    # Process images in batches of 5 to stay within context limits
    for batch_start in range(0, len(image_paths), 5):
        batch_end = min(batch_start + 5, len(image_paths))
        batch = image_paths[batch_start:batch_end]

        print(f"  Processing images {batch_start + 1}-{batch_end}...")

        # Build user message with all images in batch
        user_content = [
            {
                "type": "text",
                "text": f"Please generate alt text for these {len(batch)} images from a networking course lecture. Be concise (1-2 sentences each)."
            }
        ]

        # Add each image to the message
        for img_path in batch:
            image_data = encode_image(img_path)
            image_type = get_image_type(img_path)
            filename = Path(img_path).name

            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_type,
                    "data": image_data,
                }
            })
            user_content.append({
                "type": "text",
                "text": f"Image: {filename}"
            })

        # Send to Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            system=system_msg,
            messages=[
                {
                    "role": "user",
                    "content": user_content
                }
            ]
        )

        # Parse response
        response_text = response.content[0].text

        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                batch_alts = json.loads(json_str)
                alt_texts.update(batch_alts)
            else:
                print(f"Warning: Could not parse JSON from response")
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON response: {e}")
            print(f"Response: {response_text[:200]}")

    return alt_texts

def process_pptx_file(pptx_path):
    """Process a PPTX file: read images, generate alt text, apply to PPTX."""

    # Determine _imgs directory
    stem = Path(pptx_path).stem
    # Remove _fixed suffix if present
    if stem.endswith('_fixed'):
        stem = stem[:-6]

    parent_dir = Path(pptx_path).parent
    imgs_dir = parent_dir / f'_imgs_{stem}'

    if not imgs_dir.exists():
        print(f"Error: {imgs_dir} does not exist")
        return False

    # Get all PNG images
    image_files = sorted(list(imgs_dir.glob('*.png')))
    if not image_files:
        print(f"No images found in {imgs_dir}")
        return False

    print(f"\nProcessing {Path(pptx_path).name}")
    print(f"  Found {len(image_files)} images in {imgs_dir.name}")

    # Generate alt text for all images
    image_paths = [str(f) for f in image_files]
    alt_texts_dict = generate_alt_text_batch(image_paths)

    if not alt_texts_dict:
        print(f"Failed to generate alt text")
        return False

    # Convert to list format expected by apply_pptx_alt_texts
    # Keys are like "slide3_shape4.png", we need to convert to {slide, shape_idx, alt_text}
    alt_texts_list = []
    for img_filename, alt_text in alt_texts_dict.items():
        # Parse filename: slide3_shape4.png -> slide=2 (0-indexed), shape_idx=4
        name_part = img_filename.replace('.png', '')
        parts = name_part.replace('slide', '').split('_shape')
        if len(parts) == 2:
            try:
                slide = int(parts[0]) - 1  # Convert to 0-indexed
                shape_idx = int(parts[1])
                alt_texts_list.append({
                    'slide': slide,
                    'shape_idx': shape_idx,
                    'alt_text': alt_text
                })
            except ValueError:
                print(f"Warning: Could not parse {img_filename}")
                continue

    if not alt_texts_list:
        print(f"Failed to convert alt texts to list format")
        return False

    # Apply alt texts to PPTX
    output_path = str(pptx_path)
    try:
        result = apply_pptx_alt_texts(str(pptx_path), output_path, alt_texts_list)
        print(f"  Applied: {result['applied']} alt texts (of {result['total']})")
        return True
    except Exception as e:
        print(f"Error applying alt texts: {e}")
        return False

def main():
    """Process all PPTX files."""

    base_dir = "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing"

    files = [
        "Lecture 1 - Static Routing_fixed.pptx",
        "Lecture 2 - Default Route_fixed.pptx",
        "Lecture 4 - Static Host Routes_fixed.pptx",
    ]

    results = {
        'success': [],
        'failed': []
    }

    for filename in files:
        pptx_path = os.path.join(base_dir, filename)
        if not os.path.exists(pptx_path):
            print(f"Error: {pptx_path} not found")
            results['failed'].append(filename)
            continue

        try:
            if process_pptx_file(pptx_path):
                results['success'].append(filename)
            else:
                results['failed'].append(filename)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            results['failed'].append(filename)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Successfully processed: {len(results['success'])}")
    for f in results['success']:
        print(f"  - {f}")
    if results['failed']:
        print(f"Failed: {len(results['failed'])}")
        for f in results['failed']:
            print(f"  - {f}")

    return len(results['failed']) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
