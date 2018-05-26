# This example shows how itertools' product function can be used to easily
# expand the parameter space from an initial specification.

from itertools import product
from pprint import PrettyPrinter

printer = PrettyPrinter(indent=4)

# Dictionary containing desired values in an array
param_ranges = {
    'payloadSize': [1472, 1472/2],
    'dataRate': ['100Mbps'],
    'tcpVariant': ['TcpHybla', 'TcpHighSpeed', 'TcpHtcp', 'TcpVegas'],
    'phyRate': ['HtMcs7'],
    'simulationTime': [4],
    'pcap': ['false'],
    'runs': [10]
}

# This space will contain every combination specified in the ranges
param_space = [dict(zip(param_ranges, v)) for v in
               product(*param_ranges.values())]

print("Starting parameter space specification:")
printer.pprint(param_ranges)

print("Expanded parameter space:\n")
printer.pprint(param_space)
