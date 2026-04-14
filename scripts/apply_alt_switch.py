#!/usr/bin/env python3
"""
Apply alt text to switch fundamentals image.
Image shows network topology with switches, VLANs, and VLAN assignments.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fix_office import apply_docx_alt_texts

input_file = r"c:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Pre-Midterm Review\switch fundamentals_fixed.docx"

output_file = input_file  # Overwrite the _fixed.docx file

# Alt texts for images: index, alt_text
# For DOCX: image_N.png means index=N
alt_texts = [
    {
        'index': 0,
        'alt_text': 'Network diagram with two interconnected switches and hub-PT in center. Left side (orange, VLAN 1) contains two computers connected through 2960-24TT switches labeled SW1 and SW0. Right side (green, VLAN 2) contains similar configuration with SW2. Network addresses shown as 192.168.1.0/24 and 192.168.2.0/24 for each VLAN.'
    }
]

print("Applying alt text to switch fundamentals DOCX...")
apply_docx_alt_texts(input_file, output_file, alt_texts)
print(f"Success! Alt text applied to {output_file}")
