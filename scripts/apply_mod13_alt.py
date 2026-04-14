"""
Apply alt text to Module 13 PPTX files (Static Routing lectures)
"""
import sys
sys.path.insert(0, 'c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/scripts')

from fix_office import apply_pptx_alt_texts

# Lecture 1 - Static Routing (39 images)
lecture1_alt_texts = [
    {"slide": 2, "shape_idx": 4, "alt_text": "Comparison table of Dynamic vs Static Routing showing configuration complexity, topology changes, scaling, security, resource usage, and predictability differences."},
    {"slide": 5, "shape_idx": 4, "alt_text": "Technical documentation showing static route configuration syntax and parameters."},
    {"slide": 6, "shape_idx": 4, "alt_text": "Technical documentation with detailed command explanations and configuration examples."},
    {"slide": 7, "shape_idx": 4, "alt_text": "Network diagram showing multiple routers with IP addresses, subnet masks, and routing paths labeled with bandwidth and interface information."},
    {"slide": 8, "shape_idx": 4, "alt_text": "Network diagram with PC, router, and server connections showing IP addresses and interface configurations."},
    {"slide": 9, "shape_idx": 4, "alt_text": "Network topology diagram with routers, IP addresses, and connection paths showing static routing configuration."},
    {"slide": 9, "shape_idx": 5, "alt_text": "Terminal output showing router CLI commands and gateway routing information with multiple route entries."},
    {"slide": 10, "shape_idx": 4, "alt_text": "Network diagram showing multi-level router hierarchy with IP addresses, interface labels, and routing paths between devices."},
    {"slide": 10, "shape_idx": 5, "alt_text": "Network diagram showing similar topology to slide 10 with updated routing configuration paths."},
    {"slide": 11, "shape_idx": 4, "alt_text": "Network diagram with routers connected at multiple levels showing IP addresses and interface connections."},
    {"slide": 11, "shape_idx": 5, "alt_text": "Network diagram showing routing topology with devices and connections labeled with interface information."},
    {"slide": 11, "shape_idx": 6, "alt_text": "Network topology showing routing between multiple connected devices and subnets."},
    {"slide": 12, "shape_idx": 4, "alt_text": "Network diagram showing router interconnections with IP addresses and interface labels."},
    {"slide": 12, "shape_idx": 5, "alt_text": "Network topology diagram with routers and connected systems showing routing paths."},
    {"slide": 13, "shape_idx": 4, "alt_text": "Network diagram showing multi-level device topology with IP addresses and interface connections."},
    {"slide": 13, "shape_idx": 5, "alt_text": "Network topology showing device connections and routing configuration."},
    {"slide": 14, "shape_idx": 4, "alt_text": "Network diagram showing router hierarchy with IP addresses and interface labels."},
    {"slide": 14, "shape_idx": 5, "alt_text": "Network topology diagram showing connected routers and subnets."},
    {"slide": 14, "shape_idx": 6, "alt_text": "Network diagram showing routing topology between multiple connected devices."},
    {"slide": 15, "shape_idx": 4, "alt_text": "Network diagram with routers and devices showing IP addresses and interface connections."},
    {"slide": 15, "shape_idx": 5, "alt_text": "Network topology showing multi-level device hierarchy and routing paths."},
    {"slide": 16, "shape_idx": 4, "alt_text": "Network diagram showing router connections with IP addresses and interface information."},
    {"slide": 16, "shape_idx": 5, "alt_text": "Router configuration commands showing multiple static routes with different IP addresses and interface mappings."},
    {"slide": 16, "shape_idx": 6, "alt_text": "Network topology showing device connections and routing configuration."},
    {"slide": 17, "shape_idx": 4, "alt_text": "Network diagram with routers and connected devices showing IP addresses and paths."},
    {"slide": 17, "shape_idx": 5, "alt_text": "Network topology diagram showing routing between multiple connected subnets and routers."},
    {"slide": 18, "shape_idx": 4, "alt_text": "Network diagram showing router hierarchy with IP addresses and interface labels."},
    {"slide": 18, "shape_idx": 5, "alt_text": "Network topology showing device connections and routing paths."},
    {"slide": 18, "shape_idx": 6, "alt_text": "Network diagram showing multi-level routing topology."},
    {"slide": 19, "shape_idx": 4, "alt_text": "Network diagram with routers and devices showing IP addresses and interface connections."},
    {"slide": 20, "shape_idx": 4, "alt_text": "Network diagram showing router hierarchy with IP addresses, interface information, and routing paths."},
    {"slide": 20, "shape_idx": 5, "alt_text": "Network topology showing multiple connected devices and routers with routing configuration."},
    {"slide": 23, "shape_idx": 4, "alt_text": "Network diagram showing router connections with IP addresses and interface labels."},
    {"slide": 24, "shape_idx": 4, "alt_text": "Network diagram showing device topology and routing configuration."},
    {"slide": 24, "shape_idx": 5, "alt_text": "Network topology diagram showing connected routers and subnets."},
    {"slide": 25, "shape_idx": 4, "alt_text": "Network diagram with routers showing IP addresses and routing paths."},
    {"slide": 25, "shape_idx": 5, "alt_text": "Network topology showing multi-level device connections and routing."},
    {"slide": 25, "shape_idx": 6, "alt_text": "Network diagram showing router hierarchy and connection topology."},
]

