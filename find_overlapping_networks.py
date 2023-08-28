
import csv
import ipaddress
from io import StringIO

# Sample CSV data
csv_data = """Location,as,ip,prefix,siteid,postaladdress
Loc1,AS1,192.168.1.0,24,S1,123 Main St
Loc2,AS2,192.168.1.0,25,S2,456 Oak St
Loc3,AS3,10.0.0.0,8,S3,789 Elm St
Loc4,AS4,10.1.0.0,16,S4,101 Maple St
Loc5,AS5,172.16.0.0,16,S5,202 Birch St
"""

# Read CSV into a list of dictionaries
csv_reader = csv.DictReader(StringIO(csv_data))
networks = [row for row in csv_reader]

# Initialize output list
output = []

# Check for overlapping networks
for i, net1 in enumerate(networks):
    net1_cidr = ipaddress.ip_network(f"{net1['ip']}/{net1['prefix']}")
    is_supernet = False
    for j, net2 in enumerate(networks):
        if i == j:
            continue
        net2_cidr = ipaddress.ip_network(f"{net2['ip']}/{net2['prefix']}")
        if net1_cidr.supernet_of(net2_cidr):
            print(f"Overlap found: {net1['ip']}/{net1['prefix']} is a supernet of {net2['ip']}/{net2['prefix']}")
            is_supernet = True
    net1['is_supernet'] = is_supernet
    output.append(net1)

# Create new CSV with 'is_supernet' column
csv_output = StringIO()
csv_writer = csv.DictWriter(csv_output, fieldnames=list(networks[0].keys()) + ['is_supernet'])
csv_writer.writeheader()
csv_writer.writerows(output)

# Print the new CSV
csv_output.seek(0)
print(csv_output.read())
