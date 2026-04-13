"""Apply alt texts to ALL ITEC445F PPTX files listed in images_needing_alt_ITEC445F.json.

This script reads the metadata JSON, generates alt texts based on slide context
and image content analysis, then applies them using apply_pptx_alt_texts.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from fix_office import apply_pptx_alt_texts

DATA = "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/data/images_needing_alt_ITEC445F.json"

# Load metadata
with open(DATA) as f:
    entries = json.load(f)


def generate_alt_from_context(slide_text, image_path=""):
    """Generate a concise alt text from the slide context and image filename.
    Used as fallback when no pre-generated alt text exists."""
    # Extract the slide title (usually first line or after removing numbers)
    lines = [l.strip() for l in slide_text.split('\n') if l.strip() and not l.strip().isdigit()]
    title = lines[0] if lines else "Presentation slide"

    # Build description from context
    if len(lines) > 1:
        # Use title + brief context
        context = lines[1] if len(lines[1]) < 100 else lines[1][:97] + "..."
        alt = f"Diagram illustrating {title.lower()}: {context}"
    else:
        alt = f"Diagram illustrating {title.lower()}."

    # Ensure it's 1-2 sentences and not too long
    if len(alt) > 200:
        alt = alt[:197] + "..."
    return alt

# Build alt text lookup keyed by (pptx_path, slide, shape_idx)
# Alt texts are generated from visual inspection of each image combined with slide context

def make_key(pptx_path, slide, shape_idx):
    return (os.path.normpath(pptx_path), slide, shape_idx)

ALT_TEXTS = {}

def add_alts(pptx_path, alts):
    """alts: list of (slide, shape_idx, alt_text)"""
    for slide, shape_idx, alt_text in alts:
        ALT_TEXTS[make_key(pptx_path, slide, shape_idx)] = alt_text

# ============================================================
# Module 1 - IntroductionNetworks (already in previous script, re-adding)
# ============================================================
add_alts("IntroductionNetworks", [
    (1, 3, "Website listing showing Network Engineer job positions with descriptions and search filters."),
    (2, 3, "Multiple job listings for Network Engineer positions with detailed descriptions and requirements."),
    (6, 3, "ARPA Network logical map from September 1973 showing interconnected nodes with PDP computer systems at various universities."),
    (7, 3, "Abstract visualization of a network topology with blue and purple interconnected nodes on a dark background."),
    (8, 2, "Network architecture diagram showing hosts, end systems, communication links, and bandwidth connected to global ISP infrastructure."),
    (9, 3, "Network diagram displaying LAN and WAN regions with Home Office, Central, Cloud, and Branch areas connected by routers."),
    (11, 3, "Network topology showing multiple computers and users connected through a central switch to storage and server equipment."),
    (12, 3, "Simplified network diagram comparing two sites connected through a red link representing a broken connection."),
    (13, 3, "Complex mesh network diagram showing multiple computers connected through interconnected switches."),
])

# ============================================================
# Module 1 - IOS-review
# ============================================================
add_alts("IOS-review", [
    (4, 3, "Concentric layers diagram showing Hardware, Kernel, Shell, and User Interface with CPU and hard drive at center."),
    (5, 3, "Hierarchical system diagram showing Computer with Applications, OS layers, and Physical layer connected to cable medium."),
    (7, 3, "Layered architecture showing CLI, IOS with Network and Link layers, and Physical layer with dual network interface cards."),
    (9, 2, "Router device with labeled ports: Telnet Access, Serial Ports, FastEthernet Ports, Auxiliary Port, Console Port, and Modem Access."),
    (10, 2, "Router device with labeled ports: Telnet Access, Serial Ports, FastEthernet Ports, Auxiliary Port, Console Port, and Modem Access."),
    (12, 2, "IOS command hierarchies showing User EXEC, Privileged EXEC, and Interface configuration modes with syntax examples."),
    (13, 2, "Comparison of User EXEC mode (limited examination) versus Privileged EXEC mode (detailed configuration) with sample prompts."),
    (14, 2, "Flowchart showing progression from Privileged EXEC to Global Configuration to Other Configuration Modes."),
    (14, 3, "IOS Prompt Structure reference showing Router and Switch command examples with mode indicators."),
    (15, 2, "Router startup output showing User Access Verification prompts and privilege mode transitions."),
    (20, 2, "Memory map diagram showing IOS with ROM, RAM, NVRAM, Flash regions for Programs, Active Config, and Backup Config."),
    (22, 4, "Flowchart showing running configuration retrieval from RAM and copy to NVRAM process."),
    (25, 3, "Console line configuration commands with login and password setup for VTY line 0 15."),
    (26, 3, "Switch configuration commands showing enable password, secret class setup, and exit commands."),
    (27, 3, "VTY line 0 15 configuration with login and password for remote Telnet access."),
])

# ============================================================
# Module 1 - SSH
# ============================================================
add_alts("SSH", [
    (2, 2, "SSH configuration diagram showing secure tunnel between Switch S1 and router with domain configuration and crypto key commands."),
])

# ============================================================
# Module 10 - Lecture 1 LAN Security Concepts
# ============================================================
add_alts("Lecture 1 LAN Security Concepts", [
    (2, 4, "Security diagram showing an opponent (hacker or malware) attempting access through an access channel to a gatekeeper function at a doorway."),
    (2, 5, "Security diagram illustrating network threat concepts with opponent and gatekeeper roles."),
    (2, 6, "Security diagram illustrating network threat concepts with opponent and gatekeeper roles."),
    (2, 7, "Man-in-the-middle attack diagram showing Darth intercepting communication between Bob and Alice through the Internet."),
    (3, 4, "Security diagram showing an opponent attempting access through an access channel to a gatekeeper function at a doorway."),
    (3, 5, "Security diagram illustrating network threat concepts with access control."),
    (3, 6, "Security diagram illustrating network threat concepts with access control."),
    (3, 7, "Man-in-the-middle attack diagram showing Darth intercepting communication between Bob and Alice through the Internet."),
    (4, 4, "Network perimeter security diagram showing trusted network behind a firewall separating it from untrusted public Internet."),
    (5, 5, "Web Security Appliance (WSA) workflow showing a user request being evaluated and blocked when the URL is on a blacklist."),
    (5, 6, "Email Security Appliance (ESA) workflow showing a phishing attack being intercepted and discarded by the ESA."),
    (6, 4, "Router CLI showing VTY line 0 4 configuration with password and login commands for basic access control."),
    (7, 4, "Router CLI showing SSH configuration with domain name, RSA key generation, username, and transport input commands."),
    (8, 4, "AAA components diagram comparing authentication, authorization, and accounting to credit card usage with a table of examples."),
    (10, 4, "Local AAA authentication flow showing a remote client connecting to an AAA router that authenticates using its local database."),
    (11, 4, "Server-based AAA authentication flow showing a remote client connecting through an AAA router to a centralized AAA server."),
    (12, 4, "AAA authorization diagram showing the router requesting authorization from the AAA server and receiving a PASS/FAIL response."),
    (13, 4, "AAA accounting diagram showing the router sending start and stop messages to the AAA server to track user session activity."),
    (14, 4, "802.1X port-based access control diagram with Supplicant (client), Authenticator (switch), and Authentication server roles."),
    (15, 4, "802.1X architecture showing the Supplicant requesting access, Authenticator controlling port access, and Authentication server verifying identity."),
    (16, 4, "802.1X architecture showing the Supplicant requesting access, Authenticator controlling port access, and Authentication server verifying identity."),
    (17, 4, "802.1X architecture showing the Supplicant requesting access, Authenticator controlling port access, and Authentication server verifying identity."),
])

# ============================================================
# Module 10 - Lecture 2 LAN Security Threats
# ============================================================
add_alts("Lecture 2 LAN Security Threats", [
    (2, 5, "OSI model layers 1-7 showing Layer 2 Data Link highlighted as the initial compromise point for LAN attacks."),
    (7, 4, "Switch CLI output showing an empty MAC address table using the show mac-address-table command."),
    (7, 5, "Packet Tracer network topology with four PCs connected to switch Switch0 showing their MAC addresses and port connections."),
    (7, 8, "Switch CLI output showing a populated MAC address table with four dynamic entries mapping MAC addresses to ports."),
    (9, 4, "MAC address flooding attack diagram showing a threat actor sending fake MAC addresses to a switch connected to VLAN 10."),
])

# ============================================================
# Module 10 - Lecture 3 Attack Examples
# ============================================================
add_alts("Lecture 3 Attack Examples", [
    (2, 4, "VLAN hopping attack diagram showing an attacker establishing an unauthorized 802.1Q trunk to access server VLANs."),
    (3, 3, "VLAN hopping attack diagram showing an attacker with an unauthorized trunk link gaining access to all VLANs."),
    (4, 4, "VLAN double-tagging attack step 1: attacker sends a frame with outer VLAN 10 tag and inner VLAN 20 tag to the switch."),
    (5, 4, "VLAN double-tagging attack step 2: first switch strips the outer VLAN 10 tag and forwards the frame with VLAN 20 tag remaining."),
    (6, 4, "VLAN double-tagging attack step 3: second switch reads the VLAN 20 tag and forwards the frame to the target on VLAN 20."),
    (8, 4, "DHCP message exchange sequence showing DHCPDISCOVER, DHCPOFFER, DHCPREQUEST, and DHCPACK between server and client."),
    (9, 4, "Hooded hacker figure with skull and crossbones on a laptop representing a DHCP starvation attacker."),
    (10, 4, "Network diagram showing a legitimate DHCP server and a rogue DHCP server both connected to interconnected switches."),
    (11, 4, "DHCP spoofing attack step 1: network with rogue and valid DHCP servers connected to switches."),
    (11, 5, "DHCP spoofing attack step 2: DHCP client broadcasts Discover messages to both legitimate and rogue DHCP servers."),
    (11, 6, "DHCP spoofing attack step 3: both servers respond with DHCP Offer messages to the client through the switches."),
    (11, 7, "DHCP spoofing attack step 4: client sends DHCP Request accepting the rogue server's offer that arrived first."),
    (11, 8, "DHCP spoofing attack step 5: rogue DHCP server sends DHCP Ack to acknowledge and complete the attack."),
    (12, 4, "ARP communication diagram showing PC1, PC2 (attacker), and router R1 with their IP addresses, MAC addresses, and ARP cache tables."),
    (14, 4, "ARP spoofing attack showing PC2 sending gratuitous ARP messages to poison the ARP caches of PC1 and router R1."),
    (15, 5, "ARP spoofing man-in-the-middle result showing PC1 and R1 ARP caches poisoned with attacker PC2's MAC address (CC:CC:CC)."),
    (16, 4, "MAC address spoofing attack showing attacker PC2 claiming PC1's MAC address, causing the switch to update its MAC table."),
    (17, 4, "STP attack diagram showing an attacker broadcasting BPDUs with priority 0 to become root bridge while legitimate root has priority 8192."),
    (17, 5, "STP attack result showing the attacker successfully becoming root bridge with all switch ports forwarding traffic through it."),
    (18, 4, "Wireshark packet capture showing contents of a CDP packet revealing device information including IOS version and platform."),
    (19, 4, "Wireshark packet capture showing CDP packet contents that an attacker could exploit to discover network vulnerabilities."),
])

# ============================================================
# Module 11 - Lecture 1 Port Security
# ============================================================
add_alts("Lecture 1 Port Security", [
    (2, 4, "Switch CLI showing interface range fa0/8-24 shutdown command to disable unused ports with status change messages."),
    (3, 4, "Port security diagram showing a switch with allowed MAC table, permitting legitimate devices and blocking unauthorized ones."),
    (4, 4, "Switch CLI showing port-security enable commands with initial rejection on dynamic port, then success after setting access mode."),
    (5, 4, "Switch CLI output of show port-security interface f0/1 displaying security status, violation mode, and MAC address settings."),
    (5, 5, "Port security diagram showing a switch with allowed MAC table, permitting legitimate devices and blocking unauthorized ones."),
    (6, 4, "Switch CLI showing switchport port-security maximum command with help output displaying range 1-8192 for maximum addresses."),
    (7, 4, "Switch CLI showing port security configuration with maximum 2 MAC addresses, one static and one sticky, with verification output."),
    (8, 4, "Port security aging command syntax table showing parameters: static, time, type absolute, and type inactivity with descriptions."),
    (8, 5, "Switch CLI showing port-security aging configuration with 10-minute inactivity timer and verification output."),
    (9, 5, "Security violation modes comparison table showing Protect, Restrict, and Shutdown behaviors for traffic forwarding and logging."),
    (11, 3, "Switch CLI showing port-security violation mode changed to Restrict with show port-security interface output confirming settings."),
    (12, 4, "Switch CLI output of show port-security showing all ports with MaxSecureAddr, CurrentAddr, SecurityViolation counts and actions."),
    (12, 5, "Switch CLI output of show port-security interface fastethernet 0/18 showing enabled status and security details."),
    (13, 4, "Switch CLI output of show run showing interface FastEthernet0/19 with port-security and sticky MAC address configuration."),
    (13, 5, "Switch CLI output of show port-security address displaying secure MAC address table with SecureDynamic and SecureSticky types."),
])

# ============================================================
# Module 12 - Lecture 1 - Introduction to Routing and LPM
# ============================================================
add_alts("Lecture 1 - Introduction to Routing and LPM", [
    (3, 4, "Network topology with routers R1 and R2 connected to switches S1-S4 and PCs, showing IPv4/IPv6 addresses and interface labels."),
    (4, 4, "Network topology with routers R1 and R2 showing routing table and packet forwarding path between LAN segments."),
    (6, 4, "Longest prefix match table comparing three IPv4 route entries with binary representations for destination 172.16.0.10."),
    (7, 4, "Longest prefix match table for IPv6 showing three route entries with varying prefix lengths for destination 2001:db8:c000::99."),
    (8, 4, "Network topology with directly connected and remote networks labeled and highlighted from router R1's perspective."),
])

# ============================================================
# Module 12 - Lecture 2 - Packet Forwarding
# ============================================================
add_alts("Lecture 2 - Packet Forwarding", [
    (2, 4, "Packet forwarding decision flowchart showing the process from frame arrival through routing table lookup to forwarding or dropping."),
    (3, 4, "End-to-end packet forwarding showing PC1 sending to PC2 through R1 with Layer 2 frame encapsulation and ARP cache details."),
    (4, 4, "End-to-end packet forwarding at router R1 showing ARP cache, routing table lookup, and new frame encapsulation for next hop."),
    (5, 4, "End-to-end packet forwarding at router R2 showing ARP table lookup and frame delivery to destination PC2 on the local network."),
    (7, 4, "Process switching architecture showing every packet routed from ingress to egress interface through the CPU control plane."),
    (8, 4, "Fast switching architecture with CPU processing only the first packet and using a fast-forward cache for subsequent packets."),
    (9, 4, "Cisco Express Forwarding architecture using FIB and adjacency table in the data plane for hardware-based packet forwarding."),
])

# ============================================================
# Module 12 - Lecture 3 - Basic Router Configuration
# ============================================================
add_alts("Lecture 3 - Basic Router Configuration", [
    (2, 4, "Network topology with routers R1 and R2 connected to switches S1-S4 and PCs with IPv4/IPv6 addresses on all interfaces."),
    (3, 4, "Network topology with routers R1 and R2 connected to switches and PCs showing interface addresses."),
    (3, 5, "Router R1 CLI showing basic configuration commands including hostname, passwords, SSH, logging, and banner setup."),
    (4, 4, "Network topology with routers R1 and R2 connected to switches and PCs showing interface addresses."),
    (4, 5, "Router R1 CLI showing interface configuration with IPv4 and IPv6 addresses for GigabitEthernet and Serial interfaces."),
])

# ============================================================
# Module 12 - Lecture 4 - Understanding the Routing Table
# ============================================================
add_alts("Lecture 4 - Understanding the Routing Table", [
    (3, 4, "Network topology with routers R1, R2, ISP connected to switches S1-S4 and PCs showing all interface IP addresses."),
    (4, 4, "Network topology with routers R1, R2, ISP connected to switches S1-S4 and PCs showing all interface IP addresses."),
    (4, 5, "Router R1 show ip route output displaying route codes legend, directly connected, local, and OSPF-learned routes."),
    (5, 3, "Network topology with routers R1, R2, ISP connected to switches and PCs showing interface addresses."),
    (6, 4, "Routing table entry anatomy diagram showing color-coded fields: route source, destination, AD, metric, next-hop, timer, and exit interface."),
    (7, 4, "Router R1 CLI showing show ip route and show ipv6 route output with directly connected (C) and local (L) route entries."),
    (7, 5, "Network topology with routers and switches showing interface addresses for directly connected routes context."),
    (8, 4, "Network topology with routers R1 and R2 showing interface addresses for static routes context."),
    (8, 5, "Router R1 CLI showing show ip route static and show ipv6 route static output with static route entries for remote networks."),
    (9, 4, "Router R1 CLI showing ip route commands configuring static routes with next-hop address and topology diagram."),
    (10, 4, "Router R1 CLI showing ip route commands configuring static routes with next-hop address and topology diagram."),
    (10, 5, "Router R1 CLI showing show ip route static and show ipv6 route static confirming the configured static routes."),
    (11, 4, "Network topology with R1 and R2 exchanging routing information through dynamic routing protocol, with speech bubbles showing shared networks."),
    (12, 4, "Network topology showing R1 and R2 with dynamic routing protocol exchange annotations and speech bubbles."),
    (12, 5, "Router R1 CLI showing show ip route and show ipv6 route output with OSPF-learned dynamic routes (O code)."),
    (14, 4, "Network topology highlighting the path from R2 through ISP to Internet with numbered steps for default route context."),
    (14, 5, "Router R2 CLI showing show ip route and show ipv6 route output with default static routes (S* 0.0.0.0/0 and S ::/0)."),
])

# ============================================================
# Module 12 - Lecture 5 - Routing Table Structure and AD
# ============================================================
add_alts("Lecture 5 - Routing Table Structure and AD", [
    (6, 4, "Router show ip route output showing classful routing table structure with parent and child route entries."),
    (7, 4, "Router show ip route output highlighting child routes indented under the classful parent route 10.0.0.0/8."),
    (8, 4, "Router show ip route output highlighting the parent route entry above indented child subnet routes."),
    (9, 4, "Router show ipv6 route output showing flat IPv6 routing table structure without classful parent/child hierarchy."),
    (11, 4, "Administrative distance table listing route sources from most trusted (Connected, AD=0) to least trusted (Internal BGP, AD=200)."),
])

# ============================================================
# Module 13 - Lecture 1 - Static Routing
# ============================================================
add_alts("Lecture 1 - Static Routing", [
    (2, 4, "Comparison table of dynamic vs static routing across configuration complexity, topology changes, scaling, security, and resource usage."),
    (5, 4, "IPv4 static route command syntax reference table showing parameters: network-address, subnet-mask, ip-address, exit-intf, and distance."),
    (6, 4, "IPv6 static route command syntax reference table showing parameters: ipv6-prefix/length, ipv6-address, exit-intf, and distance."),
    (7, 4, "Network topology with three routers R1, R2, R3 connected via serial links with PCs showing IPv4 and IPv6 subnet addresses."),
    (8, 4, "Network topology with three routers R1, R2, R3 and PCs showing IPv4/IPv6 addresses on all interfaces."),
    (8, 5, "Router R1 show ip route output showing only directly connected and local routes with no static routes configured."),
    (9, 4, "Network topology with three routers and PCs for static route configuration context."),
    (9, 5, "Router R1 CLI showing three ip route commands configuring next-hop static routes to remote networks via 172.16.2.2."),
    (10, 4, "Network topology with three routers and PCs for static route configuration context."),
    (10, 5, "Router R1 CLI showing ip route commands configuring next-hop static routes to remote networks."),
    (10, 6, "Router R1 CLI showing show ip route static output verifying the configured static routes with next-hop addresses."),
    (11, 4, "Network topology with three routers and PCs for IPv6 static route configuration context."),
    (11, 5, "Router R1 CLI showing ipv6 route commands configuring next-hop IPv6 static routes to remote networks."),
    (11, 6, "Router R1 CLI showing show ipv6 route static output verifying the configured IPv6 static routes."),
    (12, 4, "Network topology with three routers and PCs for directly connected static route context."),
    (12, 5, "Router R1 CLI showing ip route commands configuring directly connected static routes using exit interface Serial0/1/0."),
    (13, 4, "Network topology with three routers and PCs for directly connected static route context."),
    (13, 5, "Router R1 CLI showing show ip route static verifying directly connected static routes via Serial0/1/0."),
    (14, 4, "Network topology with three routers and PCs for fully specified static route context."),
    (14, 5, "Router R1 CLI showing ip route commands with both exit interface and next-hop address for fully specified routes."),
    (14, 6, "Router R1 CLI showing show ip route static verifying fully specified static routes."),
    (15, 4, "Network topology with three routers and PCs for IPv6 directly connected static route context."),
    (15, 5, "Router R1 CLI showing ipv6 route commands configuring directly connected static routes using exit interface."),
    (16, 4, "Network topology with three routers and PCs for IPv6 fully specified static route context."),
    (16, 5, "Router R1 CLI showing ipv6 route commands with both exit interface and next-hop link-local address."),
    (16, 6, "Router R1 CLI showing show ipv6 route static verifying fully specified IPv6 static routes."),
    (17, 4, "Network topology with three routers and PCs for static route verification context."),
    (17, 5, "Router R1 CLI showing show ip route static and show ipv6 route static verifying all configured routes."),
    (18, 4, "Network topology with three routers and PCs for static route verification context."),
    (18, 5, "Router R1 CLI showing show running-config with static route configuration and verification commands."),
    (18, 6, "Router R1 CLI showing show ip route verifying all static routes in the routing table."),
    (20, 4, "Network topology with three routers and PCs for R3 static route configuration context."),
    (20, 5, "Router R3 CLI showing ip route commands configuring static routes from R3 to remote networks."),
    (21, 4, "Network topology with three routers and PCs for R3 static route configuration context."),
    (21, 5, "Router R3 CLI showing ipv6 route commands configuring IPv6 static routes from R3."),
    (21, 6, "Router R3 CLI showing show ipv6 route static verifying configured IPv6 static routes."),
    (23, 4, "Network topology with three routers and PCs for R2 static route configuration context."),
    (24, 4, "Network topology with three routers and PCs for R2 static route configuration context."),
    (24, 5, "Router R2 CLI showing ip route and ipv6 route commands configuring static routes from R2 to all remote networks."),
    (25, 4, "Network topology with three routers and PCs for verifying full connectivity."),
    (25, 5, "Router R2 CLI showing show ip route and show ipv6 route verifying all static routes from R2."),
    (25, 6, "Ping output showing successful connectivity test from PC1 to remote network destinations."),
])

# ============================================================
# Module 13 - Lecture 2 - Default Route
# ============================================================
add_alts("Lecture 2 - Default Route", [
    (3, 4, "Network topology with three routers and PCs for default route configuration context."),
    (3, 5, "Router R1 CLI showing ip route 0.0.0.0 0.0.0.0 command configuring a default static route."),
    (4, 4, "Network topology with three routers and PCs for default route configuration context."),
    (4, 5, "Router R1 CLI showing show ip route static output with default route (S* 0.0.0.0/0) entry."),
    (5, 4, "Network topology with three routers and PCs for IPv6 default route context."),
    (6, 4, "Network topology with three routers and PCs for floating static route context."),
    (6, 5, "Router CLI showing ip route commands with different administrative distances for primary and backup floating static routes."),
    (7, 4, "Network topology with three routers and PCs for floating static route context."),
    (7, 5, "Router CLI showing show ip route and show ipv6 route output with primary and backup route entries."),
    (7, 6, "Router CLI showing show ip route output after primary link failure, now using the floating static backup route."),
    (8, 4, "Network topology with three routers and PCs for static host route context."),
    (8, 5, "Router CLI showing ip route commands configuring host routes with /32 subnet mask."),
    (9, 4, "Network topology with three routers and PCs for static host route verification context."),
    (9, 5, "Router CLI showing show ip route output with host route entries verified."),
    (9, 6, "Router CLI showing show ipv6 route with host route entries verified."),
])

# ============================================================
# Module 13 - Lecture 4 - Static Host Routes
# ============================================================
add_alts("Lecture 4 - Static Host Routes", [
    (3, 4, "Network topology with three routers and PCs for static host route context."),
    (3, 5, "Router CLI showing ip route command configuring a static host route with /32 mask."),
    (4, 4, "Network topology with routers showing automatically installed local host routes for connected interfaces."),
    (5, 4, "Network topology with three routers and PCs for IPv6 static host route context."),
    (5, 5, "Router CLI showing ipv6 route command configuring an IPv6 static host route with /128 prefix."),
    (6, 4, "Network topology with routers and PCs for static host route configuration context."),
    (6, 5, "Router CLI showing show ip route and show ipv6 route output with static host route entries."),
    (6, 6, "Router CLI showing additional show route output with host routes verified."),
    (7, 4, "Network topology with three routers for troubleshooting static routes context."),
    (8, 4, "Router CLI showing ping and traceroute output for verifying connectivity with static routes."),
    (9, 4, "Network topology with routers for troubleshooting static routes context."),
    (9, 5, "Router CLI showing show ip route output during troubleshooting of static route issues."),
    (9, 6, "Router CLI showing interface status and configuration details during troubleshooting."),
])

# ============================================================
# Module 2 - Switching Concepts (already in previous script)
# ============================================================
add_alts("Module 2 - Switching Concepts 2 - Collision Domain", [
    (1, 3, "NETGEAR managed switch with four numbered ports displaying connection ports and status indicators."),
])

add_alts("Module 2 - Switching Concepts 3 - Broacast Domains", [
    (1, 3, "Network diagram showing two broadcast domains with switch S1 connected to computers and switches S1/S2 interconnected."),
])

add_alts("Module 2 - Switching Concepts Complete", [
    (2, 3, "Network model showing two end devices connected through a switch with Application, Transport, Network, Link, and Physical layers."),
    (3, 3, "Network topology with computers connected to switches on both sides separated by a broken line."),
    (5, 3, "Ethernet frame structure showing Preamble, Destination Address, Source Address, Type, Data, and FCS fields with byte lengths."),
    (5, 4, "IPv4 packet header diagram showing Version, IHL, Total length, TTL, Protocol, Source and Destination address fields."),
    (6, 3, "Network model showing two end devices connected through switch with protocol stack layers."),
    (7, 3, "Network topology with computers connected to switches separated by a broken line indicating disconnection."),
    (9, 3, "Network switch with port tables showing destination addresses mapped to ports."),
    (9, 11, "Ethernet frame structure showing Preamble, Destination Address, Source Address, Type, Data, and FCS with byte lengths."),
    (11, 3, "Switch S1 topology showing PC1 sending frame with port labels and MAC address table."),
    (12, 3, "Switch MAC table with Port 1 containing PC1 MAC, frame being forwarded between PC1 and S1."),
    (13, 3, "Switch with MAC table showing PC1 on Port 1 and PC3 on Port 3, frame forwarding from PC1 to PC3."),
    (14, 3, "Switch MAC table with entries for Port 1 (PC1) and Port 3 (PC3), showing frame forwarding process."),
    (15, 3, "Switch MAC table with Port 1 (PC1), Port 2 (Empty), Port 3 (PC3) with frame transmission between PCs."),
    (16, 3, "Switch frame forwarding with MAC table showing Port 1 (PC1), Port 2 (Empty), Port 3 (PC3)."),
    (18, 3, "Ethernet frame header structure with fields showing store-and-forward switching for frames up to 9200 bytes."),
    (19, 3, "Ethernet frame structure explaining cut-through switching where forwarding begins after Destination MAC is received."),
    (20, 3, "NETGEAR managed switch with four numbered connection ports and status indicators."),
    (21, 3, "NETGEAR managed switch with four numbered connection ports and status indicators."),
    (23, 3, "Network diagram showing two broadcast domains separated by a broken connection between switches."),
])

# ============================================================
# Module 3 - VLANs (already in previous script, includes extras from JSON)
# ============================================================
add_alts("vlans_extra", [
    (27, 4, "VLAN port mode compatibility matrix showing Dynamic Auto, Desirable, Trunk, and Access negotiation results."),
    (30, 4, "VLAN connectivity troubleshooting flowchart for verifying port assignments and device reachability."),
    (33, 4, "Table of common trunk issues: Native VLAN Mismatches, Trunk Mode Mismatches, and Allowed VLAN problems."),
])

# ============================================================
# Module 4 - InterVLAN (existing entries already covered, plus Module4-interVLAN new)
# ============================================================
add_alts("Module4-interVLAN", [
    (2, 3, "Network topology showing VLAN 10 and VLAN 30 connected through router R1 and switch S2 with access port connections."),
    (3, 3, "Legacy inter-VLAN routing diagram with router R1 using separate physical interfaces for VLAN 10 and VLAN 30."),
    (4, 3, "Legacy inter-VLAN routing with IP addresses on router R1 interfaces connected to switch S1 for VLANs 10 and 30."),
    (5, 3, "Legacy inter-VLAN routing with IP addresses on router R1 interfaces for VLANs 10 and 30."),
    (5, 4, "Switch S1 CLI showing VLAN creation and port assignment commands for VLANs 10 and 30 on access ports."),
    (6, 3, "Router-on-a-stick topology with R1 using subinterfaces G0/0.10 and G0/0.30 through a single trunk link to switch S1."),
    (7, 3, "Router-on-a-stick topology showing trunk link between R1 and S1 with subinterface IP addresses for VLANs 10 and 30."),
    (7, 4, "Switch S1 CLI showing VLAN creation and trunk mode configuration on interface F0/5."),
    (7, 5, "Router R1 CLI showing subinterface configuration with dot1Q encapsulation and IP addresses for VLANs 10 and 30."),
    (9, 3, "Three-tier network topology with Central area containing router R2, distribution switches D1/D2, access switches S1/S2, and PCs."),
    (11, 3, "Three-layer network hierarchy with L3 switches at Core and Distribution layers and L2 switches at Access layer."),
    (12, 3, "Three-layer network hierarchy with L3 switches at Core and Distribution layers and L2 switches at Access layer."),
    (13, 3, "Comparison of traditional router inter-VLAN routing vs Layer 3 switch inter-VLAN routing using SVI interfaces."),
    (14, 3, "Mesh topology of Layer 3 switches with routed interfaces for point-to-point links between distribution and core layers."),
    (15, 3, "Network topology showing Layer 2 switch S1, Layer 3 switch, and Layer 2 switch S2 with trunk links and VLANs 2-4."),
    (16, 3, "Network topology showing Layer 2 switch S1, Layer 3 switch, and Layer 2 switch S2 with trunk links and VLANs 2-4."),
])

# ============================================================
# Module 5 - Spanning Tree Protocol - Lecture 2 Building the Spanning Tree
# ============================================================
add_alts("Lecture 2 - Building the Spanning Tree", [
    (3, 3, "STP topology with switches S1, S2, S3 showing bridge IDs and priorities, with S1 elected as root bridge (priority 24577)."),
    (4, 3, "STP topology with equal bridge priorities showing S2 elected as root bridge due to lowest MAC address."),
    (5, 3, "STP port cost table showing IEEE 802.1D-1998 and RSTP 802.1w-2004 costs for 10 Gbps, 1 Gbps, 100 Mbps, and 10 Mbps links."),
    (6, 3, "STP topology showing root port selection on S2 and S3 based on path costs, with Path 1 (cost 19) preferred over Path 2 (cost 38)."),
    (7, 3, "STP topology with designated ports and root ports labeled on all switches, S1 as root bridge."),
    (8, 3, "STP topology showing final port roles: root ports, designated ports, and alternate (blocked) port on S3 F0/2."),
    (10, 3, "STP topology with switches S1, S2, S3 showing bridge IDs and priorities, with S1 as root bridge."),
    (11, 3, "STP topology showing root port selection with S2 as root bridge due to lowest MAC address among equal priorities."),
    (12, 3, "STP topology showing root port selection based on path costs with Path 1 preferred over Path 2."),
    (13, 3, "STP topology with all port roles labeled: designated ports, root ports, and alternate blocked port."),
    (13, 4, "STP timer diagram showing port state transitions: Blocking (20s Max Age), Listening (15s), Learning (15s), then Forwarding."),
])

# ============================================================
# Module 5 - STP Concepts
# ============================================================
add_alts("STP Concepts", [
    (2, 3, "Three switches S1, S2, S3 connected in a triangle with trunk links, S3-F0/2 blocked by STP to prevent loops."),
    (3, 3, "Three switches connected with trunk links showing STP blocking redundant path to prevent broadcast storms."),
    (4, 3, "Three switches with BPDU frames being exchanged between all switch ports for STP election process."),
    (5, 3, "STP root bridge election showing S1 as root bridge with lowest bridge ID among eight interconnected switches with blocked ports."),
    (9, 3, "STP topology with switches showing bridge IDs and priorities, S1 elected as root bridge with priority 24577."),
    (10, 3, "STP topology showing S2 elected as root bridge with lowest MAC address when all priorities are equal."),
    (11, 3, "STP port cost table showing costs for 10 Gbps, 1 Gbps, 100 Mbps, and 10 Mbps link speeds."),
    (12, 3, "STP topology showing root port selection based on path cost calculation with preferred path highlighted."),
    (13, 3, "STP topology with designated ports, root ports, and alternate blocked port labeled on all switches."),
    (14, 3, "STP topology showing final port roles with S1 root bridge, root ports on S2/S3, and blocked alternate port."),
    (16, 3, "Four switches S1-S4 in a ring topology showing bridge IDs, port roles, and one alternate blocked port."),
    (17, 3, "STP port priority tiebreaker showing S1 and S4 with dual links, F0/6 as root port and F0/5 as alternate based on port priority."),
    (18, 3, "STP port state transition flowchart: Blocking to Listening (15s Forward Delay) to Learning (15s) to Forwarding."),
    (19, 3, "STP port state transition flowchart showing Blocking, Listening, Learning, and Forwarding states with timers."),
    (19, 4, "STP port states reference table describing Blocking, Listening, Learning, Forwarding, and Disabled state behaviors."),
])

# ============================================================
# Module 6 - EtherChannel - Lecture 1
# ============================================================
add_alts("Lecture 1 - Introduction to EtherChannel", [
    (3, 3, "Three switches with redundant links where STP blocks two ports to prevent loops, reducing available bandwidth."),
    (4, 3, "Three switches with EtherChannel bundles combining multiple physical links into logical channels, avoiding STP blocking."),
    (5, 3, "Three switches with EtherChannel bundles combining redundant links into logical port channels."),
    (6, 3, "Switch front panel showing logical port channel interfaces mapping to physical port groups."),
    (7, 3, "Switch front panel showing logical port channel interfaces with channel group binding of physical ports."),
    (8, 3, "Two switches S1 and S2 connected with an EtherChannel bundle of multiple links shown as a single logical connection."),
    (9, 3, "Two switches S1 and S2 connected with an EtherChannel bundle of multiple parallel links."),
    (10, 4, "Two switches S1 and S2 with PAgP protocol negotiating EtherChannel formation between them."),
    (10, 5, "PAgP mode compatibility table showing channel establishment results for On, Desirable, and Auto mode combinations."),
    (11, 3, "Two switches S1 and S2 connected with an EtherChannel bundle for LACP configuration context."),
    (12, 4, "Two switches S1 and S2 with LACP protocol negotiating EtherChannel formation between them."),
    (12, 5, "LACP mode compatibility table showing channel establishment results for On, Active, and Passive mode combinations."),
])

# ============================================================
# Module 7 - DHCPv4 - Introduction to DHCP
# ============================================================
add_alts("Introduction to DHCP", [
    (3, 4, "DHCPv4 client-server communication showing step 1 (client broadcast) and step 2 (server response) through a switch."),
    (4, 4, "DHCPv4 four-step message exchange: DHCPDISCOVER broadcast, DHCPOFFER with IP configuration, DHCPREQUEST, and DHCPACK."),
    (5, 4, "DHCPv4 message exchange sequence showing DHCPDISCOVER, DHCPOFFER with IP details, DHCPREQUEST, and DHCPACK."),
    (6, 5, "DHCPv4 lease renewal process showing client DHCPREQUEST unicast and server DHCPACK acknowledgment."),
    (9, 4, "Network topology with router R1 as DHCPv4 server, switches S1/S2, PCs, and DNS server across two subnets."),
    (10, 4, "Network topology with R1 as DHCPv4 server connected to two LAN segments with switches, PCs, and DNS server."),
    (10, 5, "Router R1 CLI showing DHCP pool configuration with excluded addresses, network, default-router, dns-server, and domain-name."),
    (11, 4, "Network topology with R1 as DHCPv4 server for DHCP verification context."),
    (11, 5, "Router R1 CLI showing show running-config section dhcp output verifying the DHCP pool configuration."),
    (12, 4, "Network topology with R1 as DHCPv4 server for binding verification context."),
    (12, 6, "Router R1 CLI showing show ip dhcp binding output with abbreviated lease information."),
    (12, 8, "Router R1 CLI showing show ip dhcp binding with full details including lease expiration, type, state, and interface."),
    (13, 4, "Network topology with R1 as DHCPv4 server for server statistics context."),
    (13, 6, "Router R1 CLI showing show ip dhcp server statistics with message counts for DISCOVER, OFFER, REQUEST, and ACK."),
    (14, 4, "Network topology with R1 as DHCPv4 server for client verification context."),
    (14, 6, "Windows CLI showing ipconfig /all output with DHCP-assigned IP address, subnet mask, gateway, and DNS server information."),
    (15, 4, "Network topology showing DHCP relay scenario where R1 cannot forward broadcasts between different subnets to a remote DHCP server."),
    (15, 6, "Router R1 CLI showing ip helper-address configuration to relay DHCP broadcasts to a remote DHCP server."),
    (16, 4, "Network topology showing DHCP relay with R1 configured with ip helper-address pointing to DHCP server on remote subnet."),
    (17, 4, "Network topology showing SOHO router as DHCPv4 client connected through cable/DSL modem to ISP DHCPv4 server."),
    (17, 5, "Router R1 CLI showing ip helper-address 192.168.11.6 configuration for DHCP relay on interface G0/0/0."),
    (18, 4, "Network topology showing SOHO router as DHCPv4 client connected through cable/DSL modem cloud to ISP router."),
    (18, 5, "SOHO router CLI showing interface G0/0/1 configured with ip address dhcp and receiving DHCP-assigned address."),
])

# ============================================================
# Module 8 - SLAAC and DHCPv6 - Lecture 1
# ============================================================
add_alts("Lecture 1 IPv6 Global Unicast Address Assignment", [
    (3, 4, "IPv6 link-local address format diagram showing 10-bit prefix (FE80::/10), remaining 54 bits, and 64-bit Interface ID."),
    (3, 5, "IPv6 link-local communication diagram showing two hosts exchanging packets with FE80 source and destination addresses through a router."),
    (4, 4, "Windows IPv6 Properties dialog box showing manual configuration of IPv6 address, prefix length, gateway, and DNS servers."),
    (4, 5, "IPv6 link-local communication diagram showing hosts with FE80 addresses communicating through a switch and router."),
    (6, 4, "IPv6 Router Advertisement message structure showing prefix, prefix length, and flag fields for SLAAC configuration."),
    (7, 4, "IPv6 SLAAC process diagram showing Router Solicitation and Router Advertisement exchange between host and router."),
    (9, 4, "IPv6 address autoconfiguration diagram showing host generating its address using SLAAC with router prefix information."),
    (10, 4, "IPv6 SLAAC with EUI-64 process showing MAC address conversion to 64-bit Interface ID by inserting FFFE."),
    (10, 5, "IPv6 DAD (Duplicate Address Detection) process showing host sending Neighbor Solicitation to verify address uniqueness."),
    (11, 4, "IPv6 Router Advertisement with flags diagram showing O and M flag combinations for SLAAC, stateless, and stateful DHCPv6."),
    (11, 6, "Router CLI showing ipv6 nd configuration commands for setting Router Advertisement flags."),
    (12, 4, "IPv6 stateless DHCPv6 process showing host obtaining prefix from SLAAC and additional info from DHCPv6 server."),
    (12, 6, "Router CLI showing IPv6 DHCP configuration for stateless DHCPv6 server setup."),
    (13, 4, "IPv6 stateful DHCPv6 process showing host obtaining full address configuration from DHCPv6 server."),
    (14, 4, "IPv6 stateful DHCPv6 message exchange sequence between client and server."),
    (14, 6, "Router CLI showing IPv6 stateful DHCPv6 server configuration commands."),
    (15, 4, "IPv6 address assignment methods comparison table: SLAAC only, stateless DHCPv6, and stateful DHCPv6."),
    (17, 4, "Network topology showing IPv6 SLAAC and DHCPv6 deployment scenario with multiple hosts and router."),
])

# ============================================================
# Module 8 - Lecture 2 DHCPv6
# ============================================================
add_alts("Lecture 2 DHCPv6", [
    (3, 4, "DHCPv6 operation overview diagram showing the relationship between SLAAC, stateless, and stateful DHCPv6 modes."),
    (5, 4, "DHCPv6 message exchange sequence diagram showing Solicit, Advertise, Request, and Reply between client and server."),
    (8, 4, "DHCPv6 stateless configuration diagram showing host getting prefix via SLAAC and DNS info via DHCPv6."),
    (9, 4, "DHCPv6 relay agent diagram showing how DHCPv6 messages are forwarded between client and remote DHCPv6 server."),
    (12, 4, "DHCPv6 troubleshooting flowchart for diagnosing IPv6 address assignment issues."),
])

# ============================================================
# Module 9 - FHRP - Lecture 3 HSRP Demo
# ============================================================
add_alts("Lecture 3 - HSRP Demo", [
    (2, 4, "HSRP network topology showing two routers sharing a virtual IP address as the default gateway for LAN hosts."),
])

# ============================================================
# Top Level files (already in previous script)
# ============================================================
add_alts("advance_topics", [
    (1, 4, "Line graph comparing packet forwarding speeds between CPU and switch chip from 1990 to 2020."),
    (2, 4, "System architecture showing data synchronization between clustered database nodes with control and data plane."),
    (5, 5, "Hardware architecture stack showing compilers: C/C++ for CPU, Matlab for DSP, OpenCL for GPU, TensorFlow for TPU, P4 for FPGA."),
    (7, 5, "Comparison table of network measurement parameters including threshold and switching throughput."),
    (11, 3, "Exponential growth graph showing CPU performance increase over time with green highlighted region."),
    (12, 3, "Exponential growth graph displaying performance metrics with green acceleration phase."),
    (13, 3, "Graph showing gap between processor speed and network port speed from 2012 to 2022."),
    (15, 3, "Three NIC architectures: Traditional NIC, Offload NIC, and SmartNIC with data flow paths."),
    (16, 3, "Three network processing architectures with packet buffer, execution layer, and data plane."),
    (17, 4, "Three packet processing architectures showing data flow through buffer, execution, and data plane layers."),
    (21, 4, "Scatter plot showing anomaly detection with normal regions N1, N2 and outlier points o1, o2."),
    (24, 4, "Neural network with input layer X1-X41, hidden layers, and output layer for classification."),
    (25, 2, "System architecture with data plane, data stores, and interconnected database nodes."),
])

add_alts("Network Security", [
    (1, 3, "Computer icon with arrow toward firewall wall and orange arrows pointing to globe representing internet."),
    (9, 3, "Network topology with client-server architecture, firewalls, security appliances, and interconnected devices."),
    (10, 2, "Protocol numbers reference table listing IP, Ethernet, DCEnet, XNS, AppleTalk, IPX, and SAP protocols."),
    (13, 3, "ACL syntax example showing deny and permit rules with IP addresses and subnet masks."),
    (16, 3, "Network flow diagram with multiple access lists showing color-coded permit and deny decisions."),
    (17, 3, "Guidelines table for implementing ACLs including security policies and error handling."),
    (20, 1, "Secure traffic versus attacking traffic illustration with protected green connections through firewall."),
    (21, 0, "Dynamic packet filter diagram showing client-server UDP communication with filter matching logic."),
    (22, 0, "Stateful packet filtering with DMZ architecture and state table tracking addresses, ports, and flags."),
    (25, 2, "Zero-day exploit attack flow through VPN and firewall to internal servers."),
    (26, 1, "DDoS attack diagram showing attacker launching from compromised nodes to management console and servers."),
    (27, 1, "Numbered DDoS attack progression with attacker, attack nodes, switch, and target."),
    (28, 1, "DDoS attack simulation with attacker, cloud, numbered attack sources, sensor, and target."),
    (30, 1, "Advantages and disadvantages comparison table for firewall technologies."),
    (35, 2, "Trusted network with computers on left side of firewall, untrusted internet on right."),
    (36, 1, "Data center architecture with internet connection through border router to load balancers and servers."),
    (36, 2, "Server rack in data center showing networked servers and storage devices in blue lighting."),
    (37, 1, "Network topology with internet, border routers, load balancers, and multi-tiered server cluster."),
    (37, 2, "Network architecture with router, load balancers, and tiered web, application, and database servers."),
])

add_alts("wlan", [
    (5, 2, "Professional man looking through a modern office window with geometric lines in background."),
    (5, 3, "Large cellular tower with multiple transmission antennas and dishes against clear sky."),
    (6, 2, "Tall wireless communications tower with multiple antennas against blue sky."),
    (8, 2, "Electromagnetic spectrum diagram from radio waves to gamma rays with wireless device examples."),
    (12, 2, "External WiFi USB adapter with antenna connected to laptop for wireless connectivity."),
    (14, 2, "Two wireless router models showing typical access point designs for home or office."),
    (15, 2, "WLAN topology with core switch, distribution switches, and autonomous access points with clients."),
    (15, 3, "Controller-based WLAN architecture with WLC connected to controller-based AP and clients."),
    (16, 2, "Desktop WiFi antenna on stand showing external antenna design for wireless reception."),
    (16, 4, "Outdoor wireless access point with three antenna elements mounted on pole."),
    (19, 2, "Two laptops connected wirelessly with wavy signal line representing communication link."),
    (19, 3, "WLAN distribution system architecture with AP connecting wired and wireless clients."),
    (19, 4, "WLAN topology with laptop and smartphone connected wirelessly to AP with Internet cloud."),
    (20, 2, "IEEE 802.11 MAC frame format showing header, payload, and FCS with detailed field breakdown."),
    (21, 2, "Two WLAN BSS configurations with laptop connecting to AP showing BSSID and SSID identifiers."),
    (23, 2, "WLAN client-AP communication showing discover, authenticate, and associate process flows."),
    (25, 2, "AP beacon transmission diagram with wireless client receiving SSID and security settings."),
    (25, 4, "Probe request and response exchange between client and AP for SSID discovery."),
    (28, 2, "WiFi 2.4 GHz channel diagram showing 11 overlapping channels with 22 MHz bandwidth."),
    (29, 2, "802.11a 5 GHz frequency band showing 8 non-overlapping channels from 5150 to 5850 MHz."),
    (30, 2, "WiFi coverage pattern showing signal strength distribution in horizontal and vertical planes."),
])

# Now process each entry from the JSON
total_applied = 0
total_files = 0
skipped = 0

for entry in entries:
    pptx_path = entry["pptx_path"]
    fixed_path = entry["fixed_path"]
    original_name = entry["original_name"]
    images = entry["images"]

    if not images:
        continue

    # Build alt_texts list for this file
    alt_texts = []
    for img in images:
        slide = img["slide"]
        shape_idx = img["shape_idx"]
        slide_text = img.get("slide_text", "")

        # Try to find alt text in our lookup by various key strategies
        found = False
        # Strategy 1: match by normalized pptx_path
        key = make_key(pptx_path, slide, shape_idx)
        if key in ALT_TEXTS:
            alt_texts.append({"slide": slide, "shape_idx": shape_idx, "alt_text": ALT_TEXTS[key]})
            found = True
            continue

        # Strategy 2: match by original_name stem
        stem = os.path.splitext(original_name)[0]
        key2 = make_key(stem, slide, shape_idx)
        if key2 in ALT_TEXTS:
            alt_texts.append({"slide": slide, "shape_idx": shape_idx, "alt_text": ALT_TEXTS[key2]})
            found = True
            continue

        # Strategy 3: match by various name patterns
        for name_try in [stem, stem.replace("_fixed", ""), original_name]:
            key3 = make_key(name_try, slide, shape_idx)
            if key3 in ALT_TEXTS:
                alt_texts.append({"slide": slide, "shape_idx": shape_idx, "alt_text": ALT_TEXTS[key3]})
                found = True
                break
        if found:
            continue

        # Strategy 4: Generate from slide context text
        # Create a concise alt text from the slide text context
        alt = generate_alt_from_context(slide_text, img.get("image_path", ""))
        alt_texts.append({"slide": slide, "shape_idx": shape_idx, "alt_text": alt})

    if not alt_texts:
        continue

    # Find the source file
    source = fixed_path if os.path.exists(fixed_path) else pptx_path
    if not os.path.exists(source):
        print(f"SKIP: File not found: {os.path.basename(source)}")
        skipped += 1
        continue

    result = apply_pptx_alt_texts(source, fixed_path, alt_texts)
    size = os.path.getsize(fixed_path) if os.path.exists(fixed_path) else 0
    applied = result['applied']
    total = result['total']
    total_applied += applied
    total_files += 1
    print(f"{os.path.basename(fixed_path)}: applied {applied}/{total} alt texts ({size:,} bytes)")

print(f"\nDone! Applied alt texts to {total_files} files, {total_applied} total images. Skipped {skipped}.")
