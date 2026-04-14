#!/usr/bin/env python3
"""Apply alt text to PPTX images across multiple files.

This script processes 5 PPTX files and applies concise alt text to all images,
based on manual inspection of extracted images.
"""

import os
from fix_office import apply_pptx_alt_texts

# Define base paths
BASE_PATH = "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025"

# File 1: Module 5 - Spanning Tree Protocol / Lecture 2
FILE_1 = {
    'path': f"{BASE_PATH}/Module 5 - Spanning Tree Protocol/Lecture 2 - Building the Spanning Tree_fixed.pptx",
    'alt_texts': [
        {'slide': 3, 'shape_idx': 3, 'alt_text': 'Network topology showing root bridge selection with bridge priorities and MAC addresses for multiple switches and their connections.'},
        {'slide': 4, 'shape_idx': 3, 'alt_text': 'Network diagram illustrating port costs with root bridge at center connected to leaf switches via different trunk paths.'},
        {'slide': 5, 'shape_idx': 3, 'alt_text': 'Table comparing link speeds to STP and RSTP costs, showing how faster links have lower cost values.'},
        {'slide': 6, 'shape_idx': 3, 'alt_text': 'Spanning tree topology with root bridge, designated ports, and path costs labeled showing preferred and alternate paths.'},
        {'slide': 7, 'shape_idx': 3, 'alt_text': 'Network diagram indicating blocked alternate port with an X mark and showing active forwarding paths.'},
        {'slide': 10, 'shape_idx': 3, 'alt_text': 'Four-switch network topology with bridge IDs, ports marked as root, designated, or alternate, and trunk connections labeled.'},
        {'slide': 11, 'shape_idx': 3, 'alt_text': 'Simplified spanning tree showing two root bridges with designated and alternate ports connecting switches across network segments.'},
        {'slide': 12, 'shape_idx': 3, 'alt_text': 'Port cost diagram for root bridge with priority and port cost values assigned to designated and alternate ports.'},
        {'slide': 13, 'shape_idx': 3, 'alt_text': 'Flowchart showing STP port state transitions: Blocking, Listening, Learning, and Forwarding with descriptions.'},
        {'slide': 13, 'shape_idx': 4, 'alt_text': 'Flowchart showing STP port state transitions: Blocking, Listening, Learning, and Forwarding with descriptions.'},
    ]
}

# File 2: Module 7 - DHCPv4 / Introduction to DHCP (22 images)
FILE_2 = {
    'path': f"{BASE_PATH}/Module 7 - DHCPv4/Introduction to DHCP_fixed.pptx",
    'alt_texts': [
        {'slide': 3, 'shape_idx': 4, 'alt_text': 'Network diagram showing DHCPv4 server in center with two subnets: 192.168.10.0/24 and 192.168.11.0/24 containing computers and switches.'},
        {'slide': 4, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 5, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 6, 'shape_idx': 5, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 9, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 10, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 10, 'shape_idx': 5, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 11, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 12, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 12, 'shape_idx': 5, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 13, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 13, 'shape_idx': 6, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 13, 'shape_idx': 8, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 14, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 14, 'shape_idx': 6, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 15, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 15, 'shape_idx': 6, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 16, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 17, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 18, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 18, 'shape_idx': 5, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
        {'slide': 19, 'shape_idx': 4, 'alt_text': 'Network topology with DHCPv4 server connected via router to switches serving two subnets with computers and a DNS server.'},
    ]
}

# File 3: Module 8 - SLAAC and DHCPv6 / Lecture 1 IPv6 Global Unicast Address Assignment (18 images)
FILE_3 = {
    'path': f"{BASE_PATH}/Module 8 - SLAAC and DHCPv6/Lecture 1 IPv6 Global Unicast Address Assignment_fixed.pptx",
    'alt_texts': [
        {'slide': 3, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 3, 'shape_idx': 5, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 4, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 4, 'shape_idx': 5, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 6, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 7, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 9, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 10, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 11, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 11, 'shape_idx': 5, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 12, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 12, 'shape_idx': 6, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 13, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 13, 'shape_idx': 6, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 14, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 15, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 15, 'shape_idx': 6, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
        {'slide': 17, 'shape_idx': 4, 'alt_text': 'IPv6 network diagram showing router with address 2001:db8:acad:1::/64 connected to computer with fe80::1 IPv6 address.'},
    ]
}

# File 4: Module 8 - SLAAC and DHCPv6 / Lecture 2 DHCPv6 (5 images)
FILE_4 = {
    'path': f"{BASE_PATH}/Module 8 - SLAAC and DHCPv6/Lecture 2 DHCPv6_fixed.pptx",
    'alt_texts': [
        {'slide': 3, 'shape_idx': 4, 'alt_text': 'Decision tree diagram showing IPv6 address assignment methods: Dynamic GUA Assignment branching into SLAAC only, SLAAC with DHCPv6 server, and DHCPv6 server options.'},
        {'slide': 5, 'shape_idx': 4, 'alt_text': 'Network topology showing IPv6 global unicast addresses with DHCPv6 server in a separate network communicating with client across router.'},
        {'slide': 8, 'shape_idx': 4, 'alt_text': 'IPv6 address assignment process diagram with boxes showing stateless and stateful DHCP server options with descriptions.'},
        {'slide': 9, 'shape_idx': 4, 'alt_text': 'Network topology showing IPv6 address assignment with DHCPv6 server, routers, and connected computers in network configuration.'},
        {'slide': 12, 'shape_idx': 4, 'alt_text': 'Network topology showing IPv6 address assignment with DHCPv6 server, routers, and connected computers in network configuration.'},
    ]
}

# File 5: Module 9 - First Hop Redundancy Protocol (FHRP) / Lecture 3 - HSRP Demo
FILE_5 = {
    'path': f"{BASE_PATH}/Module 9 - First Hop Redundancy Protocol (FHRP)/Lecture 3 - HSRP Demo_fixed.pptx",
    'alt_texts': [
        {'slide': 2, 'shape_idx': 4, 'alt_text': 'HSRP network topology showing two routers with priorities and IP addresses in a redundant configuration with virtual gateway and multiple PC endpoints.'},
    ]
}

def process_file(file_dict, file_num):
    """Process a single PPTX file."""
    path = file_dict['path']
    alt_texts = file_dict['alt_texts']

    print(f"\n{'='*60}")
    print(f"Processing File {file_num}: {os.path.basename(path)}")
    print(f"{'='*60}")
    print(f"Path: {path}")
    print(f"Images to process: {len(alt_texts)}")

    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        return False

    try:
        result = apply_pptx_alt_texts(path, path, alt_texts)
        print(f"Result: {result}")
        if result['applied'] > 0:
            print(f"Successfully applied {result['applied']} alt texts")
            return True
        else:
            print(f"No alt texts were applied")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Process all PPTX files."""
    files = [FILE_1, FILE_2, FILE_3, FILE_4, FILE_5]
    results = []

    print("\n" + "="*60)
    print("PPTX Alt Text Application Script")
    print("="*60)

    for i, file_dict in enumerate(files, 1):
        success = process_file(file_dict, i)
        results.append((os.path.basename(file_dict['path']), success))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    successful = sum(1 for _, s in results if s)
    total = len(results)
    print(f"Files processed successfully: {successful}/{total}")
    for filename, success in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {filename}")

if __name__ == '__main__':
    main()
