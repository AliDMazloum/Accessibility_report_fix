#!/usr/bin/env python3
"""Test script to apply alt text to one PPTX file."""

import sys
from pathlib import Path

# Import the function from fix_office
sys.path.insert(0, str(Path(__file__).parent))
from fix_office import apply_pptx_alt_texts

# Test with first file
BASE_DIR = r"c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content"

file_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 2 - Switching Concepts/Module 2 - Switching Concepts 2 - Collision Domain_fixed.pptx"

alt_texts = [
    {
        "slide": 1,  # slide2 in filename = slide 1 (0-indexed)
        "shape_idx": 3,
        "alt_text": "NETGEAR network switch with multiple Ethernet ports showing PoE status indicators."
    }
]

print(f"Processing: {file_path.name}")
print(f"File exists: {file_path.exists()}")

result = apply_pptx_alt_texts(str(file_path), str(file_path), alt_texts)
print(f"Result: {result}")
print("Done!")
