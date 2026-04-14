# PPTX Alt Text Application Instructions

This document explains how to apply the pre-generated alt texts to the PPTX files.

## Files to Process

1. **Module 5 - Spanning Tree Protocol**
   - File: `Lecture 2 - Building the Spanning Tree_fixed.pptx`
   - Location: `course_content/ITEC445-001-FALL-2025/Module 5 - Spanning Tree Protocol/`
   - Images: 11 diagrams of network topology, STP port states, and bridge configuration

2. **Module 7 - DHCPv4**
   - File: `Introduction to DHCP_fixed.pptx`
   - Location: `course_content/ITEC445-001-FALL-2025/Module 7 - DHCPv4/`
   - Images: 22 network topology diagrams showing DHCPv4 server configurations

3. **Module 8 - SLAAC and DHCPv6 (Lecture 1)**
   - File: `Lecture 1 IPv6 Global Unicast Address Assignment_fixed.pptx`
   - Location: `course_content/ITEC445-001-FALL-2025/Module 8 - SLAAC and DHCPv6/`
   - Images: 18 IPv6 network address assignment diagrams

4. **Module 8 - SLAAC and DHCPv6 (Lecture 2)**
   - File: `Lecture 2 DHCPv6_fixed.pptx`
   - Location: `course_content/ITEC445-001-FALL-2025/Module 8 - SLAAC and DHCPv6/`
   - Images: 5 DHCPv6 assignment process diagrams

5. **Module 9 - FHRP**
   - File: `Lecture 3 - HSRP Demo_fixed.pptx`
   - Location: `course_content/ITEC445-001-FALL-2025/Module 9 - First Hop Redundancy Protocol (FHRP)/`
   - Images: 1 HSRP network topology diagram

## How to Apply Alt Texts

### Method 1: Run the Automated Script (Recommended)

```bash
cd scripts
python apply_all_pptx_alt_texts.py
```

This will:
- Process all 5 PPTX files
- Apply pre-generated alt texts to all images
- Save the updated files in place
- Display a summary of results

### Method 2: Process Individual Files

If you need to process individual files:

```python
from fix_office import apply_pptx_alt_texts

# Example: File 1
alt_texts_file1 = [
    {'slide': 3, 'shape_idx': 3, 'alt_text': 'Network topology showing root bridge selection...'},
    {'slide': 4, 'shape_idx': 3, 'alt_text': 'Network diagram illustrating port costs...'},
    # ... more entries
]

result = apply_pptx_alt_texts(
    input_path="Module 5 - Spanning Tree Protocol/Lecture 2 - Building the Spanning Tree_fixed.pptx",
    output_path="Module 5 - Spanning Tree Protocol/Lecture 2 - Building the Spanning Tree_fixed.pptx",
    alt_texts=alt_texts_file1
)
print(result)
```

## Alt Text Details

### File 1: Lecture 2 - Building the Spanning Tree (11 images)

| Slide | Shape | Description |
|-------|-------|-------------|
| 4 | 3 | Network topology showing root bridge selection with bridge priorities and MAC addresses |
| 5 | 3 | Network diagram illustrating port costs with root bridge at center |
| 6 | 3 | Table comparing link speeds to STP and RSTP costs |
| 7 | 3 | Spanning tree topology with root bridge and designated ports labeled |
| 8 | 3 | Network diagram indicating blocked alternate port with X mark |
| 11 | 3 | Four-switch network topology with bridge IDs |
| 12 | 3 | Simplified spanning tree showing root and alternate ports |
| 13 | 3 | Port cost diagram for root bridge |
| 14 | 3 | Flowchart showing STP port state transitions |
| 14 | 4 | Flowchart showing STP port state transitions |

### File 2: Introduction to DHCP (22 images)

Network topology diagrams showing:
- DHCPv4 server in center with two subnets (192.168.10.0/24 and 192.168.11.0/24)
- Multiple router connections
- DNS server configuration
- Computer endpoints

Slides: 10-21 (multiple shape indices per slide)

### File 3: Lecture 1 IPv6 Global Unicast Address Assignment (18 images)

IPv6 network diagrams showing:
- Router with address 2001:db8:acad:1::/64
- Connected computer with fe80::1 IPv6 address
- Various configuration states

Slides: 10-16 (multiple shape indices per slide)

### File 4: Lecture 2 DHCPv6 (5 images)

DHCPv6-specific diagrams:
- Dynamic GUA assignment decision tree
- DHCPv6 server network topology
- Stateless/stateful DHCP options
- IPv6 address assignment process

Slides: 4, 10, 13, 14

### File 5: Lecture 3 - HSRP Demo (1 image)

- HSRP network topology with redundant router configuration
- Virtual gateway and priority settings
- Multiple PC endpoints

Slide: 3, Shape: 4

## Verification

After applying alt texts, verify the changes by:

1. Opening each PPTX file in PowerPoint
2. For each image, right-click and select "Edit Alt Text"
3. Confirm the description has been populated
4. Check that descriptions are concise (1-2 sentences)

## Notes

- Alt texts are designed to be concise (1-2 sentences)
- Descriptions focus on the technical content and network topology
- All files are saved in place (not creating new copies)
- The script uses the `fix_office.apply_pptx_alt_texts()` function from the accessibility fixing module