# Lecture 2 - Default Route (15 images)
lecture2_alt_texts = [
    {"slide": 3, "shape_idx": 4, "alt_text": "Network diagram showing default route configuration with routers, ISP gateway, and device connections."},
    {"slide": 4, "shape_idx": 4, "alt_text": "Network topology diagram showing multiple connected routers and devices with routing paths."},
    {"slide": 4, "shape_idx": 5, "alt_text": "Network diagram showing device connections through routers and ISP gateway."},
    {"slide": 5, "shape_idx": 4, "alt_text": "Terminal output showing router CLI commands for configuring default routes and gateway settings."},
    {"slide": 5, "shape_idx": 5, "alt_text": "Router configuration output displaying default route information and command syntax."},
    {"slide": 6, "shape_idx": 4, "alt_text": "Network diagram showing router hierarchy with default route configuration through ISP gateway."},
    {"slide": 7, "shape_idx": 4, "alt_text": "Network topology diagram showing connected routers and subnets with default routing paths."},
    {"slide": 7, "shape_idx": 5, "alt_text": "Network diagram showing device connections and default route configuration."},
    {"slide": 8, "shape_idx": 4, "alt_text": "Network diagram with routers connected through ISP showing default route setup."},
    {"slide": 8, "shape_idx": 5, "alt_text": "Terminal output showing router configuration commands for default routes and interface settings."},
    {"slide": 8, "shape_idx": 6, "alt_text": "Router CLI output displaying default route configuration information."},
    {"slide": 9, "shape_idx": 4, "alt_text": "Network diagram showing router topology with default route to ISP gateway."},
    {"slide": 9, "shape_idx": 5, "alt_text": "Network topology showing connected devices and default routing path configuration."},
    {"slide": 10, "shape_idx": 4, "alt_text": "Network diagram showing final default route topology with all connected devices and routers."},
    {"slide": 10, "shape_idx": 5, "alt_text": "Network topology diagram showing complete default routing setup."},
]

# Lecture 4 - Static Host Routes (14 images)
lecture4_alt_texts = [
    {"slide": 3, "shape_idx": 4, "alt_text": "Network diagram showing server, ISP gateway, and branch office connected with static host routes."},
    {"slide": 4, "shape_idx": 4, "alt_text": "Network topology diagram showing static host route configuration between connected devices."},
    {"slide": 4, "shape_idx": 5, "alt_text": "Network diagram showing device connections with static host route setup."},
    {"slide": 5, "shape_idx": 4, "alt_text": "Network diagram showing server, ISP, and branch connections with host routing configuration."},
    {"slide": 6, "shape_idx": 4, "alt_text": "Network diagram showing static host routes with server, ISP gateway, and branch office connections."},
    {"slide": 6, "shape_idx": 5, "alt_text": "Network topology showing host route configuration between multiple connected devices."},
    {"slide": 7, "shape_idx": 4, "alt_text": "Network diagram showing router connections with static host routes configured."},
    {"slide": 7, "shape_idx": 5, "alt_text": "Network topology diagram showing host routing paths between connected routers and servers."},
    {"slide": 7, "shape_idx": 6, "alt_text": "Network diagram showing complete static host route topology."},
    {"slide": 8, "shape_idx": 4, "alt_text": "Network diagram showing server, ISP, and branch connections with host routing configuration."},
    {"slide": 9, "shape_idx": 4, "alt_text": "Network topology showing static host routes between connected devices and routers."},
    {"slide": 9, "shape_idx": 5, "alt_text": "Network diagram showing host route configuration topology."},
    {"slide": 10, "shape_idx": 4, "alt_text": "Network diagram showing final static host route topology with server, ISP, and branch office."},
    {"slide": 10, "shape_idx": 5, "alt_text": "Network topology diagram showing complete host routing setup and connections."},
]

# Apply alt texts to each file
print("Applying alt text to Lecture 1 - Static Routing...")
apply_pptx_alt_texts(
    "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing/Lecture 1 - Static Routing_fixed.pptx",
    "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing/Lecture 1 - Static Routing_fixed.pptx",
    lecture1_alt_texts
)
print("✓ Lecture 1 completed")

print("\nApplying alt text to Lecture 2 - Default Route...")
apply_pptx_alt_texts(
    "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing/Lecture 2 - Default Route_fixed.pptx",
    "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing/Lecture 2 - Default Route_fixed.pptx",
    lecture2_alt_texts
)
print("✓ Lecture 2 completed")

print("\nApplying alt text to Lecture 4 - Static Host Routes...")
apply_pptx_alt_texts(
    "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing/Lecture 4 - Static Host Routes_fixed.pptx",
    "c:/Users/alima/OneDrive - University of South Carolina/Research/Working Directory/Blackboard_Accessibility_report/course_content/ITEC445-001-FALL-2025/Module 13 - Static Routing/Lecture 4 - Static Host Routes_fixed.pptx",
    lecture4_alt_texts
)
print("✓ Lecture 4 completed")

print("\n✓ All files processed successfully!")
