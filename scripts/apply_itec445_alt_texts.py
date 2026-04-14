#!/usr/bin/env python3
"""
Apply alt text to ITEC445 PPTX files based on extracted images.
"""

import sys
from pathlib import Path

# Import the function from fix_office
sys.path.insert(0, str(Path(__file__).parent))
from fix_office import apply_pptx_alt_texts

# Base directory
BASE_DIR = r"c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content"

# File 1: Module 2 - Switching Concepts 2 - Collision Domain
file1_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 2 - Switching Concepts/Module 2 - Switching Concepts 2 - Collision Domain_fixed.pptx"
file1_alt_texts = [
    {
        "slide": 1,  # slide2 in filename = slide 1 (0-indexed)
        "shape_idx": 3,
        "alt_text": "NETGEAR network switch with multiple Ethernet ports showing PoE status indicators."
    }
]

# File 2: Module 2 - Switching Concepts 3 - Broadcast Domains
file2_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 2 - Switching Concepts/Module 2 - Switching Concepts 3 - Broacast Domains_fixed.pptx"
file2_alt_texts = [
    {
        "slide": 1,  # slide2
        "shape_idx": 3,
        "alt_text": "Network diagram showing single switch with connected devices in broadcast domain (top) and multi-switch network with separate broadcast domains for S1 and S2 (bottom)."
    }
]

# File 3: Module 2 - Switching Concepts Complete
file3_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 2 - Switching Concepts/Module 2 - Switching Concepts Complete_fixed.pptx"
file3_alt_texts = [
    {"slide": 2, "shape_idx": 3, "alt_text": "OSI model with end devices connected through switch showing data link and physical layers."},
    {"slide": 3, "shape_idx": 3, "alt_text": "Two network segments showing collision domains between switch and connected devices."},
    {"slide": 5, "shape_idx": 3, "alt_text": "Ethernet frame structure diagram showing frame header, network header, transport header, data, and FCS fields with byte counts."},
    {"slide": 5, "shape_idx": 4, "alt_text": "OSI model layering showing end devices, switch, and physical connections between application, transport, network, link and physical layers."},
    {"slide": 6, "shape_idx": 3, "alt_text": "Simplified Ethernet frame showing preamble, destination MAC, source MAC, type, data, and FCS checksum fields with byte allocations."},
    {"slide": 7, "shape_idx": 3, "alt_text": "Two network segments showing collision domains between switch and connected devices."},
    {"slide": 8, "shape_idx": 3, "alt_text": "IPv4 header format diagram showing 32-bit structure with fields for version, service type, length, identification, flags, fragment offset, TTL, protocol, checksum, source and destination addresses."},
    {"slide": 9, "shape_idx": 3, "alt_text": "IPv4 header format diagram showing 32-bit structure with fields for version, service type, length, identification, flags, fragment offset, TTL, protocol, checksum, source and destination addresses."},
    {"slide": 9, "shape_idx": 5, "alt_text": "MAC switching learning process showing switch port table mapping destination addresses to ports."},
    {"slide": 10, "shape_idx": 3, "alt_text": "Switch port lookup showing port 1 with destination address EA and MAC address table mapping EA to port 1, AA to port 2, BA to port 3, and AC to port 6."},
    {"slide": 10, "shape_idx": 11, "alt_text": "Ethernet frame structure diagram showing frame header, network header, transport header, data, and FCS fields with byte counts."},
    {"slide": 11, "shape_idx": 3, "alt_text": "Frame forwarding process showing PC1 sending frame through port 1 to S1 switch, with PC2 receiving on port 2 and PC3 on port 3."},
    {"slide": 12, "shape_idx": 3, "alt_text": "MAC table learning showing switch S1 with port 1 MAC PC1 and ports 2 and 3 empty, demonstrating frame forwarding between connected devices."},
    {"slide": 13, "shape_idx": 3, "alt_text": "MAC table update showing S1 learning frame from PC3 with port 3 MAC now populated after frame arrival."},
    {"slide": 14, "shape_idx": 3, "alt_text": "Frame forwarding with flooding showing S1 forwarding frame from PC1 to both ports 2 and 3 with updated MAC table entries."},
    {"slide": 15, "shape_idx": 3, "alt_text": "MAC table with multiple entries showing S1 switch with destination addresses PC1, PC2 and PC3 mapped to their respective ports."},
    {"slide": 16, "shape_idx": 3, "alt_text": "MAC table entry showing S1 learning frame from PC3 with port 3 now containing MAC address from PC3."},
    {"slide": 19, "shape_idx": 3, "alt_text": "Detailed Ethernet frame structure with colored headers showing frame header, network header, transport header, data fields and FCS checksum with byte measurements and store-and-forward explanation."},
    {"slide": 20, "shape_idx": 3, "alt_text": "Ethernet frame structure diagram highlighting that frames begin forwarding once destination MAC is received with visual pointer to relevant frame sections."},
    {"slide": 21, "shape_idx": 3, "alt_text": "NETGEAR network switch with multiple Ethernet ports showing PoE status indicators."},
    {"slide": 22, "shape_idx": 3, "alt_text": "NETGEAR network switch with multiple Ethernet ports showing PoE status indicators."},
    {"slide": 24, "shape_idx": 3, "alt_text": "Network diagram showing single switch with connected devices in broadcast domain (top) and multi-switch network with separate broadcast domains for S1 and S2 (bottom)."},
]

