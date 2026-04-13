"""Apply all generated alt texts to ITEC445F PPTX files, then upload."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from fix_office import apply_pptx_alt_texts

BASE = "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025"

# Map directory paths to their PPTX source files
DIR_TO_PPTX = {
    "_imgs_IntroductionNetworks": "Module 1 - Basic device configuration/IntroductionNetworks",
    "_imgs_IOS-review": "Module 1 - Basic device configuration/IOS-review",
    "_imgs_Module 1 - basic device configuration II - SSH": "Module 1 - Basic device configuration/Module 1 - basic device configuration II - SSH",
    "_imgs_Module 2 - Switching Concepts 2 - Collision Domain": "Module 2 - Switching Concepts/Module 2 - Switching Concepts 2 - Collision Domain",
    "_imgs_Module 2 - Switching Concepts 3 - Broacast Domains": "Module 2 - Switching Concepts/Module 2 - Switching Concepts 3 - Broacast Domains",
    "_imgs_Module 2 - Switching Concepts Complete": "Module 2 - Switching Concepts/Module 2 - Switching Concepts Complete",
    "_imgs_Lecture 1 - vlans fundamentals 1": "Module 3 - Virtual Local Area Networks/Lecture 1 - vlans fundamentals 1",
    "_imgs_Lecture 2 - vlans - trunks and 802-1Q": "Module 3 - Virtual Local Area Networks/Lecture 2 - vlans - trunks and 802-1Q",
    "_imgs_Lecture 3 - VLAN configuration": "Module 3 - Virtual Local Area Networks/Lecture 3 - VLAN configuration",
    "_imgs_Lecture 5 - Native VLANs": "Module 3 - Virtual Local Area Networks/Lecture 5 - Native VLANs",
    "_imgs_vlans": "Module 3 - Virtual Local Area Networks/vlans",
    "_imgs_Lecture 1 - Intro to InterVLAN and Legacy InterVLAN": "Module 4 - InterVLAN Routing/Lecture 1 - Intro to InterVLAN and Legacy InterVLAN",
    "_imgs_Lecture 2 - InterVLAN routing - routing on a stick": "Module 4 - InterVLAN Routing/Lecture 2 - InterVLAN routing - routing on a stick",
    "_imgs_Lecture 3 - L3 switches and Inter-VLAN": "Module 4 - InterVLAN Routing/Lecture 3 - L3 switches and Inter-VLAN",
    "_imgs_advance_topics": "Top Level/advance_topics",
    "_imgs_Network Security": "Top Level/Network Security",
    "_imgs_wlan": "Top Level/wlan",
}

# All alt texts organized by img directory suffix
all_alts = {
    # Module 1 - IntroductionNetworks (9)
    "_imgs_IntroductionNetworks": [
        {"slide": 1, "shape_idx": 3, "alt_text": "Website listing showing Network Engineer job positions with descriptions and search filters."},
        {"slide": 2, "shape_idx": 3, "alt_text": "Multiple job listings for Network Engineer positions with detailed descriptions and requirements."},
        {"slide": 6, "shape_idx": 3, "alt_text": "ARPA Network logical map from September 1973 showing interconnected nodes with PDP computer systems at various universities."},
        {"slide": 7, "shape_idx": 3, "alt_text": "Abstract visualization of a network topology with blue and purple interconnected nodes on a dark background."},
        {"slide": 8, "shape_idx": 2, "alt_text": "Network architecture diagram showing hosts, end systems, communication links, and bandwidth connected to global ISP infrastructure."},
        {"slide": 9, "shape_idx": 3, "alt_text": "Network diagram displaying LAN and WAN regions with Home Office, Central, Cloud, and Branch areas connected by routers."},
        {"slide": 11, "shape_idx": 3, "alt_text": "Network topology showing multiple computers and users connected through a central switch to storage and server equipment."},
        {"slide": 12, "shape_idx": 3, "alt_text": "Simplified network diagram comparing two sites connected through a red link representing a broken connection."},
        {"slide": 13, "shape_idx": 3, "alt_text": "Complex mesh network diagram showing multiple computers connected through interconnected switches."},
    ],
    # Module 1 - IOS-review (15)
    "_imgs_IOS-review": [
        {"slide": 4, "shape_idx": 3, "alt_text": "Concentric layers diagram showing Hardware, Kernel, Shell, and User Interface with CPU and hard drive at center."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Hierarchical system diagram showing Computer with Applications, OS layers, and Physical layer connected to cable medium."},
        {"slide": 7, "shape_idx": 3, "alt_text": "Layered architecture showing CLI, IOS with Network and Link layers, and Physical layer with dual network interface cards."},
        {"slide": 9, "shape_idx": 2, "alt_text": "Router device with labeled ports: Telnet Access, Serial Ports, FastEthernet Ports, Auxiliary Port, Console Port, and Modem Access."},
        {"slide": 10, "shape_idx": 2, "alt_text": "Router device with labeled ports: Telnet Access, Serial Ports, FastEthernet Ports, Auxiliary Port, Console Port, and Modem Access."},
        {"slide": 12, "shape_idx": 2, "alt_text": "IOS command hierarchies showing User EXEC, Privileged EXEC, and Interface configuration modes with syntax examples."},
        {"slide": 13, "shape_idx": 2, "alt_text": "Comparison of User EXEC mode (limited examination) versus Privileged EXEC mode (detailed configuration) with sample prompts."},
        {"slide": 14, "shape_idx": 2, "alt_text": "Flowchart showing progression from Privileged EXEC to Global Configuration to Other Configuration Modes."},
        {"slide": 14, "shape_idx": 3, "alt_text": "IOS Prompt Structure reference showing Router and Switch command examples with mode indicators."},
        {"slide": 15, "shape_idx": 2, "alt_text": "Router startup output showing User Access Verification prompts and privilege mode transitions."},
        {"slide": 20, "shape_idx": 2, "alt_text": "Memory map diagram showing IOS with ROM, RAM, NVRAM, Flash regions for Programs, Active Config, and Backup Config."},
        {"slide": 22, "shape_idx": 4, "alt_text": "Flowchart showing running configuration retrieval from RAM and copy to NVRAM process."},
        {"slide": 25, "shape_idx": 3, "alt_text": "Console line configuration commands with login and password setup for VTY line 0 15."},
        {"slide": 26, "shape_idx": 3, "alt_text": "Switch configuration commands showing enable password, secret class setup, and exit commands."},
        {"slide": 27, "shape_idx": 3, "alt_text": "VTY line 0 15 configuration with login and password for remote Telnet access."},
    ],
    # Module 1 - SSH (1)
    "_imgs_Module 1 - basic device configuration II - SSH": [
        {"slide": 2, "shape_idx": 2, "alt_text": "SSH configuration diagram showing secure tunnel between Switch S1 and router with domain configuration and crypto key commands."},
    ],
    # Module 2 - Collision Domain (1)
    "_imgs_Module 2 - Switching Concepts 2 - Collision Domain": [
        {"slide": 1, "shape_idx": 3, "alt_text": "NETGEAR managed switch with four numbered ports displaying connection ports and status indicators."},
    ],
    # Module 2 - Broadcast Domains (1)
    "_imgs_Module 2 - Switching Concepts 3 - Broacast Domains": [
        {"slide": 1, "shape_idx": 3, "alt_text": "Network diagram showing two broadcast domains with switch S1 connected to computers and switches S1/S2 interconnected."},
    ],
    # Module 2 - Complete (21)
    "_imgs_Module 2 - Switching Concepts Complete": [
        {"slide": 2, "shape_idx": 3, "alt_text": "Network model showing two end devices connected through a switch with Application, Transport, Network, Link, and Physical layers."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Network topology with computers connected to switches on both sides separated by a broken line."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Ethernet frame structure showing Preamble, Destination Address, Source Address, Type, Data, and FCS fields with byte lengths."},
        {"slide": 5, "shape_idx": 4, "alt_text": "IPv4 packet header diagram showing Version, IHL, Total length, TTL, Protocol, Source and Destination address fields."},
        {"slide": 6, "shape_idx": 3, "alt_text": "Network model showing two end devices connected through switch with protocol stack layers."},
        {"slide": 7, "shape_idx": 3, "alt_text": "Network topology with computers connected to switches separated by a broken line indicating disconnection."},
        {"slide": 9, "shape_idx": 3, "alt_text": "Network switch with port tables showing destination addresses mapped to ports."},
        {"slide": 9, "shape_idx": 11, "alt_text": "Ethernet frame structure showing Preamble, Destination Address, Source Address, Type, Data, and FCS with byte lengths."},
        {"slide": 11, "shape_idx": 3, "alt_text": "Switch S1 topology showing PC1 sending frame with port labels and MAC address table."},
        {"slide": 12, "shape_idx": 3, "alt_text": "Switch MAC table with Port 1 containing PC1 MAC, frame being forwarded between PC1 and S1."},
        {"slide": 13, "shape_idx": 3, "alt_text": "Switch with MAC table showing PC1 on Port 1 and PC3 on Port 3, frame forwarding from PC1 to PC3."},
        {"slide": 14, "shape_idx": 3, "alt_text": "Switch MAC table with entries for Port 1 (PC1) and Port 3 (PC3), showing frame forwarding process."},
        {"slide": 15, "shape_idx": 3, "alt_text": "Switch MAC table with Port 1 (PC1), Port 2 (Empty), Port 3 (PC3) with frame transmission between PCs."},
        {"slide": 16, "shape_idx": 3, "alt_text": "Switch frame forwarding with MAC table showing Port 1 (PC1), Port 2 (Empty), Port 3 (PC3)."},
        {"slide": 18, "shape_idx": 3, "alt_text": "Ethernet frame header structure with fields showing store-and-forward switching for frames up to 9200 bytes."},
        {"slide": 19, "shape_idx": 3, "alt_text": "Ethernet frame structure explaining cut-through switching where forwarding begins after Destination MAC is received."},
        {"slide": 20, "shape_idx": 3, "alt_text": "NETGEAR managed switch with four numbered connection ports and status indicators."},
        {"slide": 21, "shape_idx": 3, "alt_text": "NETGEAR managed switch with four numbered connection ports and status indicators."},
        {"slide": 23, "shape_idx": 3, "alt_text": "Network diagram showing two broadcast domains separated by a broken connection between switches."},
    ],
    # Module 3 - VLAN fundamentals (4)
    "_imgs_Lecture 1 - vlans fundamentals 1": [
        {"slide": 2, "shape_idx": 3, "alt_text": "Network topology showing two switch trees connected by a central core switch with multiple devices."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Central core switch connected to six switches with device names and IP addresses in different segments."},
        {"slide": 4, "shape_idx": 3, "alt_text": "Central core switch with six connected switches and their respective devices and IP addresses."},
        {"slide": 7, "shape_idx": 3, "alt_text": "Terminal output showing VLAN brief information with device names, status, ports, and VLAN assignments."},
    ],
    # Module 3 - Trunks (7)
    "_imgs_Lecture 2 - vlans - trunks and 802-1Q": [
        {"slide": 1, "shape_idx": 3, "alt_text": "Network topology illustrating broadcast frame forwarding between two switch trees connected by core switch."},
        {"slide": 2, "shape_idx": 3, "alt_text": "PC1 sending broadcast with switches forwarding frames, showing Ethernet addresses and port connections."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Broadcast forwarding on VLAN 10 and 20 only, with switches configured for specific VLANs across trunks."},
        {"slide": 4, "shape_idx": 3, "alt_text": "VLAN trunk configuration supporting VLAN 10 and 20 with trunk links and port assignments highlighted."},
        {"slide": 4, "shape_idx": 4, "alt_text": "Ethernet frame structure with 802.1Q tag insertion showing MAC addresses and 4-byte VLAN tag components."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Detailed 802.1Q tagged frame structure with Priority bits, CFI, and VID components breakdown."},
        {"slide": 6, "shape_idx": 3, "alt_text": "PC1 connected to central switch with three 802.1Q trunk ports connecting to switches for VLAN1, VLAN2, VLAN3."},
    ],
    # Module 3 - VLAN configuration (14)
    "_imgs_Lecture 3 - VLAN configuration": [
        {"slide": 2, "shape_idx": 3, "alt_text": "Table of Cisco IOS commands for creating a VLAN including configure terminal and vlan ID creation."},
        {"slide": 2, "shape_idx": 4, "alt_text": "VLAN 20 configuration with switch S1 connected to student PC2 via F0/18 and CLI commands."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Cisco IOS commands for assigning ports to VLANs with interface configuration and switchport mode access."},
        {"slide": 3, "shape_idx": 4, "alt_text": "Student PC connected to switch S1 port F0/18 configured for VLAN 20 with CLI commands."},
        {"slide": 4, "shape_idx": 3, "alt_text": "Terminal output showing VLAN brief and show vlan results with status, ports, type, and SAID."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Terminal showing delete VLAN commands and resulting VLAN brief table with status and port assignments."},
        {"slide": 8, "shape_idx": 3, "alt_text": "Show vlan name student command output with VLAN information and Remote SPAN VLAN status."},
        {"slide": 8, "shape_idx": 4, "alt_text": "Show interfaces vlan 20 output with VLAN status, hardware address, and MTU configuration."},
        {"slide": 9, "shape_idx": 3, "alt_text": "Three switches S1, S2, S3 connected with Faculty, Student, and Guest VLANs and IP addresses."},
        {"slide": 9, "shape_idx": 4, "alt_text": "Interface FastEthernet0/1 trunk configuration with allowed VLAN list for VLANs 10, 20, and 30."},
        {"slide": 10, "shape_idx": 3, "alt_text": "Cisco IOS commands for trunk mode configuration with interface setup and VLAN allowance."},
        {"slide": 10, "shape_idx": 4, "alt_text": "Interface configuration for FastEthernet0/1 trunk mode with allowed VLAN parameters."},
        {"slide": 11, "shape_idx": 3, "alt_text": "Interface status showing encapsulation and native VLAN information with 802.1Q tagging."},
        {"slide": 12, "shape_idx": 3, "alt_text": "Interface F0/1 switchport mode access with VLAN information highlighted in orange."},
    ],
    # Module 3 - Native VLANs (1)
    "_imgs_Lecture 5 - Native VLANs": [
        {"slide": 3, "shape_idx": 3, "alt_text": "Central switch connected to multiple switches in green and orange groups representing different VLAN assignments."},
    ],
    # Module 3 - vlans complete (38)
    "_imgs_vlans": [
        {"slide": 2, "shape_idx": 3, "alt_text": "Network topology showing two switch trees connected by a central core switch."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Central core switch connected to six switches with device names and IP addresses."},
        {"slide": 4, "shape_idx": 3, "alt_text": "Central core switch with six connected switches and their devices and IP addresses."},
        {"slide": 6, "shape_idx": 3, "alt_text": "VLAN brief information showing device names, status, ports, and VLAN assignments."},
        {"slide": 8, "shape_idx": 3, "alt_text": "Two switch trees connected by core switch with broadcast frame forwarding annotation."},
        {"slide": 9, "shape_idx": 3, "alt_text": "PC1 broadcast with switches forwarding frames showing Ethernet addresses and port connections."},
        {"slide": 10, "shape_idx": 3, "alt_text": "Broadcast forwarding on VLAN 10 and 20 only with configured switches across trunks."},
        {"slide": 11, "shape_idx": 3, "alt_text": "VLAN trunk configuration supporting VLAN 10 and 20 with trunk links highlighted."},
        {"slide": 11, "shape_idx": 4, "alt_text": "Ethernet frame with 802.1Q tag insertion showing MAC addresses and VLAN tag components."},
        {"slide": 12, "shape_idx": 3, "alt_text": "802.1Q tagged frame structure with Priority bits, CFI, and VID components."},
        {"slide": 12, "shape_idx": 4, "alt_text": "802.1Q tagged frame structure with Priority, CFI, and VID field breakdown."},
        {"slide": 13, "shape_idx": 3, "alt_text": "PC1 connected to switch with three 802.1Q trunk ports for VLAN1, VLAN2, VLAN3."},
        {"slide": 15, "shape_idx": 3, "alt_text": "Cisco IOS VLAN creation commands table with configure terminal and vlan ID steps."},
        {"slide": 15, "shape_idx": 4, "alt_text": "VLAN 20 configuration with switch S1 and student PC2 via F0/18."},
        {"slide": 16, "shape_idx": 3, "alt_text": "IOS commands for assigning ports to VLANs with switchport mode access."},
        {"slide": 16, "shape_idx": 4, "alt_text": "Student PC on switch S1 port F0/18 configured for VLAN 20."},
        {"slide": 17, "shape_idx": 3, "alt_text": "VLAN brief and show vlan results with status, ports, and type information."},
        {"slide": 18, "shape_idx": 3, "alt_text": "Delete VLAN commands and resulting VLAN brief table."},
        {"slide": 21, "shape_idx": 3, "alt_text": "Show vlan name student output with Remote SPAN VLAN status."},
        {"slide": 21, "shape_idx": 4, "alt_text": "Show interfaces vlan 20 output with status and MTU configuration."},
        {"slide": 22, "shape_idx": 3, "alt_text": "Three switches S1, S2, S3 with Faculty, Student, Guest VLANs and IP addresses."},
        {"slide": 22, "shape_idx": 4, "alt_text": "FastEthernet0/1 trunk configuration with allowed VLANs 10, 20, 30."},
        {"slide": 23, "shape_idx": 3, "alt_text": "Cisco IOS trunk mode configuration commands table."},
        {"slide": 23, "shape_idx": 4, "alt_text": "FastEthernet0/1 trunk configuration with allowed VLAN parameters."},
        {"slide": 24, "shape_idx": 3, "alt_text": "Interface status with encapsulation and native VLAN with 802.1Q tagging."},
        {"slide": 24, "shape_idx": 4, "alt_text": "Interface F0/1 switchport mode access with VLAN information highlighted."},
        {"slide": 25, "shape_idx": 3, "alt_text": "Interface status with DTP protocol details and VLAN configuration parameters."},
        {"slide": 26, "shape_idx": 3, "alt_text": "Three switches S1, S2, S3 connected with dashed trunk links."},
        {"slide": 27, "shape_idx": 3, "alt_text": "VLAN port mode compatibility matrix with Auto, Desirable, Trunk, and Access modes."},
        {"slide": 28, "shape_idx": 3, "alt_text": "Switch S1 with F0/1 trunk link to S2 and F0/3 non-trunk link to S3."},
        {"slide": 28, "shape_idx": 4, "alt_text": "VLAN port mode compatibility matrix with Dynamic modes, Trunk, and Access."},
        {"slide": 29, "shape_idx": 3, "alt_text": "Show dtp interface command results with trunking status for FastEthernet0/1."},
        {"slide": 29, "shape_idx": 4, "alt_text": "VLAN troubleshooting decision tree for port assignments and device connectivity."},
        {"slide": 30, "shape_idx": 3, "alt_text": "MAC address table entries with dynamic VLAN assignments for ports."},
        {"slide": 31, "shape_idx": 3, "alt_text": "Interface F0/1 switchport with access mode and VLAN 10 assignment highlighted."},
        {"slide": 31, "shape_idx": 4, "alt_text": "Connectivity troubleshooting flowchart with VLAN presence and address verification."},
        {"slide": 32, "shape_idx": 3, "alt_text": "Show interfaces F0/1 trunk output with port info, encapsulation, and allowed VLANs."},
        {"slide": 32, "shape_idx": 4, "alt_text": "Interface configuration with native VLAN 2 and trunk allowed VLAN lists."},
        {"slide": 33, "shape_idx": 3, "alt_text": "Table of common VLAN issues: Native VLAN Mismatches, Trunk Mode Mismatches, and Allowed VLAN problems."},
        {"slide": 34, "shape_idx": 3, "alt_text": "Network with student email server VLAN 20, web/FTP server VLAN 10, and native VLAN 99 trunk."},
        {"slide": 34, "shape_idx": 4, "alt_text": "Switch S3 and S1 interface trunk information with port modes and active VLAN listings."},
    ],
    # Module 4 - InterVLAN Intro (5)
    "_imgs_Lecture 1 - Intro to InterVLAN and Legacy InterVLAN": [
        {"slide": 2, "shape_idx": 3, "alt_text": "Network topology showing VLAN 10 and VLAN 30 connected through routers R1 and S2 with trunked interfaces."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Network topology showing VLAN 10 and VLAN 30 connected through routers with trunked interfaces."},
        {"slide": 4, "shape_idx": 3, "alt_text": "Router-on-a-stick inter-VLAN routing with IP addresses on subinterfaces for VLAN 10 and VLAN 30."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Router-on-a-stick architecture with VLAN 10 and VLAN 30 subinterface IP addresses."},
        {"slide": 5, "shape_idx": 4, "alt_text": "Cisco router configuration commands for VLAN 10 and VLAN 30 interface setup with trunk and access modes."},
    ],
    # Module 4 - Router on a stick (4)
    "_imgs_Lecture 2 - InterVLAN routing - routing on a stick": [
        {"slide": 2, "shape_idx": 3, "alt_text": "Router R1 connected to switch S1 with trunk, showing VLAN 10, VLAN 30 subinterfaces and IP subnets."},
        {"slide": 3, "shape_idx": 3, "alt_text": "Router R1 connected to switch S1 with trunk for VLAN 10 and VLAN 30 subinterfaces."},
        {"slide": 3, "shape_idx": 4, "alt_text": "Switch configuration for VLAN 10 and VLAN 30 with F0/5 configured as trunk mode."},
        {"slide": 3, "shape_idx": 5, "alt_text": "Router subinterface configuration with encapsulation and IP addresses for VLAN 10 and VLAN 30."},
    ],
    # Module 4 - L3 switches (3)
    "_imgs_Lecture 3 - L3 switches and Inter-VLAN": [
        {"slide": 4, "shape_idx": 3, "alt_text": "Comparison of traditional routing versus Layer 3 switching using virtual switched interfaces for inter-VLAN routing."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Mesh topology of four Layer 3 switches with routed interfaces and redundant paths."},
        {"slide": 6, "shape_idx": 3, "alt_text": "Three-layer network with PCs across VLANs 2, 3, 4 connected through Layer 2 and Layer 3 switches."},
    ],
    # Top Level - advance_topics (14)
    "_imgs_advance_topics": [
        {"slide": 1, "shape_idx": 4, "alt_text": "Line graph comparing packet forwarding speeds between CPU and switch chip from 1990 to 2020."},
        {"slide": 2, "shape_idx": 4, "alt_text": "System architecture showing data synchronization between clustered database nodes with control and data plane."},
        {"slide": 5, "shape_idx": 5, "alt_text": "Hardware architecture stack showing compilers: C/C++ for CPU, Matlab for DSP, OpenCL for GPU, TensorFlow for TPU, P4 for FPGA."},
        {"slide": 7, "shape_idx": 5, "alt_text": "Comparison table of network measurement parameters including threshold and switching throughput."},
        {"slide": 11, "shape_idx": 3, "alt_text": "Exponential growth graph showing CPU performance increase over time with green highlighted region."},
        {"slide": 12, "shape_idx": 3, "alt_text": "Exponential growth graph displaying performance metrics with green acceleration phase."},
        {"slide": 13, "shape_idx": 3, "alt_text": "Graph showing gap between processor speed and network port speed from 2012 to 2022."},
        {"slide": 15, "shape_idx": 3, "alt_text": "Three NIC architectures: Traditional NIC, Offload NIC, and SmartNIC with data flow paths."},
        {"slide": 16, "shape_idx": 3, "alt_text": "Three network processing architectures with packet buffer, execution layer, and data plane."},
        {"slide": 17, "shape_idx": 4, "alt_text": "Three packet processing architectures showing data flow through buffer, execution, and data plane layers."},
        {"slide": 21, "shape_idx": 4, "alt_text": "Scatter plot showing anomaly detection with normal regions N1, N2 and outlier points o1, o2."},
        {"slide": 24, "shape_idx": 4, "alt_text": "Neural network with input layer X1-X41, hidden layers, and output layer for classification."},
        {"slide": 25, "shape_idx": 2, "alt_text": "System architecture with data plane, data stores, and interconnected database nodes."},
        {"slide": 1, "shape_idx": 4, "alt_text": "System architecture showing database components, data plane, and interconnected server cluster."},
    ],
    # Top Level - Network Security (20)
    "_imgs_Network Security": [
        {"slide": 1, "shape_idx": 3, "alt_text": "Computer icon with arrow toward firewall wall and orange arrows pointing to globe representing internet."},
        {"slide": 9, "shape_idx": 3, "alt_text": "Network topology with client-server architecture, firewalls, security appliances, and interconnected devices."},
        {"slide": 10, "shape_idx": 2, "alt_text": "Protocol numbers reference table listing IP, Ethernet, DCEnet, XNS, AppleTalk, IPX, and SAP protocols."},
        {"slide": 13, "shape_idx": 3, "alt_text": "ACL syntax example showing deny and permit rules with IP addresses and subnet masks."},
        {"slide": 16, "shape_idx": 3, "alt_text": "Network flow diagram with multiple access lists showing color-coded permit and deny decisions."},
        {"slide": 17, "shape_idx": 3, "alt_text": "Guidelines table for implementing ACLs including security policies and error handling."},
        {"slide": 20, "shape_idx": 1, "alt_text": "Secure traffic versus attacking traffic illustration with protected green connections through firewall."},
        {"slide": 21, "shape_idx": 0, "alt_text": "Dynamic packet filter diagram showing client-server UDP communication with filter matching logic."},
        {"slide": 22, "shape_idx": 0, "alt_text": "Stateful packet filtering with DMZ architecture and state table tracking addresses, ports, and flags."},
        {"slide": 25, "shape_idx": 2, "alt_text": "Zero-day exploit attack flow through VPN and firewall to internal servers."},
        {"slide": 26, "shape_idx": 1, "alt_text": "DDoS attack diagram showing attacker launching from compromised nodes to management console and servers."},
        {"slide": 27, "shape_idx": 1, "alt_text": "Numbered DDoS attack progression with attacker, attack nodes, switch, and target."},
        {"slide": 28, "shape_idx": 1, "alt_text": "DDoS attack simulation with attacker, cloud, numbered attack sources, sensor, and target."},
        {"slide": 30, "shape_idx": 1, "alt_text": "Advantages and disadvantages comparison table for firewall technologies."},
        {"slide": 35, "shape_idx": 2, "alt_text": "Trusted network with computers on left side of firewall, untrusted internet on right."},
        {"slide": 36, "shape_idx": 1, "alt_text": "Data center architecture with internet connection through border router to load balancers and servers."},
        {"slide": 36, "shape_idx": 2, "alt_text": "Server rack in data center showing networked servers and storage devices in blue lighting."},
        {"slide": 37, "shape_idx": 1, "alt_text": "Network topology with internet, border routers, load balancers, and multi-tiered server cluster."},
        {"slide": 37, "shape_idx": 2, "alt_text": "Network architecture with router, load balancers, and tiered web, application, and database servers."},
    ],
    # Top Level - wlan (26 - agent found 22)
    "_imgs_wlan": [
        {"slide": 5, "shape_idx": 2, "alt_text": "Professional man looking through a modern office window with geometric lines in background."},
        {"slide": 5, "shape_idx": 3, "alt_text": "Large cellular tower with multiple transmission antennas and dishes against clear sky."},
        {"slide": 6, "shape_idx": 2, "alt_text": "Tall wireless communications tower with multiple antennas against blue sky."},
        {"slide": 8, "shape_idx": 2, "alt_text": "Electromagnetic spectrum diagram from radio waves to gamma rays with wireless device examples."},
        {"slide": 12, "shape_idx": 2, "alt_text": "External WiFi USB adapter with antenna connected to laptop for wireless connectivity."},
        {"slide": 14, "shape_idx": 2, "alt_text": "Two wireless router models showing typical access point designs for home or office."},
        {"slide": 15, "shape_idx": 2, "alt_text": "WLAN topology with core switch, distribution switches, and autonomous access points with clients."},
        {"slide": 15, "shape_idx": 3, "alt_text": "Controller-based WLAN architecture with WLC connected to controller-based AP and clients."},
        {"slide": 16, "shape_idx": 2, "alt_text": "Desktop WiFi antenna on stand showing external antenna design for wireless reception."},
        {"slide": 16, "shape_idx": 4, "alt_text": "Outdoor wireless access point with three antenna elements mounted on pole."},
        {"slide": 19, "shape_idx": 2, "alt_text": "Two laptops connected wirelessly with wavy signal line representing communication link."},
        {"slide": 19, "shape_idx": 3, "alt_text": "WLAN distribution system architecture with AP connecting wired and wireless clients."},
        {"slide": 19, "shape_idx": 4, "alt_text": "WLAN topology with laptop and smartphone connected wirelessly to AP with Internet cloud."},
        {"slide": 20, "shape_idx": 2, "alt_text": "IEEE 802.11 MAC frame format showing header, payload, and FCS with detailed field breakdown."},
        {"slide": 21, "shape_idx": 2, "alt_text": "Two WLAN BSS configurations with laptop connecting to AP showing BSSID and SSID identifiers."},
        {"slide": 23, "shape_idx": 2, "alt_text": "WLAN client-AP communication showing discover, authenticate, and associate process flows."},
        {"slide": 25, "shape_idx": 2, "alt_text": "AP beacon transmission diagram with wireless client receiving SSID and security settings."},
        {"slide": 25, "shape_idx": 4, "alt_text": "Probe request and response exchange between client and AP for SSID discovery."},
        {"slide": 28, "shape_idx": 2, "alt_text": "WiFi 2.4 GHz channel diagram showing 11 overlapping channels with 22 MHz bandwidth."},
        {"slide": 29, "shape_idx": 2, "alt_text": "802.11a 5 GHz frequency band showing 8 non-overlapping channels from 5150 to 5850 MHz."},
        {"slide": 30, "shape_idx": 2, "alt_text": "WiFi coverage pattern showing signal strength distribution in horizontal and vertical planes."},
    ],
}

# Apply alt texts
for dir_suffix, alts in all_alts.items():
    if dir_suffix not in DIR_TO_PPTX:
        print(f"SKIP: No PPTX mapping for {dir_suffix}")
        continue

    rel_path = DIR_TO_PPTX[dir_suffix]
    # Try _fixed.pptx first, then .pptx
    fixed_path = os.path.join(BASE, rel_path + "_fixed.pptx")
    orig_path = os.path.join(BASE, rel_path + ".pptx")

    source = fixed_path if os.path.exists(fixed_path) else orig_path
    if not os.path.exists(source):
        print(f"SKIP: File not found for {dir_suffix}: {source}")
        continue

    result = apply_pptx_alt_texts(source, fixed_path, alts)
    size = os.path.getsize(fixed_path) if os.path.exists(fixed_path) else 0
    print(f"{os.path.basename(fixed_path)}: applied {result['applied']}/{result['total']} alt texts ({size:,} bytes)")

print("\nDone!")
