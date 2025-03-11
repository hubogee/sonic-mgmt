import pytest
from ipaddress import ip_address, IPv4Address, IPv6Address

#from tests.snappi_tests.dataplane.files.helpers import get_duthost_vlan_details, 
from tests.common.snappi_tests.snappi_test_params import SnappiTestParams
from snappi_tests.reboot.files.reboot_helper import get_macs
from tests.common.snappi_tests.snappi_fixtures import snappi_api_serv_ip, snappi_api_serv_port, \
     snappi_api,  get_snappi_ports, get_snappi_ports_single_dut, get_snappi_ports_multi_dut   # noqa F401

from tests.common.snappi_tests.common_helpers import get_addrs_in_subnet

@pytest.fixture(scope="module")
def setup_snappi_port_configs(duthosts, get_snappi_ports):
    """
    Adding IP addresses and IP gateway addresses from the minigraph vlan interface details to snappi ports 
    
    Example:
        {
            'ipAddress': '192.168.1.9',
            'ipGateway': '192.168.1.2',
            'prefix': 24,
            'subnet': '192.168.1.0/24',
            'src_mac_address': 'aa:00:00:00:00:05',
            'router_mac_address': '9c:69:ed:6f:9f:a0',
            'speed': '800000',
            'snappi_speed_type': 'speed_800_gbps',
            'connected_to_dut_port': 'Ethernet16',
            'port_name': '10.36.84.31/2',
            'duthost': <MultiAsicSonicHost sonic-s6100-dut2>,
            'api_server_ip': '10.36.84.33',
            'asic_type': 'broadcom',
            'asic_value': None
        }
    """
    common_vars = SnappiTestParams()
    common_vars.snappi_port_configs = {}
    duthost_vlan_interface, subnet_tracker, all_vlan_gateway_ip = get_duthost_vlan_details(duthosts) 
    mac_address_generator = get_macs("AA0000000000", count=len(get_snappi_ports))
    ip_addresses = get_addrs_in_subnet(subnet_tracker[0], number_of_ip=len(get_snappi_ports), exclude_ips=all_vlan_gateway_ip)
    port_list = []
    
    for index,port in enumerate(get_snappi_ports):
        speed = port['speed']
        src_mac_address = mac_address_generator[index]
        
        # The src port's gateway mac is the router_mac for ALL VLANs
        router_mac_address = port['duthost'].facts['router_mac']
    
        if port['duthost'].hostname not in common_vars.snappi_port_configs:
           common_vars.snappi_port_configs[port['duthost'].hostname] = {}

        port_name = port['location']
        hostname = port['duthost'].hostname
        port_list.append({'ipAddress':  ip_addresses[index], 
                          'ipGateway': duthost_vlan_interface[hostname]['vlan_ip'], 
                          'prefix': duthost_vlan_interface[hostname]['ip_prefix'],
                          'subnet': duthost_vlan_interface[hostname]['subnet'], 
                          'src_mac_address': src_mac_address,
                          'router_mac_address': router_mac_address,
                          'speed': speed,
                          'snappi_speed_type': port['snappi_speed_type'],
                          'connected_to_dut_port': port['peer_port'],
                          'port_name': port['location'],
                          'duthost': port['duthost'],
                          'api_server_ip': port['api_server_ip'],
                          'asic_type': port['asic_type'],
                          'asic_value': port['asic_value']
                          }) 

    return port_list

def get_duthost_vlan_details(duthosts):
    """
    Loop through each duthosts to get its vlan details
    
    Usage:
        duthost_vlan_interface, subnet_tracker, all_vlan_gateway_ip = get_duthost_vlan_details(duthosts)
        
    Return:
       - duthost_vlan_interface: A dict object containing individual duthost as keys with all the dut's vlan details
       - subnet_tracker:         A list of subnets for calling ip_address_generator() to generate source ip addresses in the subnet
       - all_vlan_gateway_ip:    A list of all the vlan IP addresses for ip_address_generator() to exclude
                                 when providing the ip addresses

       duthost_vlan_interface, subnet_tracker, all_vlan_gateway_ip
    """
    minigraph = {}
    duthost_vlan_interface = {}
    
    # subnet_tracker is for ip address generator to know how many ip addresses to provide
    subnet_tracker = []
    
    # Keep track of all gateway IP addresses to exclude from generating src ip addresses
    all_vlan_gateway_ip = []
 
    for dut in duthosts:
        duthost_vlan_interface[dut.hostname] = {}
        duthost_minigraph_vlan_interface = dut.minigraph_facts(host=dut.hostname)['ansible_facts']['minigraph_vlan_interfaces']
        
        vlan_id =   duthost_minigraph_vlan_interface[0]['attachto']
        vlan_ip =   duthost_minigraph_vlan_interface[0]['addr']
        ip_prefix = duthost_minigraph_vlan_interface[0]['prefixlen']
        subnet =    duthost_minigraph_vlan_interface[0]['subnet']
        
        duthost_vlan_interface[dut.hostname].update({'vlan_id': vlan_id, 'vlan_ip': vlan_ip, 'subnet': subnet, 'ip_prefix': ip_prefix})
                                                      
        if vlan_ip not in all_vlan_gateway_ip:
            all_vlan_gateway_ip.append(vlan_ip)

        # subnet_tracker is for ip address generator
        if subnet not in subnet_tracker:
            subnet_tracker.append(subnet)
    
    return (duthost_vlan_interface, subnet_tracker, all_vlan_gateway_ip)


def ip_address_generator(subnets, exclude_ip_addresses):                                                                                     
    """
    Instantiate an IP Address generator dict object for each subnet
    This function returns a dictionary object container subnets as keys.
    
    Usage:
       ip_generatorObj = ip_address_generator(subnets, exclude_ip_addresses)
       next(ip_generatorObj[subnet])
    """
    ip_generator = {}
    for each_subnet in subnets:
        if '.' in each_subnet:
            network = IPv4Network(each_subnet)
            
        if ':' in each_subnet:
            network = IPv6Network(each_subnet)
        
        # Create a IP address generator for each ip subnet    
        ip_generator[each_subnet] = (host for host in network.hosts() if str(host) not in exclude_ip_addresses)
        return ip_generator
    
    
class Generate_Mac_Address:
    def __init__(self, starting_mac_address):
        """
        starting_mac_address: The initial starting mac address
        """
        self.mac_address = starting_mac_address
        
    def increment_mac_address(self):
        """
        Increments a MAC address by 1.
        
        If the initial starting mac address is AA:00:00:00:00:01
        incrementMac: pars: ['AA', '00', '00', '00', '00', '01']  
        integer_mac: 186916976721921  
        incremented_int: 186916976721922  
        incremented_hex: aa0000000002  
        final: AA:00:00:00:00:02
        """
        parts = self.mac_address.split(":")
        integer_mac = int("".join(parts), 16)
        incremented_int = integer_mac + 1
        incremented_hex = hex(incremented_int)[2:].zfill(12)
        self.mac_address =  ":".join(incremented_hex[i:i+2] for i in range(0, 12, 2)).upper()
        return self.mac_address
    