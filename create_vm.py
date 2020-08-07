# Import the needed management objects from the libraries. The azure.common library
# is installed automatically with the other libraries.
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
import uuid
import secrets
import string
import sys
from pathlib import Path

alphabet = string.ascii_letters + string.digits + string.punctuation
password = "".join(
    secrets.choice(alphabet) for i in range(60)
)  # for a 20-character password

print(f"Provisioning a virtual machine...some operations might take a minute or two.")

# Step 1: Provision a resource group

# Obtain the management object for resources, using the credentials from the CLI login.
resource_client = get_client_from_cli_profile(ResourceManagementClient)

# Constants we need in multiple places: the resource group name and the region
# in which we provision resources. You can change these values however you want.
RESOURCE_GROUP_NAME = "ci_sample_rg"
LOCATION = "centralus"
unique_string = uuid.uuid4().hex
ci_tags = {"type": "ci_resources", "run_id": unique_string}
rg_result = resource_client.resource_groups.get(resource_group_name=RESOURCE_GROUP_NAME)


print(f"Got {rg_result.name} in the {rg_result.location} region")

# For details on the previous code, see Example: Provision a resource group
# at https://docs.microsoft.com/azure/developer/python/azure-sdk-example-resource-group

# Step 2: provision a virtual network

# A virtual machine requires a network interface client (NIC). A NIC requires
# a virtual network and subnet along with an IP address. Therefore we must provision
# these downstream components first, then provision the NIC, after which we
# can provision the VM.

# Network and IP address names
VNET_NAME = f"python-example-vnet-{unique_string}"
SUBNET_NAME = f"python-example-subnet-{unique_string}"
IP_NAME = f"python-example-ip-{unique_string}"
IP_CONFIG_NAME = f"python-example-ip-config-{unique_string}"
NIC_NAME = f"python-example-nic-{unique_string}"
NETWORK_SECURITY_GROUP_NAME = f"python-example-nsg-{unique_string}"

# Obtain the management object for networks
network_client = get_client_from_cli_profile(NetworkManagementClient)

# Provision the virtual network and wait for completion
poller = network_client.virtual_networks.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    VNET_NAME,
    {
        "location": LOCATION,
        "address_space": {"address_prefixes": ["10.0.0.0/16"]},
        "tags": ci_tags,
    },
)

vnet_result = poller.result()

print(
    f"Provisioned virtual network {vnet_result.name} with address prefixes {vnet_result.address_space.address_prefixes}"
)

# Step 3: Provision the subnet and wait for completion
poller = network_client.subnets.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    VNET_NAME,
    SUBNET_NAME,
    {"address_prefix": "10.0.0.0/24", "tags": ci_tags},
)
subnet_result = poller.result()

print(
    f"Provisioned virtual subnet {subnet_result.name} with address prefix {subnet_result.address_prefix}"
)

# Step 4: Provision an IP address and wait for completion
poller = network_client.public_ip_addresses.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": {"name": "Standard"},
        "public_ip_allocation_method": "Static",
        "public_ip_address_version": "IPV4",
        "tags": ci_tags,
    },
)

ip_address_result = poller.result()

print(
    f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}"
)

# Step 5: Provision the network interface client
poller = network_client.network_security_groups.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    NETWORK_SECURITY_GROUP_NAME,
    {
        "location": LOCATION,
        "properties": {
            "securityRules": [
                {
                    "name": "ssh_allow",
                    "properties": {
                        "protocol": "*",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "destinationPortRange": "22",
                        "sourcePortRange": "*",
                        "priority": 130,
                        "direction": "Inbound",
                    },
                }
            ]
        },
        "tags": ci_tags,
    },
)

nsg_result = poller.result()

print(f"Provisioned network security group {nsg_result.name}")

poller = network_client.network_interfaces.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    NIC_NAME,
    {
        "location": LOCATION,
        "ip_configurations": [
            {
                "name": IP_CONFIG_NAME,
                "subnet": {"id": subnet_result.id},
                "public_ip_address": {"id": ip_address_result.id},
            }
        ],
        "network_security_group": {"id": f"{nsg_result.id}"},
        "tags": ci_tags,
    },
)

nic_result = poller.result()

print(f"Provisioned network interface client {nic_result.name}")


# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = get_client_from_cli_profile(ComputeManagementClient)

VM_NAME = f"CI-VM-{unique_string}"
USERNAME = f"{uuid.uuid4().hex}"
PASSWORD = f"{password}"

print(
    f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes."
)

# Provision the VM specifying only minimal arguments, which defaults to an Ubuntu 18.04 VM
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

ssh_pub_key = Path("/tmp/sshkey.pub").read_text().rstrip()
print(f"SSH Key: {ssh_pub_key}")
pub_path = f"/home/{USERNAME}/.ssh/authorized_keys"
print(f"Pub_path: {pub_path}")

poller = compute_client.virtual_machines.begin_create_or_update(
    RESOURCE_GROUP_NAME,
    VM_NAME,
    {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": "Canonical",
                "offer": "UbuntuServer",
                "sku": "16.04.0-LTS",
                "version": "latest"
            }
        },
        "hardware_profile": {"vm_size": "Standard_DS1_v2"},
        "osProfile": {
            "adminUsername": f"{USERNAME}",
            "computerName": f"{VM_NAME}",
            "linuxConfiguration": {
                "ssh": {
                    "publicKeys": [
                        {
                            "path": f"{pub_path}",
                            "keyData": f"{ssh_pub_key}",
                        }
                    ]
                },
                "disablePasswordAuthentication": True,
            },
        },
        "network_profile": {"network_interfaces": [{"id": nic_result.id,}]},
        "tags": ci_tags,
    },
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")
print(f"::set-output name=VM_NAME::{VM_NAME}")
print(f"::set-output name=USERNAME::{USERNAME}")
print(f"::set-output name=IP_ADDRESS::{ip_address_result.ip_address}")

print(f"SSH Command = \nssh -i /tmp/sshkey -o StrictHostKeyChecking=no {USERNAME}@{ip_address_result.ip_address} 'ls -lAR'")
# scp -i /tmp/sshkey -o StrictHostKeyChecking=no do_work_on_runner.py e5ecb2d144bf4f7fb77ad87a3e5090e5@52.154.210.237:do_work_on_remote_runner.py