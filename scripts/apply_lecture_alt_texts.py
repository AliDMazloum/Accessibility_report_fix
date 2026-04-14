#!/usr/bin/env python3
"""
Apply alt text to PPTX files for Module 12 - Routing Concepts lectures.
This script generates concise alt text for images and embeds them in the PPTX files.
"""

import sys
sys.path.insert(0, 'c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/scripts')

from fix_office import apply_pptx_alt_texts

# Base path
BASE_PATH = "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 12 - Routing Concepts"

# Lecture 1 - Introduction to Routing and LPM (5 images)
lecture1_alt_texts = [
    {"slide": 3, "shape_idx": 4, "alt_text": "Network topology diagram showing multiple routers and network segments connected with labeled interfaces and routing paths."},
    {"slide": 4, "shape_idx": 4, "alt_text": "Network topology with packet capture output showing routing information and traffic flow between network devices."},
    {"slide": 6, "shape_idx": 4, "alt_text": "Table showing IPv4 address 172.16.0.10 in decimal and binary, with routing prefix entries for different subnet masks."},
    {"slide": 7, "shape_idx": 4, "alt_text": "IPv6 routing table comparison showing different prefix lengths and their matching capabilities."},
    {"slide": 8, "shape_idx": 4, "alt_text": "Complete network topology diagram illustrating directly connected networks and remote networks in the routing domain."},
]

print("Processing Lecture 1 - Introduction to Routing and LPM...")
input_path = f"{BASE_PATH}/Lecture 1 - Introduction to Routing and LPM_fixed.pptx"
output_path = f"{BASE_PATH}/Lecture 1 - Introduction to Routing and LPM_fixed.pptx"
apply_pptx_alt_texts(input_path, output_path, lecture1_alt_texts)
print("✓ Lecture 1 completed")

# Lecture 2 - Packet Forwarding (7 images)
lecture2_alt_texts = [
    {"slide": 2, "shape_idx": 4, "alt_text": "Packet forwarding flow diagram showing how packets are processed through input, output, and routing decisions."},
    {"slide": 3, "shape_idx": 4, "alt_text": "Network packet processing diagram with CLI commands showing packet forwarding implementation."},
    {"slide": 4, "shape_idx": 4, "alt_text": "Diagram of packet flow through router layers with interface queues and routing table lookup process."},
    {"slide": 5, "shape_idx": 4, "alt_text": "Illustration of packet forwarding with ARP resolution showing layer 2 and layer 3 header modifications."},
    {"slide": 7, "shape_idx": 4, "alt_text": "Router architecture diagram showing control plane with CPU, data plane with interfaces, and packet flow paths."},
    {"slide": 8, "shape_idx": 4, "alt_text": "Router architecture with control plane, data plane, and fast forward cache for optimized packet processing."},
    {"slide": 9, "shape_idx": 4, "alt_text": "Router architecture illustrating FIB (Forwarding Information Base) and adjacency table for packet forwarding."},
]

print("Processing Lecture 2 - Packet Forwarding...")
input_path = f"{BASE_PATH}/Lecture 2 - Packet Forwarding_fixed.pptx"
output_path = f"{BASE_PATH}/Lecture 2 - Packet Forwarding_fixed.pptx"
apply_pptx_alt_texts(input_path, output_path, lecture2_alt_texts)
print("✓ Lecture 2 completed")

# Lecture 3 - Basic Router Configuration (5 images)
lecture3_alt_texts = [
    {"slide": 2, "shape_idx": 4, "alt_text": "Network topology diagram with four routers interconnected showing interface configurations and network segments."},
    {"slide": 3, "shape_idx": 4, "alt_text": "Same network topology as slide 2 for reference."},
    {"slide": 3, "shape_idx": 5, "alt_text": "CLI command output showing router configuration including enable, terminal setup, and security settings."},
    {"slide": 4, "shape_idx": 4, "alt_text": "Network topology diagram repeated for configuration context."},
    {"slide": 4, "shape_idx": 5, "alt_text": "CLI configuration commands showing IPv4 and IPv6 address configuration for multiple router interfaces."},
]

