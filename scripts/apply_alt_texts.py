#!/usr/bin/env python3
"""
Apply alt text to PPTX files based on images in _imgs directories.
This script reads PNG images from _imgs directories and generates appropriate alt text,
then applies it to the corresponding PPTX files.
"""

import os
import sys
from pathlib import Path
from fix_office import apply_pptx_alt_texts

# Define file configurations with their image directories
FILES_CONFIG = [
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\Lecture 1 LAN Security Concepts_fixed.pptx",
        "imgs_dir": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\_imgs_Lecture 1 LAN Security Concepts",
        "alt_texts": [
            {"slide": 10, "shape_idx": 4, "alt_text": "Diagram showing remote client authentication process with AAA router prompting for credentials and router authenticating with corporate network."},
            {"slide": 11, "shape_idx": 4, "alt_text": "Network diagram illustrating remote client connecting through AAA router to both AAA server and corporate network."},
            {"slide": 12, "shape_idx": 4, "alt_text": "Authentication sequence showing numbered steps for router-to-AAA server communication and PASS/FAIL response for user authorization."},
            {"slide": 13, "shape_idx": 4, "alt_text": "Accounting process diagram demonstrating how AAA server generates start and stop messages to track user session duration."},
            {"slide": 14, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 15, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 16, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 17, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 2, "shape_idx": 4, "alt_text": "Network security concept diagram showing opponent types and access channels with gatekeeper function controlling network entry."},
            {"slide": 2, "shape_idx": 7, "alt_text": "Wiretapping scenario illustration with Darth as attacker intercepting communications between Bob and Alice over internet or other communication facility."},
            {"slide": 3, "shape_idx": 4, "alt_text": "Network security concept diagram showing opponent types and access channels with gatekeeper function controlling network entry."},
            {"slide": 3, "shape_idx": 7, "alt_text": "Wiretapping scenario illustration with Darth as attacker intercepting communications between Bob and Alice over internet or other communication facility."},
            {"slide": 4, "shape_idx": 4, "alt_text": "Network diagram showing internal trusted network connecting through firewall to untrusted internet with packet filtering and direction indicators."},
            {"slide": 4, "shape_idx": 7, "alt_text": "Email security diagram with ESA analyzing phishing emails, threat actor sends email, and email is forwarded with ESA analyzing for malware detection."},
            {"slide": 5, "shape_idx": 4, "alt_text": "Cisco IOS configuration commands for VTY line security including password and login commands for remote access control."},
            {"slide": 6, "shape_idx": 4, "alt_text": "Cisco router configuration commands for domain name, RSA key generation, username creation, SSH version 2 enabling, and transport protocols."},
            {"slide": 6, "shape_idx": 5, "alt_text": "Network device management diagram showing IP addresses, SSH access, and secure connection configuration between router and admin console."},
            {"slide": 7, "shape_idx": 4, "alt_text": "Network device management diagram showing IP addresses, SSH access, and secure connection configuration between router and admin console."},
        ]
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\Lecture 2 LAN Security Threats_fixed.pptx",
        "imgs_dir": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\_imgs_Lecture 2 LAN Security Threats",
        "alt_texts": []  # Will be populated after examining images
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\Lecture 3 Attack Examples_fixed.pptx",
        "imgs_dir": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\_imgs_Lecture 3 Attack Examples",
        "alt_texts": []  # Will be populated after examining images
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 11 - Mitigating Cyber-attacks with Switch Security\Lecture 1 Port Security_fixed.pptx",
        "imgs_dir": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 11 - Mitigating Cyber-attacks with Switch Security\_imgs_Lecture 1 Port Security",
        "alt_texts": []  # Will be populated after examining images
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 14 - Troubleshooting Static Routes\Lecture 1 Troubleshooting Tools_fixed.pptx",
        "imgs_dir": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 14 - Troubleshooting Static Routes\_imgs_Lecture 1 Troubleshooting Tools",
        "alt_texts": []  # Will be populated after examining images
    }
]

def process_pptx_file(config):
    """Process a single PPTX file by applying alt texts."""
    pptx_path = config["pptx_path"]
    output_path = pptx_path.replace("_fixed.pptx", "_fixed_alt.pptx")
    alt_texts = config["alt_texts"]

    if not alt_texts:
        print(f"Skipping {Path(pptx_path).name}: No alt texts configured")
        return

    try:
        apply_pptx_alt_texts(pptx_path, output_path, alt_texts)
        print(f"Successfully processed: {Path(pptx_path).name}")
        print(f"  Output: {Path(output_path).name}")
        print(f"  Applied {len(alt_texts)} alt texts")
    except Exception as e:
        print(f"Error processing {Path(pptx_path).name}: {e}")

def main():
    """Main entry point."""
    print("Processing PPTX files with alt text...")

    # For now, only process the first file which has alt texts configured
    config = FILES_CONFIG[0]
    process_pptx_file(config)

    print("\nAlt text application complete!")

if __name__ == "__main__":
    main()
