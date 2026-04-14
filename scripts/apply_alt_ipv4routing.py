#!/usr/bin/env python3
"""
Apply alt text to Basic IPv4 Routing image.
Image shows simple network topology with three routers and VLAN connections.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fix_office import apply_docx_alt_texts

input_file = r"c:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Pre-Final Exam Review\Basic IPv4 Routing_fixed.docx"

output_file = input_file  # Overwrite the _fixed.docx file

# Alt texts for images: index, alt_text
# For DOCX: image_N.png means index=N
alt_texts = [
    {
        'index': 0,
        'alt_text': 'Network topology showing three routers (LAN10, LAN20, LAN30) connected through a central 2960-24TT switch and router with interface labels and IP addresses 192.168.10.0/24, 192.168.20.0/24, and 192.168.30.0/24 for each network segment.'
    }
]

print("Applying alt text to Basic IPv4 Routing DOCX...")
apply_docx_alt_texts(input_file, output_file, alt_texts)
print(f"Success! Alt text applied to {output_file}")
