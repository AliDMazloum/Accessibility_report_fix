#!/usr/bin/env python3
"""
Apply alt text to EtherChannel PPTX presentation images.
Reads extracted images, generates concise alt text, and applies to shapes.
"""

import sys

sys.path.insert(0, 'c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/scripts')
from fix_office import apply_pptx_alt_texts

# File paths
pptx_path = "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/_downloads/Lecture 1 - Introduction to EtherChannel_fixed.pptx"

# Alt text mappings based on image analysis
# Format: {slide: N-1, shape_idx: M, alt_text: "..."}
alt_texts = [
    # slide4_shape3: Network topology with blocked ports
    {
        "slide": 3,
        "shape_idx": 3,
        "alt_text": "Network diagram showing two switches connected to a central switch with blocked ports indicated by red circles and orange labels."
    },
    # slide5_shape3: EtherChannel enabled topology
    {
        "slide": 4,
        "shape_idx": 3,
        "alt_text": "Network diagram showing two switches connected to a central switch with EtherChannel connections indicated by purple ellipses."
    },
    # slide6_shape3: EtherChannel enabled topology (duplicate)
    {
        "slide": 5,
        "shape_idx": 3,
        "alt_text": "Network diagram showing two switches connected to a central switch with EtherChannel connections indicated by purple ellipses."
    },
    # slide7_shape3: Cisco switch port diagram with logical port
    {
        "slide": 6,
        "shape_idx": 3,
        "alt_text": "Cisco switch diagram with multiple ports on the front panel, showing physical connections and a logical port in the upper portion."
    },
    # slide8_shape3: Cisco switch port diagram (duplicate)
    {
        "slide": 7,
        "shape_idx": 3,
        "alt_text": "Cisco switch diagram with multiple ports on the front panel, showing physical connections and a logical port in the upper portion."
    },
    # slide9_shape3: Two switches S1 and S2 connected with EtherChannel
    {
        "slide": 8,
        "shape_idx": 3,
        "alt_text": "Two blue switches labeled S1 and S2 connected by a black line with a purple EtherChannel indicator."
    },
    # slide10_shape3: Two switches S1 and S2 connected with EtherChannel (duplicate)
    {
        "slide": 9,
        "shape_idx": 3,
        "alt_text": "Two blue switches labeled S1 and S2 connected by a black line with a purple EtherChannel indicator."
    },
    # slide11_shape4: S1 and S2 with PAgP protocol arrow
    {
        "slide": 10,
        "shape_idx": 4,
        "alt_text": "PAgP protocol diagram with orange bidirectional arrow above two switches S1 and S2 connected with EtherChannel."
    },
    # slide11_shape5: PAgP mode compatibility table
    {
        "slide": 10,
        "shape_idx": 5,
        "alt_text": "Table showing PAgP mode compatibility for S1 and S2 with Channel Establishment outcomes for On, Desirable, and Auto modes."
    },
    # slide12_shape3: Two switches S1 and S2 connected with EtherChannel (third variant)
    {
        "slide": 11,
        "shape_idx": 3,
        "alt_text": "Two blue switches labeled S1 and S2 connected by a black line with a purple EtherChannel indicator."
    },
    # slide13_shape4: S1 and S2 with LACP protocol arrow
    {
        "slide": 12,
        "shape_idx": 4,
        "alt_text": "LACP protocol diagram with orange bidirectional arrow above two switches S1 and S2 connected with EtherChannel."
    },
    # slide13_shape5: LACP mode compatibility table
    {
        "slide": 12,
        "shape_idx": 5,
        "alt_text": "Table showing LACP mode compatibility for S1 and S2 with Channel Establishment outcomes for On, Active, and Passive modes."
    },
]

# Apply alt texts
print(f"Applying alt text to: {pptx_path}")
print(f"Total images: {len(alt_texts)}")

apply_pptx_alt_texts(pptx_path, pptx_path, alt_texts)

print("Alt text application complete!")
