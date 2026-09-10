#!/usr/bin/env python3

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
checks if there are any vms on a host that don't have Zerto DRaaS tag

The missing Zerto tag is a critical issue because it highlights that a
new system lacks DRaaS replication protection. To ensure compliance,
every virtual machine must be assigned a Zerto tag identified by the
'Zerto - Protection Automation' category.
"""

__cmd__ = 'zertotag'

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from pyVmomi import vim
from monplugin import Check, Status
from .. import CheckVsphereException
from ..tools import cli, service_instance
from ..tools.helper import find_entity_views, isbanned, isallowed, CheckArgument

def run():
    parser = cli.Parser()
    # parser.add_optional_arguments(cli.Argument.DATACENTER_NAME)
    parser.add_optional_arguments(cli.Argument.VIHOST)
    parser.add_optional_arguments(CheckArgument.ALLOWED('regex match against vm name'))
    parser.add_optional_arguments(CheckArgument.BANNED('regex match against vm name'))
    args = parser.get_args()
    si = service_instance.connect(args)

    check = Check()

    if args.vihost:
        host = find_entity_views(
            si,
            vim.HostSystem,
            begin_entity=si.content.rootFolder,
            sieve={'name': args.vihost},
        )
        if not host:
            raise CheckVsphereException(f"host {args.vihost} not found")
        parentView = host[0]['obj'].obj
    else:
        parentView = si.content.rootFolder

    #vm_view = si.content.viewManager.CreateContainerView(parentView, [vim.VirtualMachine], True)
    vms = find_entity_views(
        si,
        vim.VirtualMachine,
        begin_entity=parentView,
        properties=['name', 'config.hardware.device', 'config.template', 'customValue']
    )

    check.add_message(
        Status.OK,
        "no VMs missing Zerto tags"
    )

    # 1. API REST authentication
    vcenter_host = args.host
    vcenter_user = args.user
    vcenter_password = args.password

    session = requests.Session()
    session.verify = False # Ignore SSL cert

    # Request token REST
    auth_url = f"https://{vcenter_host}/rest/com/vmware/cis/session"
    auth_resp = session.post(auth_url, auth=(vcenter_user, vcenter_password))

    if auth_resp.status_code != 200:
        check.add_message(Status.UNKNOWN, f"Unable to authenticate with the REST API: {auth_resp.text}")
        (code, message) = check.check_messages()
        check.exit(code=code, message=message)

    # Save token for next requests
    session_token = auth_resp.json()['value']
    session.headers.update({'vmware-api-session-id': session_token})

    # Helper function to get tag categories and names given a VM ID
    def get_vm_tags(vm_id):
        # 1. Find the tag IDs associated with the VM
        assoc_url = f"https://{vcenter_host}/rest/com/vmware/cis/tagging/tag-association?~action=list-attached-tags"
        payload = {
            "object_id": {
                "id": vm_id,
                "type": "VirtualMachine"
            }
        }
        resp = session.post(assoc_url, json=payload)

        if resp.status_code != 200:
            return f"Error {resp.status_code}: {resp.text}"

        tag_ids = resp.json().get('value', [])
        if not tag_ids:
            return "No Tags"

        # 2. Resolve tag IDs to retrieve Tag Name and Category ID
        tag_details = []
        for tag_id in tag_ids:
            tag_url = f"https://{vcenter_host}/rest/com/vmware/cis/tagging/tag/id:{tag_id}"
            tag_resp = session.get(tag_url)

            if tag_resp.status_code == 200:
                tag_data = tag_resp.json().get('value', {})
                tag_name = tag_data.get('name', 'Unknown')
                category_id = tag_data.get('category_id')

                # 3. Resolve Category ID to retrieve Category Name
                category_name = "UnknownCategory"
                if category_id:
                    cat_url = f"https://{vcenter_host}/rest/com/vmware/cis/tagging/category/id:{category_id}"
                    cat_resp = session.get(cat_url)
                    if cat_resp.status_code == 200:
                        category_name = cat_resp.json().get('value', {}).get('name', 'Unknown')

                # Combine category and tag in the desired format
                tag_details.append(f"[{category_name}] {tag_name}")
            else:
                tag_details.append(f"TagID:{tag_id}")

        return ", ".join(tag_details)

    for vm in vms:
        match = 0

        if isbanned(args, vm['props']['name']):
            continue
        if not isallowed(args, vm['props']['name']):
            continue

        if vm['props']['runtime.powerState'] != 'poweredOn':
            # it's powered off, api is unreliable
            # config.hardware or config.template might be missing
            continue

        if vm['props']['config.template']:
            # This vm is a template, ignore it
            continue

        # Check if the VM has a tag where the category contains "Zerto"
        has_zerto_category = False

        vm_id = vm['obj'].obj._moId
        tags_str = get_vm_tags(vm_id)
        for item in tags_str.split(', '):
            if '[' in item and ']' in item:
                # Extract the text between '[' and ']'
                category_name = item[item.find('[')+1 : item.find(']')]

                # Check if "Zerto" is part of the category name
                if 'Zerto' in category_name:
                    has_zerto_category = True
                    break

        # Skip this VM if it has Zerto-related tag
        if has_zerto_category:
            continue

        #print(f"VM: {vm['props']['name']} | Tag: {tags_str}")
        match += 1
        if match > 0:
            check.add_message(
                Status.CRITICAL,
                f'{vm["props"]["name"]} is missing Zerto tag'
            )

    (code, message) = check.check_messages(separator=' - ')
    check.exit(
        code=code,
        message=message
    )


if __name__ == "__main__":
    run()
