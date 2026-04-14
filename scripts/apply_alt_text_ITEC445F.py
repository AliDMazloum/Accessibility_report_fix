"""Apply alt text to all PPTX files for ITEC445F course.

This script reads the metadata JSON, deduplicates entries, and applies
vision-generated alt text to each image in each PPTX file using
apply_pptx_alt_texts from fix_office.py.
"""
import os
import sys
import json

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_office import apply_pptx_alt_texts

BASE = "C:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report"
META_PATH = os.path.join(BASE, "data/images_needing_alt_ITEC445F.json")

# ── Alt texts generated from visual inspection of each image ──

ALT_TEXTS = {
    # ===================== wlan.pptx =====================
    "wlan.pptx": {
        (3, 2): "Group of people at a table using wireless devices including a laptop, tablet, and smartphones, illustrating the benefits of wireless connectivity.",
        (5, 2): "Man wearing Bluetooth wireless earbuds, representing Bluetooth wireless technology for device pairing.",
        (5, 3): "Cellular tower with multiple antennas against a blue sky, representing WiMAX and cellular broadband wireless technologies.",
        (6, 2): "Cellular communications tower with sector antennas mounted on a metal pole, representing cellular broadband technology.",
        (6, 3): "Communications satellite with solar panels orbiting Earth, representing satellite broadband technology.",
        (8, 2): "Diagram of the electromagnetic spectrum showing radio waves, infrared, ultraviolet, X-rays, and gamma rays, with wireless devices operating in the radio wave frequency range.",
        (12, 2): "USB wireless network adapter plugged into a laptop, illustrating an external wireless NIC for WLAN connectivity.",
        (13, 2): "Wireless home router with four external antennas and Ethernet cables connected, placed on a table in a living room.",
        (14, 2): "Two Cisco Meraki Go wireless access points, one flat and one standing upright, shown against a dark background.",
        (15, 2): "Network diagram showing an autonomous access point connected to a switch and router, wirelessly serving a smartphone, monitor, and laptop.",
        (15, 3): "Network diagram showing a controller-based access point using LWAPP protocol to communicate with a WLC, while wirelessly serving mobile devices.",
        (16, 2): "Omnidirectional wireless antenna on a stand with a cable, used to provide 360-degree Wi-Fi coverage.",
        (16, 3): "Directional parabolic grid antenna mounted on a metal pole, used to focus radio signals in a specific direction.",
        (16, 4): "MIMO antenna array with multiple antenna elements mounted on a building rooftop, used to increase wireless bandwidth.",
        (19, 2): "Diagram showing two laptops connected directly via wireless signals in ad hoc peer-to-peer mode without an access point.",
        (19, 3): "Network diagram showing infrastructure mode with a wireless access point connecting to a router, switches, and wired PCs via a distribution system, while serving wireless clients.",
        (19, 4): "Diagram showing wireless tethering where a laptop connects wirelessly to a smartphone, which provides Internet access via cellular connection.",
        (20, 2): "Diagram showing two Basic Service Sets (BSSs), each with a laptop connected to an access point identified by its BSSID MAC address.",
        (20, 3): "Diagram showing an Extended Service Area (ESA) where two BSSs are interconnected through a distribution system with switches and a router, allowing clients in different BSSs to communicate.",
        (21, 2): "Diagram of the 802.11 wireless frame structure showing Header, Payload, and FCS fields, with the header expanded to show Frame Control, Duration, four Address fields, and Sequence Control.",
        (23, 2): "Sequence diagram showing a wireless client discovering an AP, then exchanging authenticate and associate messages in a three-stage process.",
        (25, 2): "Diagram showing passive discovery mode where an AP periodically sends beacon frames containing SSID, supported standards, and security settings to a wireless client.",
        (25, 4): "Diagram showing active discovery mode where a wireless client sends a probe request with SSID and supported standards, and the AP responds with a probe response.",
        (28, 2): "Diagram of the 2.4 GHz frequency band showing 11 overlapping channels, each 22 MHz wide and separated by 5 MHz, with non-overlapping channels 1, 6, and 11 highlighted.",
        (29, 2): "Diagram of the 5 GHz frequency band showing 8 non-overlapping channels (36, 40, 44, 48, 52, 56, 60, 64) each separated by 20 MHz between 5150 and 5350 MHz.",
        (30, 2): "Floor plan of a large venue showing overlapping circular wireless coverage areas from multiple access points, illustrating WLAN deployment planning with coverage overlap at entrances and exits.",
    },

    # ===================== advance_topics.pptx =====================
    "advance_topics.pptx": {
        (1, 4): "Diagram of traditional legacy networking showing three routers, each with local routing algorithms (e.g., OSPF), local forwarding tables, and proprietary interfaces between the control and data planes.",
        (2, 4): "Diagram of SDN architecture showing a software-based centralized controller with applications at the top, connected to data plane switches via the OpenFlow interface, with header field matching and forwarding actions.",
        (3, 4): "Diagram of SDN limitations showing the same SDN architecture with OpenFlow interface, highlighting that forwarding rules are based on a fixed number of header fields and the data plane has hard-coded fixed functions.",
        (5, 5): "Timeline showing the evolution of domain-specific computing from computers (CPU with C/Java) to signal processing (DSP with Matlab) to graphics (GPU with OpenCL) to machine learning (TPU with TensorFlow) to networking (Tofino PISA with P4).",
        (7, 5): "Comparison table between a 64x100GE fixed-function ASIC switch and a 64x100GE Barefoot Tofino P4 programmable switch, showing parameters like throughput, power consumption, table scale, and additional capabilities.",
        (9, 4): "Log-scale graph of packet forwarding speeds from 1990 to 2020, comparing CPU and switch chip performance, showing switch chips reaching 12.8 Tbps and exceeding CPU speeds by over 100x.",
        (11, 3): "Graph showing processor performance growth over time from 1980 to 2015, with annotations showing 25% annual growth initially, 52% per year in the 1990s, then slowing to 23%, 12%, and 3.5% per year after Dennard scaling ended.",
        (12, 3): "Same processor performance graph emphasizing that multi-core processors have slowed down due to Amdahl's law and Moore's law has recently ended.",
        (13, 3): "Graph comparing processor speed (MIPS/socket) and network port speed (Gbps) from 2012 to 2022, showing a growing gap where network speeds outpace processor speeds after 2018.",
        (15, 3): "Block diagrams comparing three types of NICs: (a) Traditional NIC with packet buffer and DMA engine, (b) Offload NIC adding basic acceleration, and (c) SmartNIC with traffic management, domain-specific processors, and CPU cores.",
        (16, 3): "Block diagrams comparing three types of NICs: (a) Traditional NIC with packet buffer and DMA engine, (b) Offload NIC adding basic acceleration, and (c) SmartNIC with traffic management, domain-specific processors, and CPU cores.",
        (17, 4): "Block diagrams comparing three types of NICs: (a) Traditional NIC with packet buffer and DMA engine, (b) Offload NIC adding basic acceleration, and (c) SmartNIC with traffic management, domain-specific processors, and CPU cores.",
        (21, 4): "Scatter plot showing two clusters of normal data points labeled N1 and N2 on an X-Y axis, with two isolated outlier points labeled o1 and o2 representing anomalies.",
        (24, 2): "Diagram of a multi-layer perceptron neural network for network intrusion detection, with 41 input features (duration, protocol type, service, flag, etc.) connected through hidden layers to 5 output classes (Normal, Denial of Service, Remote to User, User to Root, Probing).",
    },

    # ===================== Network Security.pptx =====================
    "Network Security.pptx": {
        (1, 3): "Diagram showing a firewall as a brick wall separating a protected computer from the public Internet, with arrows showing allowed and blocked traffic.",
        (3, 3): "Timeline of firewall network security evolution from 1989 to 2019, showing key milestones: packet filtering (1989), stateful inspection (1994), mainstream growth (1995), UTM introduction (2004), NGFW (2008), and service-defined firewalls (2019).",
        (9, 3): "Network diagram showing a router firewall with Access Control Lists filtering traffic between internal network and Internet, alongside a diagram of the OSI model highlighting Layer 3 and Layer 4 inspection of source/destination IP addresses and ports.",
        (10, 2): "Table showing ACL protocol types and their number ranges: IP (1-99, 1300-1999), Extended IP (100-199, 2000-2699), Ethernet type code (200-299), DECnet (300-399), XNS (400-599), AppleTalk (600-699), and others.",
        (13, 3): "CLI output showing four ACL statements: deny host 192.168.10.1, permit 192.168.10.0 with wildcard 0.0.0.255, deny 192.168.0.0 with wildcard 0.0.255.255, and permit 192.0.0.0 with wildcard 0.255.255.255.",
        (16, 3): "Flowchart showing standard ACL processing logic for an inbound packet on Fa0/0, with sequential evaluation of permit/deny statements and traffic flow indicators showing which packets are allowed (green) or denied (red).",
        (17, 3): "Table of ACL best practices with guidelines and benefits, including basing ACLs on security policy, preparing descriptions, using a text editor to create and save ACLs, and testing on a development network first.",
        (20, 1): "Diagram showing a stateful packet filter that allows return traffic from the Internet for sessions initiated by internal users, while blocking externally originated traffic from reaching the internal network.",
        (21, 0): "Diagram showing dynamic packet filtering between a client (192.168.51.50) and server (172.16.3.4), where outgoing UDP packets are remembered and matching return packets are allowed while non-matching packets are blocked.",
        (22, 0): "Diagram showing stateful packet filtering with a firewall between the Internet, a DMZ server, and an internal server, maintaining a state table tracking source/destination addresses, ports, sequence numbers, and TCP flags.",
        (25, 2): "Network diagram showing a zero-day exploit attacking through a VPN and firewall to reach LAN resources, web server, email server, and DNS server.",
        (26, 1): "Diagram of an IDS deployment where: (1) an attacker sends traffic through a switch, (2) a sensor copies and analyzes the traffic, and (3) alerts are sent to a management console, while the attack still reaches the target.",
        (27, 1): "Diagram of an IDS deployment showing the same flow where the sensor detects the attack and alerts the management console, but cannot stop the single-packet attack from reaching and affecting the target.",
        (28, 1): "Diagram of an IPS deployment in inline mode where: (1) attacker traffic enters, (2) the sensor inspects it inline, (3) alerts the management console, and (4) drops malicious packets to a bit bucket before they reach the target.",
        (30, 1): "Comparison table of IDS vs IPS showing advantages and disadvantages: IDS has no network impact but cannot stop attacks; IPS stops trigger packets and uses normalization but may impact network latency.",
        (35, 2): "Diagram showing perimeter security concept with a firewall separating the trusted internal administered network from the untrusted public Internet.",
        (36, 1): "Diagram of a data center network hierarchy showing Internet connection through a border router, access router, load balancer, Tier 1 switches, Tier 2 switches, TOR switches, and server racks.",
        (36, 2): "Photo of a large data center aisle with rows of server racks illuminated by blue LED lights, representing a modern Microsoft Chicago data center.",
        (37, 1): "Diagram of a data center network hierarchy showing Internet connection through a border router, access router, load balancer, Tier 1 switches, Tier 2 switches, TOR switches, and server racks, with perimeter security deployed at ingress/egress points.",
        (38, 1): "Diagram of a data center network hierarchy illustrating how remote employees, mobile users, and cloud computing blur the boundary between internal and external networks, challenging perimeter-based security.",
    },

    # ===================== IOS-review.ppt (fixed as .pptx) =====================
    "IOS-review.ppt": {
        (4, 3): "Concentric circle diagram of an operating system showing Hardware at the center, surrounded by the Kernel layer, then the Shell layer, with a user at a computer accessing the system through the User Interface.",
        (5, 3): "Layered diagram of a computer's network stack showing applications at the top, then the operating system layers (Transport, Network, Link), device driver, network interface card (Link, Physical), and cable medium.",
        (7, 3): "Layered diagram of a Cisco router's architecture showing the Command Line Interface at the top, the Internetwork Operating System with Network and Link/Physical layers for multiple interfaces, connected to cable media.",
        (9, 2): "Photo of the back panel of a Cisco 1841 router showing labeled ports: FastEthernet ports for Telnet access, auxiliary port for modem access, console port for terminal access, and serial ports.",
        (10, 2): "Photo of the back panel of a Cisco 1841 router showing labeled ports: FastEthernet ports for Telnet access, auxiliary port for modem access, console port for terminal access, and serial ports.",
        (12, 2): "Hierarchical chart of IOS command modes showing User EXEC (Router>), Privileged EXEC (Router#), Global Configuration (Router(config)#), and sub-modes: Interface (config-if), Routing Engine (config-router), and Line (config-line) with their respective commands.",
        (13, 2): "Diagram showing two IOS modes: User EXEC Mode (limited examination, view-only, Switch>/Router> prompt) with an arrow leading to Privileged EXEC Mode (detailed examination, debugging, file manipulation, Switch#/Router# prompt).",
        (14, 2): "Flowchart showing the IOS mode hierarchy from Privileged EXEC Mode to Global Configuration Mode (Switch/Router(config)#) to Other Configuration Modes for specific service or interface configurations.",
        (14, 3): "IOS prompt structure examples showing how the prompt changes to denote the current CLI mode: Router> for user EXEC, Router# for privileged EXEC, Router(config)# for global configuration, and Router(config-if)# for interface configuration.",
        (15, 2): "Screenshot of a router console session showing the enable command to enter Privileged EXEC mode (Router#), the disable command to return to User EXEC mode (Router>), and the exit command to log out.",
        (20, 2): "Diagram of router memory components (RAM, NVRAM, Flash) and their contents, with associated IOS show commands: show version, show running-config, show memory, show flash, show interface, and show startup-config.",
        (22, 4): "Diagram showing the show running-config command output displaying the active configuration in RAM, with the copy running-config startup-config command to save it to NVRAM.",
        (25, 3): "CLI screenshot showing console password configuration: line console 0, password cisco, login, and exit commands on switch Sw-Floor-1.",
        (26, 3): "CLI screenshot showing privileged EXEC password configuration: enable, conf terminal, enable secret class, exit, disable, then re-entering with the enable command requiring the new password.",
        (27, 3): "CLI screenshot showing VTY line password configuration: line vty 0 15, password cisco, and login commands on switch Sw-Floor-1.",
    },

    # ===================== Module 1 - basic device configuration I.pptx =====================
    "Module 1 - basic device configuration I.pptx": {
        (4, 3): "Diagram showing switch boot process with Flash memory containing the IOS image being loaded into RAM as Cisco IOS, and NVRAM containing the startup-config being loaded into RAM as the running-config.",
        (6, 3): "Network diagram showing PC1 connected to switch S1 via console cable, with the boot system command specifying the IOS image path in flash memory, and a legend explaining command, storage device, path, and filename components.",
        (6, 4): "Text label reading 'Configure BOOT Environment Variable' as a heading for the boot system configuration slide.",
        (7, 2): "Network topology showing PC1 connected to switch S1 via console cable, with S1 connected to router R1 at IP 172.17.99.1, with notes about using console cable for initial configuration and remote management.",
        (8, 2): "Same network topology of PC1, switch S1, and router R1, illustrating that SVI is related to VLANs and all ports are assigned to VLAN 1 by default.",
        (9, 2): "Table of Cisco switch IOS commands for SVI configuration: configure terminal, ip default-gateway, end, and copy running-config startup-config.",
        (9, 3): "Table of Cisco switch IOS commands for SVI configuration: configure terminal, interface vlan 99, ip address, no shutdown, end, and copy running-config startup-config.",
        (9, 4): "Network diagram showing PC1 connected to switch S1 connected to router R1 as the default gateway, illustrating the network scenario for SVI configuration.",
        (10, 3): "CLI output of show ip interface brief and show ipv6 interface brief commands on switch S1, showing Vlan99 interface with IP 172.17.99.11 and IPv6 addresses, with status down/down.",
    },

    # ===================== IntroductionNetworks.pptx =====================
    "IntroductionNetworks.pptx": {
        (1, 3): "Screenshot of CareerBuilder.com job search results showing over 300 Network Engineer job listings with various titles, locations, and salary ranges.",
        (2, 3): "Screenshot of CareerBuilder.com showing additional Network Engineer job postings from various companies and locations.",
        (6, 3): "ARPA Network logical map from September 1973 showing the early Internet topology with nodes at universities and research institutions like MIT, Stanford, UCLA, Harvard, and Carnegie connected through IMP nodes.",
        (7, 3): "Visualization of a partial map of the Internet from 2005 showing a dense web of colorful interconnected nodes and links, illustrating the massive scale of the modern Internet.",
        (8, 2): "Network diagram showing the structure of the Internet with end systems (hosts), communication links with varying bandwidth, routers, ISPs at regional and global levels, all interconnected.",
        (9, 3): "Network diagram showing LAN and WAN topology with Home Office, Central, and Branch locations connected through the Internet via routers and switches, with LAN (yellow) and WAN (purple) areas highlighted.",
        (11, 3): "Diagram of a Local Area Network showing users at workstations, desktop computers, and IP phones connected through a central switch to a server, all within a small geographical area.",
        (12, 3): "Diagram of two LANs connected by a WAN link, showing end devices connected to switches in each LAN with a red line representing the wide area network connection between them.",
        (13, 3): "Diagram of the Internet as an interconnected collection of networks (internetwork) showing multiple LANs with switches, routers, and end devices all interconnected through WAN links.",
    },

    # ===================== review_IP_Addressing.ppt =====================
    "review_IP_Addressing.ppt": {
        (2, 3): "Diagram explaining positional notation using decimal number 192, with a table showing radix (10), exponents, positional values (100, 10, 1), numerical identifiers, and computed values summing to 192.",
        (3, 2): "Binary to decimal conversion table showing power-of-2 values (128, 64, 32, 16, 8, 4, 2, 1) with binary digits 10100000, representing the decimal value 176.",
        (3, 3): "Binary to decimal conversion table showing power-of-2 values (128, 64, 32, 16, 8, 4, 2, 1) with all binary digits set to 1 (11111111), representing the decimal value 255.",
        (4, 3): "Binary to decimal conversion table showing binary 10110000 with the answer 176, demonstrating how to sum the positional values where bits are set to 1.",
        (4, 4): "Binary to decimal conversion table showing binary 11111111 with the answer 255, demonstrating that all bits set to 1 equals the maximum octet value.",
        (5, 3): "Detailed diagram showing binary-to-decimal conversion of a 32-bit IP address (192.168.10.10) with each octet broken into bit values, binary representation, and calculated decimal values.",
        (6, 3): "Flowchart showing the decimal-to-binary conversion process for the number 168, using successive comparison and subtraction against powers of 2, resulting in binary 10101000.",
        (7, 3): "Flowchart showing the decimal-to-binary conversion process for the number 168, using successive comparison and subtraction against powers of 2, resulting in binary 10101000.",
        (8, 4): "Diagram showing the network and host portions of IPv4 address 192.168.10.10 with subnet mask 255.255.255.0, displayed in both decimal and binary, with the network and host portions color-coded.",
        (9, 4): "Table of valid subnet mask values showing binary bit patterns for subnet values 255, 254, 252, 248, 240, 224, 192, 128, and 0.",
        (10, 4): "Table showing three subnetting examples for the 10.1.1.0 network with prefix lengths /24, /25, and /26, displaying network address, first/last host, broadcast address, and number of hosts for each.",
        (11, 4): "Table showing two subnetting examples for the 10.1.1.0 network with prefix lengths /27 and /28, displaying network address, first/last host, broadcast address, and number of hosts for each.",
        (12, 4): "Network diagram of the 10.1.1.0/24 network showing router R2 connected to a switch serving four hosts at addresses 10.1.1.10, 10.1.1.11, 10.1.1.12, and 10.1.1.254.",
        (12, 5): "Table showing the binary representation of network address (all 0s in host portion), host address (mix of 0s and 1s), and broadcast address (all 1s in host portion) for the 10.1.1.0/24 network.",
        (13, 4): "Network diagram of the 10.1.1.0/24 network showing router R2 connected to a switch serving four hosts at addresses 10.1.1.10, 10.1.1.11, 10.1.1.12, and 10.1.1.254.",
        (13, 5): "Table showing the binary representation of the first host address (all 0s and a 1 in host portion = 10.1.1.1) and last host address (all 1s and a 0 in host portion = 10.1.1.254) for the 10.1.1.0/24 network.",
        (14, 3): "Diagram showing the bitwise AND operation between IPv4 address 192.168.10.10 and subnet mask 255.255.255.0 in both decimal and binary, producing the network address 192.168.10.0.",
        (15, 4): "Screenshot of Windows LAN Interface Properties dialog showing network connection settings with Internet Protocol Version 4 (TCP/IPv4) selected.",
        (15, 5): "Screenshot of Windows IPv4 Properties dialog configured with a static IP address, subnet mask 255.255.255.0, and default gateway fields filled in.",
        (16, 2): "Screenshot of a Windows command prompt showing ipconfig output displaying IP Address 10.1.1.101, Subnet Mask 255.255.255.0, Default Gateway 10.1.1.1, and DNS Servers.",
        (16, 5): "Screenshot of Windows IPv4 Properties dialog with 'Obtain an IP address automatically' (DHCP) option selected.",
        (17, 5): "Network diagram showing unicast transmission from source 172.16.4.1 to destination 172.16.4.253, with the packet going through a router and switch to reach only the specific destination host.",
        (18, 5): "Network diagram showing limited broadcast transmission from source 172.16.4.1 to destination 255.255.255.255, with the packet delivered to all hosts on the network while the router blocks it from forwarding.",
        (22, 4): "Table of legacy classful IPv4 address classes showing Class A (0-127, /8), Class B (128-191, /16), Class C (192-223, /24), Class D multicast (224-239), and Class E experimental (240-255) with their ranges and host counts.",
        (25, 4): "World map showing the five Regional Internet Registries: ARIN (North America), RIPE NCC (Europe/Middle East), APNIC (Asia Pacific), AfriNIC (Africa), and LACNIC (Latin America).",
        (27, 4): "Hierarchical diagram of the 3 tiers of ISPs showing Tier 1 (Sprint, Savvis) connected to the Internet backbone, Tier 2 (.nLayer, France Telecom), and Tier 3 (Fortress ITX, Beachcomputers) at the bottom.",
        (29, 4): "Network diagram showing dual-stack IPv4/IPv6 migration technique with devices running both protocols simultaneously, connected through a dual-stack router R1.",
        (30, 5): "Network diagram showing IPv6 tunneling technique where IPv6-only networks (PC1, PC2) communicate through an IPv4-only network via dual-stack routers R1 and R2 that encapsulate IPv6 packets in IPv4.",
        (31, 5): "Network diagram showing NAT64 translation technique where an IPv6-only network (PC1) communicates with an IPv4-only network (PC2) through a NAT64 router that translates between protocols.",
        (35, 5): "Diagram showing IPv6 address structure with 8 hextets, each containing 4 hexadecimal digits (0000-FFFF) equal to 16 binary digits, with each hextet comprising four 4-bit groups.",
        (36, 5): "Table showing IPv6 address representation rules: preferred format with leading zeros, compressed format without leading zeros, resulting in 2001:DB8:A:1000:0:0:0:100.",
        (37, 5): "Table showing IPv6 address compression rules: preferred format 2001:0DB8:0000:0000:ABCD:0000:0000:0100, with two possible compressed forms using double colon (::), noting only one :: may be used.",
        (38, 5): "Table showing IPv6 link-local address representation: preferred FE80:0000:0000:0000:0123:4567:89AB:CDEF compressed to FE80::123:4567:89AB:CDEF by omitting leading zeros and using double colon.",
        (39, 5): "Diagram showing IPv6 address structure with 64-bit prefix and 64-bit Interface ID, with example address 2001:0DB8:000A::/64 broken into its prefix and interface ID portions.",
        (41, 5): "Network diagram showing IPv6 unicast transmission from source 2001:0DB8:ACAD:1::10 to destination 2001:0DB8:ACAD:1::8, routing through a switch with all devices having IPv6 addresses.",
        (42, 4): "Tree diagram showing the six types of IPv6 unicast addresses: Global Unicast, Link-local, Loopback (::1/128), Unspecified Address (::/128), Unique Local (FC00::/7-FDFF::/7), and Embedded IPv4.",
        (46, 5): "Diagram showing IPv6 link-local address format with 10-bit prefix (1111 1110 10 = FE80::/10), 54 remaining bits, and 64-bit Interface ID, which can be automatically or manually configured.",
        (47, 5): "Network diagram showing IPv6 link-local communications where packets with FE80 source/destination addresses are forwarded by the switch but blocked by the router, keeping traffic within the local link.",
        (49, 5): "Diagram showing IPv6 global unicast address structure with Global Routing Prefix, Subnet ID, and Interface ID fields, with the first hextet ranging from 2000 to 3FFF (first 3 bits = 001).",
        (50, 5): "Diagram showing IPv6 global unicast address structure with 48-bit Global Routing Prefix, 16-bit Subnet ID, and 64-bit Interface ID, noting that /48 prefix + 16-bit subnet = /64 prefix.",
        (51, 5): "Diagram showing IPv6 global unicast address structure with 48-bit Global Routing Prefix, 16-bit Subnet ID, and 64-bit Interface ID, noting that /48 prefix + 16-bit subnet = /64 prefix.",
        (52, 5): "Diagram showing IPv6 global unicast address structure with 48-bit Global Routing Prefix, 16-bit Subnet ID, and 64-bit Interface ID, noting that /48 prefix + 16-bit subnet = /64 prefix.",
        (53, 5): "Diagram showing an IPv6 address 2001:DB8:ACAD:1::10 broken into its components: Global Routing Prefix (2001:0DB8:ACAD), Subnet ID (0001), and Interface ID (0000:0000:0000:0010).",
        (56, 5): "Diagram and CLI output showing static configuration of IPv6 global unicast addresses on router R1 interfaces (G0/0, G0/1, S0/0/0) connected to PCs and a cloud, using ipv6 address commands.",
        (57, 5): "Diagram showing the EUI-64 process: splitting a 48-bit MAC address (FC:99:47:75:CE:E0), inserting FFFE in the middle, and flipping the U/L bit to create a 64-bit interface identifier (FE:99:47:FF:FE:75:CE:E0).",
        (57, 5): "CLI output of show interface and show ipv6 interface brief commands on router R1, showing link-local addresses generated using EUI-64 process with FFFE inserted in the MAC address.",
        (60, 5): "Diagram showing dynamic link-local address format with FE80::/10 prefix (10 bits), /64 boundary, and 64-bit Interface ID generated either by EUI-64 process or random number.",
        (61, 5): "CLI output showing static configuration of link-local address FE80::1 on all router R1 interfaces (G0/0, G0/1, S0/0/0) using the ipv6 address fe80::1 link-local command.",
        (62, 5): "CLI output of show ipv6 interface brief on router R1 showing statically configured link-local address FE80::1 on all interfaces along with their global unicast addresses.",
        (63, 5): "CLI output of show ipv6 route command on router R1 displaying the IPv6 routing table with connected (C) and local (L) routes for three subnets and the multicast route FF00::/8.",
        (66, 5): "Network diagram showing IPv6 all-nodes multicast communication where router R1 sends a packet from 2001:0DB8:ACAD:1::1 to destination FF02::1, which is delivered by the switch to all hosts on the link.",
        (67, 5): "Diagram showing IPv6 solicited node multicast address construction by copying the last 24 bits of a global unicast address (00:0010) and appending them to the FF02::FF00::/104 prefix.",
    },
}