print("Processing Lecture 3 - Basic Router Configuration...")
input_path = f"{BASE_PATH}/Lecture 3 - Basic Router Configuration_fixed.pptx"
output_path = f"{BASE_PATH}/Lecture 3 - Basic Router Configuration_fixed.pptx"
apply_pptx_alt_texts(input_path, output_path, lecture3_alt_texts)
print("✓ Lecture 3 completed")

# Lecture 4 - Understanding the Routing Table (17 images)
lecture4_alt_texts = [
    {"slide": 3, "shape_idx": 4, "alt_text": "Network topology showing router interconnections with labeled interfaces."},
    {"slide": 4, "shape_idx": 4, "alt_text": "Network topology diagram repeated."},
    {"slide": 4, "shape_idx": 5, "alt_text": "CLI output of 'show ip route' command displaying routing table codes and entry details."},
    {"slide": 5, "shape_idx": 3, "alt_text": "Network topology diagram for reference."},
    {"slide": 6, "shape_idx": 4, "alt_text": "Detailed routing table entry example with colored legend explaining destination, administrative distance, metric, and other routing parameters."},
    {"slide": 7, "shape_idx": 4, "alt_text": "CLI output showing IPv4 and IPv6 routing table entries with directly connected and local routes."},
    {"slide": 7, "shape_idx": 5, "alt_text": "Network diagram illustrating packet forwarding path and routing table information."},
    {"slide": 8, "shape_idx": 4, "alt_text": "CLI output of static routing commands with IPv6 routing table entries."},
    {"slide": 9, "shape_idx": 4, "alt_text": "Network topology diagram for context."},
    {"slide": 9, "shape_idx": 5, "alt_text": "CLI output showing static routes in both IPv4 and IPv6 routing tables."},
    {"slide": 10, "shape_idx": 4, "alt_text": "Network diagram with packet flow arrows showing routing decision process between routers."},
    {"slide": 11, "shape_idx": 4, "alt_text": "Network diagram showing packet forwarding between routers using routing decisions."},
    {"slide": 11, "shape_idx": 5, "alt_text": "CLI output displaying static route entries in routing tables for IPv4 and IPv6."},
    {"slide": 12, "shape_idx": 4, "alt_text": "Network topology with red and blue arrows indicating packet forwarding paths and routing decisions."},
    {"slide": 13, "shape_idx": 4, "alt_text": "Network topology diagram with directional arrows showing packet flow paths."},
    {"slide": 13, "shape_idx": 5, "alt_text": "CLI output showing route details and metric information from 'show ip route' command."},
    {"slide": 14, "shape_idx": 4, "alt_text": "Network topology with orange arrows highlighting specific packet forwarding path between routers."},
]

print("Processing Lecture 4 - Understanding the Routing Table...")
input_path = f"{BASE_PATH}/Lecture 4 - Understanding the Routing Table_fixed.pptx"
output_path = f"{BASE_PATH}/Lecture 4 - Understanding the Routing Table_fixed.pptx"
apply_pptx_alt_texts(input_path, output_path, lecture4_alt_texts)
print("✓ Lecture 4 completed")

# Lecture 5 - Routing Table Structure and AD (5 images)
lecture5_alt_texts = [
    {"slide": 6, "shape_idx": 4, "alt_text": "CLI output showing routing table entries with connected networks and various routing protocol sources."},
    {"slide": 7, "shape_idx": 4, "alt_text": "CLI output displaying connected interface routes in the routing table."},
    {"slide": 8, "shape_idx": 4, "alt_text": "CLI output showing connected and static routes with administrative distance information."},
    {"slide": 9, "shape_idx": 4, "alt_text": "CLI output of IPv6 routing table showing connected routes and next-hop information."},
    {"slide": 11, "shape_idx": 4, "alt_text": "Table showing routing sources and their corresponding administrative distance values from 0 to 200."},
]

print("Processing Lecture 5 - Routing Table Structure and AD...")
input_path = f"{BASE_PATH}/Lecture 5 - Routing Table Structure and AD_fixed.pptx"
output_path = f"{BASE_PATH}/Lecture 5 - Routing Table Structure and AD_fixed.pptx"
apply_pptx_alt_texts(input_path, output_path, lecture5_alt_texts)
print("✓ Lecture 5 completed")

print("\n" + "="*60)
print("All lectures processed successfully!")
print("="*60)
