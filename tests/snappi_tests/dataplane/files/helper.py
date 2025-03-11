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
            'peer_port': 'Ethernet16',
            'location': '10.36.84.31/2',
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
                          'ipGateway': duthost_vlan_interface[hostname]['vlan_ip'] , 
                          'prefix': duthost_vlan_interface[hostname]['ip_prefix'],
                          'subnet': duthost_vlan_interface[hostname]['subnet'], 
                          'src_mac_address': src_mac_address,
                          'router_mac_address': router_mac_address,
                          'speed': speed,
                          'snappi_speed_type': port['snappi_speed_type'],
                          'peer_port': port['peer_port'],
                          'location': port['location'],
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
 
    duthost_vlan_interface = {dut.hostname: {'vlan_id': '', 'vlan_ip': '', 'subnet': '', 'ip_prefix': ''} for dut in duthosts}
    
    for dut in duthosts:
        # NOTE! This only gets the first vlan interface
        duthost_minigraph_vlan_interface = dut.minigraph_facts(host=dut.hostname)['ansible_facts']['minigraph_vlan_interfaces'][0]

        duthost_vlan_interface[dut.hostname] = {'vlan_id':   duthost_minigraph_vlan_interface['attachto'], 
                                                'vlan_ip':   duthost_minigraph_vlan_interface['addr'], 
                                                'subnet':    duthost_minigraph_vlan_interface['subnet'], 
                                                'ip_prefix': duthost_minigraph_vlan_interface['prefixlen']}
                                                                      
        if duthost_minigraph_vlan_interface['addr'] not in all_vlan_gateway_ip:
            all_vlan_gateway_ip.append(duthost_minigraph_vlan_interface['addr'])

        # subnet_tracker is for ip address generator
        if duthost_minigraph_vlan_interface['subnet'] not in subnet_tracker:
            subnet_tracker.append(duthost_minigraph_vlan_interface['subnet'])
    
    return (duthost_vlan_interface, subnet_tracker, all_vlan_gateway_ip)


