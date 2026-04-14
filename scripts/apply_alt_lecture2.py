#!/usr/bin/env python3
"""
Apply alt text to Lecture 2 Packet Processing slide 3 shape 4.
Image shows network topology with two switches connected through hub-PT to an Internet cloud.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fix_office import apply_pptx_alt_texts

input_file = r"c:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 14 - Troubleshooting Static Routes\Lecture 2 Packet Processing_fixed.pptx"

output_file = input_file  # Overwrite the _fixed.pptx file

# Alt texts for images: slide (0-indexed), shape_idx, alt_text
alt_texts = [
    {
        'slide': 2,  # slide3_shape4.png means slide 3, so index 2
        'shape_idx': 4,
        'alt_text': 'Network diagram showing two switches on left and right connected through hub-PT with interfaces labeled, connecting to Internet cloud below. Left network LAN-10 (192.168.10.0/24) uses 2960-24TT switch on VLAN, right network LAN-20 (192.168.20.0/24) uses 2960-24TT switch, with routing between them via hub and Internet.'
    }
]

print("Applying alt text to PPTX file...")
apply_pptx_alt_texts(input_file, output_file, alt_texts)
print(f"Success! Alt text applied to {output_file}")