def get_unique_files(metadata):
    """Deduplicate metadata entries by (pptx_path, fixed_path) pair."""
    seen = set()
    unique = []
    for entry in metadata:
        key = (entry["pptx_path"], entry.get("fixed_path"))
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique


def main():
    # Load metadata
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    unique_files = get_unique_files(metadata)
    print(f"Found {len(metadata)} entries, {len(unique_files)} unique files\n")

    total_applied = 0
    total_files_fixed = 0

    for entry in unique_files:
        report_name = entry["report_name"]
        pptx_path = entry["pptx_path"]
        fixed_path = entry.get("fixed_path")
        images = entry["images"]

        print(f"{'='*60}")
        print(f"File: {report_name}")
        print(f"  Images needing alt text: {len(images)}")

        # Determine input file
        if fixed_path and os.path.exists(fixed_path):
            input_path = fixed_path
            output_path = fixed_path
            print(f"  Using fixed file: {fixed_path}")
        elif os.path.exists(pptx_path):
            input_path = pptx_path
            # For .ppt files, only work with the _fixed.pptx version
            if pptx_path.endswith('.ppt'):
                if fixed_path and os.path.exists(fixed_path):
                    input_path = fixed_path
                    output_path = fixed_path
                else:
                    print(f"  SKIP: .ppt file without _fixed.pptx version")
                    continue
            else:
                output_path = pptx_path.replace('.pptx', '_fixed.pptx')
                if os.path.exists(output_path):
                    input_path = output_path
            print(f"  Input: {input_path}")
            print(f"  Output: {output_path}")
        else:
            print(f"  SKIP: File not found: {pptx_path}")
            continue

        # Look up alt texts for this file
        if report_name not in ALT_TEXTS:
            print(f"  SKIP: No alt texts defined for {report_name}")
            continue

        file_alts = ALT_TEXTS[report_name]
        alt_text_list = []
        for img in images:
            key = (img["slide"], img["shape_idx"])
            if key in file_alts:
                alt_text_list.append({
                    "slide": img["slide"],
                    "shape_idx": img["shape_idx"],
                    "alt_text": file_alts[key],
                })
            else:
                print(f"  WARNING: No alt text for slide {img['slide']+1}, shape {img['shape_idx']}")

        if not alt_text_list:
            print(f"  No alt texts to apply")
            continue

        print(f"  Applying {len(alt_text_list)} alt texts...")

        try:
            result = apply_pptx_alt_texts(input_path, output_path, alt_text_list)
            print(f"  Result: {result['applied']} applied out of {result['total']} provided")
            total_applied += result['applied']
            if result['applied'] > 0:
                total_files_fixed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'='*60}")
    print(f"SUMMARY: Applied {total_applied} alt texts across {total_files_fixed} files")


if __name__ == "__main__":
    main()
