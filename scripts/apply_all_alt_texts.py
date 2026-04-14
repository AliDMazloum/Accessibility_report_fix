#!/usr/bin/env python3
"""
Apply alt text to all 5 PPTX files based on images in _imgs directories.
"""

import sys
from pathlib import Path
from fix_office import apply_pptx_alt_texts

# Configuration for all 5 PPTX files with their alt texts
FILES_CONFIG = [
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\Lecture 1 LAN Security Concepts_fixed.pptx",
        "name": "Lecture 1 LAN Security Concepts",
        "alt_texts": [
            {"slide": 10, "shape_idx": 4, "alt_text": "Diagram showing remote client authentication process with AAA router prompting for credentials and router authenticating with corporate network."},
            {"slide": 11, "shape_idx": 4, "alt_text": "Network diagram illustrating remote client connecting through AAA router to both AAA server and corporate network."},
            {"slide": 12, "shape_idx": 4, "alt_text": "Authentication sequence showing numbered steps for router-to-AAA server communication and PASS/FAIL response for user authorization."},
            {"slide": 13, "shape_idx": 4, "alt_text": "Accounting process diagram demonstrating how AAA server generates start and stop messages to track user session duration."},
            {"slide": 14, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 15, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 16, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 17, "shape_idx": 4, "alt_text": "Three-tier network security architecture with Supplicant requiring access, Authenticator controlling physical network access, and Authentication server performing client authentication."},
            {"slide": 2, "shape_idx": 4, "alt_text": "Network security concept diagram showing opponent types including human hackers and software threats, access channels, and gatekeeper function controlling network entry."},
            {"slide": 2, "shape_idx": 7, "alt_text": "Wiretapping scenario illustration with Darth as attacker intercepting communications between Bob and Alice over internet or other communication facility."},
            {"slide": 3, "shape_idx": 4, "alt_text": "Network security concept diagram showing opponent types including human hackers and software threats, access channels, and gatekeeper function controlling network entry."},
            {"slide": 3, "shape_idx": 7, "alt_text": "Wiretapping scenario illustration with Darth as attacker intercepting communications between Bob and Alice over internet or other communication facility."},
            {"slide": 4, "shape_idx": 4, "alt_text": "Network diagram showing internal trusted network connecting through firewall to untrusted internet with packet filtering and directional data flow indicators."},
            {"slide": 4, "shape_idx": 7, "alt_text": "Email security diagram with ESA analyzing phishing emails, threat actor sends attack email, and ESA analyzes for malware detection and discards threats."},
            {"slide": 5, "shape_idx": 4, "alt_text": "Cisco IOS configuration commands for VTY line security including password setting and login enabling for remote access control."},
            {"slide": 6, "shape_idx": 4, "alt_text": "Cisco router configuration commands for domain name setup, RSA key generation, username creation, SSH version 2 enabling, and transport protocol configuration."},
            {"slide": 6, "shape_idx": 5, "alt_text": "Network diagram showing router interface configurations with IP addresses for secure SSH access and admin console connections."},
            {"slide": 7, "shape_idx": 4, "alt_text": "Network diagram showing router interface configurations with IP addresses for secure SSH access and admin console connections."},
        ]
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\Lecture 2 LAN Security Threats_fixed.pptx",
        "name": "Lecture 2 LAN Security Threats",
        "alt_texts": [
            {"slide": 9, "shape_idx": 4, "alt_text": "VLAN hopping attack diagram showing threat actor using 802.1Q trunk port to gain unauthorized access to server VLAN."},
            {"slide": 2, "shape_idx": 5, "alt_text": "OSI model layers diagram showing where different attack types occur, with layer 2 data link highlighted as initial compromise point."},
            {"slide": 7, "shape_idx": 4, "alt_text": "Cisco switch command output showing MAC address table with VLAN and port information."},
            {"slide": 7, "shape_idx": 5, "alt_text": "Network topology diagram with switch connecting multiple PCs and servers showing MAC address mappings and port configurations."},
            {"slide": 7, "shape_idx": 8, "alt_text": "Switch command output displaying MAC address table with dynamic entries showing VLAN and port assignments."},
        ]
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 10 - LAN Security Concepts\Lecture 3 Attack Examples_fixed.pptx",
        "name": "Lecture 3 Attack Examples",
        "alt_texts": [
            {"slide": 2, "shape_idx": 4, "alt_text": "Network topology showing switches connected with 802.1Q trunk, VLAN 10 and VLAN 20 connected to servers, with attacker creating unauthorized trunk."},
            {"slide": 3, "shape_idx": 3, "alt_text": "VLAN hopping attack step 1 showing attacker sending crafted Ethernet frame with VLAN tags toward the switch."},
            {"slide": 4, "shape_idx": 3, "alt_text": "VLAN hopping attack step 2 showing attacker frame being processed and reaching target VLAN on switch."},
            {"slide": 5, "shape_idx": 4, "alt_text": "VLAN hopping attack step 3 showing packet reaching target host in VLAN 20 after being untagged by switch."},
            {"slide": 8, "shape_idx": 4, "alt_text": "DHCP Discovery process diagram showing DHCP client sending DHCPDISCOVER broadcast, legitimate server responding with DHCOFFER, and rogue DHCP server also offering IP addresses."},
            {"slide": 9, "shape_idx": 4, "alt_text": "Illustration of hacker on laptop with malicious intent represented by skull and crossbones icon."},
            {"slide": 10, "shape_idx": 4, "alt_text": "Rogue DHCP server attack showing switch topology with legitimate DHCP server, cross-connected clients, and attacker positioning rogue DHCP server."},
            {"slide": 11, "shape_idx": 4, "alt_text": "Rogue DHCP server attack showing switch topology with legitimate DHCP server, cross-connected clients, and attacker positioning rogue DHCP server."},
            {"slide": 12, "shape_idx": 4, "alt_text": "DHCP Discover flood attack showing multiple DHCP Discover messages from DHCP client to legitimate server and rogue server."},
            {"slide": 12, "shape_idx": 5, "alt_text": "DHCP Offer stage of attack showing server and rogue server sending multiple offer messages with configuration details."},
            {"slide": 12, "shape_idx": 6, "alt_text": "DHCP Request stage of attack showing client and rogue server exchanging request messages for IP address assignment."},
            {"slide": 12, "shape_idx": 7, "alt_text": "DHCP Acknowledgment stage of attack showing server and rogue server sending ACK messages to complete IP address assignment."},
            {"slide": 12, "shape_idx": 8, "alt_text": "DHCP attack completion showing DHCP Ack messages being sent to finalize configuration assignment from rogue server."},
            {"slide": 13, "shape_idx": 4, "alt_text": "ARP spoofing attack showing attacker with PC sending fake ARP cache entries for IP to MAC address mapping."},
            {"slide": 15, "shape_idx": 4, "alt_text": "ARP spoofing detailed diagram showing multiple computers with ARP caches containing spoofed MAC address mappings."},
            {"slide": 16, "shape_idx": 5, "alt_text": "ARP spoofing attack progression showing PC2 injecting false ARP responses into network causing MAC address table corruption."},
            {"slide": 17, "shape_idx": 4, "alt_text": "MAC address spoofing attack showing threat actor claiming fake MAC address to deceive network and redirect traffic."},
            {"slide": 18, "shape_idx": 4, "alt_text": "Spanning Tree Protocol attack showing attacker with bridge being elected as root bridge through BPDUs with priority 0."},
            {"slide": 18, "shape_idx": 5, "alt_text": "Network topology showing switches with forward and block indicators under different spanning tree configurations with attacker as root."},
            {"slide": 19, "shape_idx": 4, "alt_text": "Spreadsheet document displayed in application window containing network configuration and security-related data."},
            {"slide": 20, "shape_idx": 4, "alt_text": "Spreadsheet document displayed in application window containing network configuration and security-related data."},
        ]
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 11 - Mitigating Cyber-attacks with Switch Security\Lecture 1 Port Security_fixed.pptx",
        "name": "Lecture 1 Port Security",
        "alt_texts": [
            {"slide": 2, "shape_idx": 4, "alt_text": "Cisco IOS configuration commands for switch interface range shutdown and port security configuration."},
            {"slide": 3, "shape_idx": 4, "alt_text": "Port security diagram showing allowed MAC addresses and attackers blocked from connecting to protected switch ports."},
            {"slide": 4, "shape_idx": 4, "alt_text": "Cisco switch command output showing port security configuration error for dynamic port and switchport mode setting."},
            {"slide": 5, "shape_idx": 4, "alt_text": "Cisco switch port security status output showing security enabled, violation mode set to shutdown, and MAC address aging settings."},
            {"slide": 6, "shape_idx": 4, "alt_text": "Port security diagram showing allowed MAC addresses and attackers blocked from connecting to protected switch ports."},
            {"slide": 6, "shape_idx": 5, "alt_text": "Port security diagram showing allowed MAC addresses and attackers blocked from connecting to protected switch ports."},
            {"slide": 7, "shape_idx": 4, "alt_text": "Cisco IOS configuration commands for switchport port-security maximum address limit setting on switch interface."},
            {"slide": 8, "shape_idx": 4, "alt_text": "Cisco switch command output showing port security aging configuration with static and dynamic address aging parameters."},
            {"slide": 9, "shape_idx": 4, "alt_text": "Table describing three port security violation modes: Protect, Restrict, and Shutdown with their effects on traffic and error reporting."},
            {"slide": 10, "shape_idx": 5, "alt_text": "Table showing security violation modes with columns for Violation Mode, Forwards Traffic, Sends Syslog Message, Displays Error Message, Increases Violation Counter, and Shuts Down Port."},
            {"slide": 12, "shape_idx": 3, "alt_text": "Table describing three port security violation modes: Protect, Restrict, and Shutdown with their effects on traffic and error reporting."},
            {"slide": 13, "shape_idx": 4, "alt_text": "Table showing security violation modes with columns for Violation Mode, Forwards Traffic, Sends Syslog Message, Displays Error Message, Increases Violation Counter, and Shuts Down Port."},
            {"slide": 13, "shape_idx": 5, "alt_text": "Table showing security violation modes with columns for Violation Mode, Forwards Traffic, Sends Syslog Message, Displays Error Message, Increases Violation Counter, and Shuts Down Port."},
            {"slide": 14, "shape_idx": 4, "alt_text": "Table showing security violation modes with columns for Violation Mode, Forwards Traffic, Sends Syslog Message, Displays Error Message, Increases Violation Counter, and Shuts Down Port."},
            {"slide": 14, "shape_idx": 5, "alt_text": "Table showing security violation modes with columns for Violation Mode, Forwards Traffic, Sends Syslog Message, Displays Error Message, Increases Violation Counter, and Shuts Down Port."},
        ]
    },
    {
        "pptx_path": r"C:\Users\alima\OneDrive - University of South Carolina\Research\Working Directory\Blackboard_Accessibility_report\course_content\ITEC445-001-FALL-2025\Module 14 - Troubleshooting Static Routes\Lecture 1 Troubleshooting Tools_fixed.pptx",
        "name": "Lecture 1 Troubleshooting Tools",
        "alt_texts": [
            {"slide": 2, "shape_idx": 4, "alt_text": "Ping command output showing ping to IP address 192.168.20.2 with response statistics showing packets sent, received, and packet loss percentage."},
            {"slide": 2, "shape_idx": 5, "alt_text": "Network topology diagram showing LAN-10 and LAN-20 connected through two switches with routers and interconnecting links and labeled with IP addresses."},
            {"slide": 3, "shape_idx": 4, "alt_text": "Tracert command output showing route trace to destination 192.168.20.2 with numbered hops, response times, and IP addresses."},
            {"slide": 3, "shape_idx": 5, "alt_text": "Network topology diagram showing LAN-10 and LAN-20 connected through two switches with routers and interconnecting links and labeled with IP addresses."},
            {"slide": 4, "shape_idx": 4, "alt_text": "Cisco router show IP route command output displaying routing table with all configured and connected routes with protocol codes and destinations."},
            {"slide": 5, "shape_idx": 4, "alt_text": "Cisco router show IP interface brief command output displaying interface information including IP addresses, status, and protocol details."},
            {"slide": 5, "shape_idx": 5, "alt_text": "Network topology diagram showing LAN-10 and LAN-20 connected through two switches with routers and interconnecting links and labeled with IP addresses."},
            {"slide": 6, "shape_idx": 4, "alt_text": "Cisco router show CDP neighbors command output displaying neighboring devices with capabilities, device ID, holdtime, and port information."},
            {"slide": 6, "shape_idx": 5, "alt_text": "Network topology diagram showing LAN-10 and LAN-20 connected through two switches with routers and interconnecting links and labeled with IP addresses."},
            {"slide": 7, "shape_idx": 4, "alt_text": "Cisco router show IP route command output displaying routing table with all configured and connected routes with protocol codes and destinations."},
        ]
    }
]

