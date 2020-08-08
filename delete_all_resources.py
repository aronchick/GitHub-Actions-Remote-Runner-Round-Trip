import os
import sys
import json
from datetime import datetime
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.resource import ResourceManagementClient

RUN_ID=sys.argv[1]
CENTRAL_US = "centralus"
SOURCE_GROUP_NAME='ci_sample_rg'

def print_item(group):
    """Print a ResourceGroup instance."""
    print("\tName: {}".format(group.name))
    print("\tId: {}".format(group.id))
    print("\tLocation: {}".format(group.location))
    print("\tTags: {}".format(group.tags))
    print_properties(group.properties)


def print_properties(props):
    """Print a ResourceGroup properties instance."""
    if props and props.provisioning_state:
        print("\tProperties:")
        print("\t\tProvisioning State: {}".format(props.provisioning_state))
    print("\n\n")

def resolve_resource_api(client, resource):
    """ This method retrieves the latest non-preview api version for
    the given resource (unless the preview version is the only available
    api version) """
    provider = client.providers.get(resource.id.split('/')[6])
    rt = next((t for t in provider.resource_types
               if t.resource_type == '/'.join(resource.type.split('/')[1:])), None)
    #print(rt)
    if rt and 'api_versions' in rt.__dict__:
        #api_version = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        #return npv[0] if npv else rt[0].api_versions[0]
        api_version = [v for v in rt.__dict__['api_versions'] if 'preview' not in v.lower()]
        return api_version[0] if api_version else rt.__dict__['api_versions'][0]

resource_client = get_client_from_cli_profile(ResourceManagementClient)

all_resources = []
for i in resource_client.resources.list(filter=f"tagName eq 'run_id' and tagValue eq '{RUN_ID}'"): 
    all_resources.append({"id": i.id, "resource": i})

print(f"Total items to delete: {len(all_resources)}")

count = 0

while count < 5:
    temp_resource_holder = None
    for this_resource in all_resources:
        print(f"Deleting type: {this_resource['resource'].type}... ", end="")
        id = this_resource['id']
        temp_resource_holder = this_resource
        try:
            poller = resource_client.resources.delete_by_id(resource_id=this_resource['id'], api_version=resolve_resource_api(resource_client, this_resource['resource']))
            rg_delete_result = poller.result()
        except:
            pass
        print(f"Done.")
    r = list(resource_client.resources.list(filter=f"tagName eq 'run_id' and tagValue eq '{RUN_ID}'"))
    if len(r) == 0:
        break

    count = count + 1

print(f"Deleted. Remaining items with 'run_id' == {RUN_ID}: " + str(len(list(resource_client.resources.list(filter=f"tagName eq 'run_id' and tagValue eq '{RUN_ID}'")))))