# File 4: Module 4 Lecture 1
file4_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 4 - InterVLAN Routing/Lecture 1 - Intro to InterVLAN and Legacy InterVLAN_fixed.pptx"
file4_alt_texts = [
    {"slide": 2, "shape_idx": 3, "alt_text": "InterVLAN routing network showing router R1 connecting VLAN 10 and VLAN 30 with interface IPs, switch S2 and client PCs with their IP addresses."},
    {"slide": 3, "shape_idx": 3, "alt_text": "InterVLAN routing network showing router R1 connecting VLAN 10 and VLAN 30 with interface IPs, switch S2 and client PCs with their IP addresses."},
    {"slide": 4, "shape_idx": 3, "alt_text": "Legacy InterVLAN routing showing direct IP subnet connections on R1 interfaces with VLAN 10 and VLAN 30 connected to switch S1 and client PCs."},
    {"slide": 5, "shape_idx": 3, "alt_text": "Legacy InterVLAN routing showing direct IP subnet connections on R1 interfaces with VLAN 10 and VLAN 30 connected to switch S1 and client PCs."},
    {"slide": 5, "shape_idx": 4, "alt_text": "CLI configuration showing S1 vlan configuration commands with interface setup and switchport access vlan commands."},
]

# File 5: Module 4 Lecture 2
file5_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 4 - InterVLAN Routing/Lecture 2 - InterVLAN routing - routing on a stick_fixed.pptx"
file5_alt_texts = [
    {"slide": 2, "shape_idx": 3, "alt_text": "Router-on-a-stick topology showing router R1 with trunk interface, switch S1 with VLAN 10 and VLAN 30, and subinterface configuration details."},
    {"slide": 3, "shape_idx": 3, "alt_text": "Router-on-a-stick topology showing router R1 with trunk interface, switch S1 with VLAN 10 and VLAN 30, and subinterface configuration details."},
    {"slide": 3, "shape_idx": 4, "alt_text": "CLI configuration for router subinterface showing vlan 10, interface setup, switchport mode trunk and vlan configuration."},
    {"slide": 3, "shape_idx": 5, "alt_text": "CLI configuration for router subinterface showing interface go/0.30, encapsulation dotq 30, and IP address configuration commands."},
]

# File 6: Module 4 Lecture 3
file6_path = Path(BASE_DIR) / "ITEC445-001-FALL-2025/Module 4 - InterVLAN Routing/Lecture 3 - L3 switches and Inter-VLAN_fixed.pptx"
file6_alt_texts = [
    {"slide": 4, "shape_idx": 3, "alt_text": "L3 switch topology with SVI interfaces showing two L3 switches connected with VLAN 10 and VLAN 20, each connected to access switches with client PCs."},
    {"slide": 5, "shape_idx": 3, "alt_text": "Mesh network topology showing four L3 switches interconnected with routed interfaces and access switches below with client PCs in VLAN 10 and VLAN 20."},
    {"slide": 6, "shape_idx": 3, "alt_text": "Multi-layer network architecture with Layer 3 core switches in mesh topology connected to Layer 2 access switches with trunk links and VLANs 2, 3, and 4."},
]

def apply_alt_texts(file_path, alt_texts):
    """Apply alt texts to a PPTX file."""
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return False

    output_path = file_path
    try:
        apply_pptx_alt_texts(str(file_path), str(output_path), alt_texts)
        print(f"SUCCESS: Applied {len(alt_texts)} alt texts to {file_path.name}")
        return True
    except Exception as e:
        print(f"ERROR applying alt texts to {file_path.name}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Applying alt texts to ITEC445 PPTX files")
    print("=" * 80)

    files_to_process = [
        (file1_path, file1_alt_texts, "Module 2 - Switching Concepts 2 - Collision Domain"),
        (file2_path, file2_alt_texts, "Module 2 - Switching Concepts 3 - Broadcast Domains"),
        (file3_path, file3_alt_texts, "Module 2 - Switching Concepts Complete"),
        (file4_path, file4_alt_texts, "Module 4 Lecture 1 - Intro to InterVLAN"),
        (file5_path, file5_alt_texts, "Module 4 Lecture 2 - Routing on a stick"),
        (file6_path, file6_alt_texts, "Module 4 Lecture 3 - L3 switches"),
    ]

    results = []
    for file_path, alt_texts, description in files_to_process:
        print(f"\nProcessing: {description}")
        print(f"  File: {file_path.name}")
        print(f"  Alt texts: {len(alt_texts)}")
        success = apply_alt_texts(file_path, alt_texts)
        results.append((description, success))

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    for description, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  {status}: {description}")

    total = len(results)
    successful = sum(1 for _, success in results if success)
    print(f"\nTotal: {successful}/{total} files processed successfully")
