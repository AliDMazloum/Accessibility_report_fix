#!/usr/bin/env python3
"""
Apply alt text to In-class Example 2 InterVLAN Communications image.
Image shows VLAN network topology with router and two computers using DHCP.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fix_office import apply_docx_alt_texts

input_file = r"c:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Pre-Midterm Review\In-class Example 2 - ITEC 445 - InterVLAN Communications_fixed.docx"

output_file = input_file  # Overwrite the _fixed.docx file

# Alt texts for images: index, alt_text
# For DOCX: image_N.png means index=N
alt_texts = [
    {
        'index': 0,
        'alt_text': 'InterVLAN network topology showing VLAN 10 (GREEN, 10.0.0.0/16) with static host configuration and VLAN 11 (ORANGE, 11.0.0.0/16) with DHCP configuration. Each VLAN contains a PC-PT computer connected via 2960-24TT switch S1 to router 1941 R1 with corresponding interface labels G0/0.10 and G0/0.11.'
    }
]

print("Applying alt text to In-class Example 2 InterVLAN Communications DOCX...")
apply_docx_alt_texts(input_file, output_file, alt_texts)
print(f"Success! Alt text applied to {output_file}")