def process_pptx_file(config):
    """Process a single PPTX file by applying alt texts."""
    pptx_path = config["pptx_path"]
    output_path = pptx_path.replace("_fixed.pptx", "_fixed_alt.pptx")
    alt_texts = config["alt_texts"]
    name = config["name"]

    if not alt_texts:
        print(f"SKIPPED: {name}")
        print(f"  Reason: No alt texts configured")
        return False

    try:
        apply_pptx_alt_texts(pptx_path, output_path, alt_texts)
        print(f"SUCCESS: {name}")
        print(f"  Input:  {Path(pptx_path).name}")
        print(f"  Output: {Path(output_path).name}")
        print(f"  Applied {len(alt_texts)} alt texts")
        return True
    except Exception as e:
        print(f"ERROR: {name}")
        print(f"  Exception: {e}")
        return False

def main():
    """Main entry point."""
    print("=" * 70)
    print("PPTX ALT TEXT APPLICATION")
    print("=" * 70)
    print()

    successful = 0
    failed = 0
    skipped = 0

    for i, config in enumerate(FILES_CONFIG, 1):
        print(f"[{i}/{len(FILES_CONFIG)}] Processing {config['name']}...")
        if process_pptx_file(config):
            successful += 1
        else:
            failed += 1
        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print(f"Skipped:    {skipped}")
    print(f"Total:      {len(FILES_CONFIG)}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
