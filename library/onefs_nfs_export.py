#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible Module: onefs_nfs_export
Description: Configure NFS exports on Dell PowerScale/Isilon via OneFS API
Author: VCF Automation Framework
Version: 1.0.0
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.error import HTTPError

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0.0'
}

DOCUMENTATION = '''
---
module: onefs_nfs_export
short_description: Configure NFS exports on Dell PowerScale/Isilon via OneFS API
description:
    - This module configures NFS exports on Dell PowerScale/Isilon storage clusters using the OneFS API.
    - Can create, modify, and delete NFS exports.
    - Supports configuring export paths, client access, and export options.
options:
    base_uri:
        description:
            - Base URI of the OneFS API (e.g., https://powerscale-hostname:8080).
        required: true
        type: str
    username:
        description:
            - Username for OneFS API authentication.
        required: true
        type: str
    password:
        description:
            - Password for OneFS API authentication.
        required: true
        type: str
    export_name:
        description:
            - Name of the NFS export.
        required: true
        type: str
    export_path:
        description:
            - File system path for the export.
        required: true
        type: str
    clients:
        description:
            - List of client networks or hostnames allowed to access the export.
        required: true
        type: list
    read_only:
        description:
            - Whether the export is read-only.
        required: false
        type: bool
        default: false
    state:
        description:
            - Desired state of the export (present or absent).
        required: false
        type: str
        choices: ['present', 'absent']
        default: present
    validate_certs:
        description:
            - Whether to validate SSL certificates.
        required: false
        type: bool
        default: false
    timeout:
        description:
            - Timeout in seconds for API requests.
        required: false
        type: int
        default: 120
notes:
    - This module requires the OneFS API to be accessible on the PowerScale cluster.
    - Changes to NFS exports take effect immediately.
    - The module uses the OneFS Platform API (RESTful interface).
author:
    - VCF Automation Framework Team
'''

EXAMPLES = '''
- name: Create NFS export for VCF vSAN
  onefs_nfs_export:
    base_uri: "https://powerscale.example.com:8080"
    username: "root"
    password: "{{ vault_powerscale_password }}"
    export_name: "vcf-vsan"
    export_path: "/ifs/vcf/vsan"
    clients:
      - "192.168.1.0/24"
      - "192.168.2.0/24"
    read_only: false
    state: present
    validate_certs: false
  delegate_to: localhost

- name: Delete NFS export
  onefs_nfs_export:
    base_uri: "https://powerscale.example.com:8080"
    username: "root"
    password: "{{ vault_powerscale_password }}"
    export_name: "vcf-vsan"
    state: absent
  delegate_to: localhost
'''

RETURN = '''
changed:
    description: Whether the NFS export was changed.
    type: bool
    returned: always
export:
    description: Details of the NFS export configuration.
    type: dict
    returned: always
'''


class OneFSNFSExport:
    """Class to handle OneFS NFS export operations."""

    def __init__(self, module):
        """
        Initialize the OneFSNFSExport class.

        Args:
            module: AnsibleModule instance
        """
        self.module = module
        self.base_uri = module.params['base_uri']
        self.username = module.params['username']
        self.password = module.params['password']
        self.export_name = module.params['export_name']
        self.export_path = module.params['export_path']
        self.clients = module.params['clients']
        self.read_only = module.params['read_only']
        self.state = module.params['state']
        self.validate_certs = module.params['validate_certs']
        self.timeout = module.params['timeout']
        
        # Build API endpoints
        self.exports_uri = f"{self.base_uri}/platform/1/nfs/exports"
        self.export_uri = f"{self.exports_uri}/{self.export_name}"
        
        # Result tracking
        self.changed = False
        self.export_details = {}

    def get_export(self):
        """
        Get the current configuration of the NFS export.

        Returns:
            dict: Export configuration or None if not found
        """
        try:
            response, info = fetch_url(
                self.module,
                self.export_uri,
                method='GET',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] == 200:
                data = json.loads(response.read())
                self.export_details = data
                return data
            elif info['status'] == 404:
                return None
            else:
                self.module.fail_json(
                    msg=f"Failed to get NFS export: HTTP {info['status']}",
                    status=info['status']
                )
                
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting NFS export: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting NFS export: {str(e)}")

    def create_export(self):
        """
        Create a new NFS export.

        Returns:
            bool: True if successful
        """
        # Build export configuration
        export_config = {
            'name': self.export_name,
            'paths': [self.export_path],
            'clients': [
                {
                    'address': client,
                    'access': 'ro' if self.read_only else 'rw',
                    'root': False
                }
                for client in self.clients
            ]
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.exports_uri,
                method='POST',
                body=json.dumps(export_config),
                headers={'Content-Type': 'application/json'},
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201, 202]:
                self.module.fail_json(
                    msg=f"Failed to create NFS export: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            self.changed = True
            self.module.log(f"NFS export {self.export_name} created successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error creating NFS export: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error creating NFS export: {str(e)}")

    def update_export(self):
        """
        Update an existing NFS export.

        Returns:
            bool: True if changes were made, False otherwise
        """
        # Check if current configuration matches desired configuration
        current_clients = self.export_details.get('clients', [])
        desired_clients = [
            {
                'address': client,
                'access': 'ro' if self.read_only else 'rw',
                'root': False
            }
            for client in self.clients
        ]
        
        # Simple comparison - in production, would need more sophisticated diff
        if current_clients == desired_clients:
            self.module.log("NFS export already matches desired configuration")
            return False
        
        # Build update configuration
        export_config = {
            'paths': [self.export_path],
            'clients': desired_clients
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.export_uri,
                method='PUT',
                body=json.dumps(export_config),
                headers={'Content-Type': 'application/json'},
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 202]:
                self.module.fail_json(
                    msg=f"Failed to update NFS export: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            self.changed = True
            self.module.log(f"NFS export {self.export_name} updated successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error updating NFS export: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error updating NFS export: {str(e)}")

    def delete_export(self):
        """
        Delete an existing NFS export.

        Returns:
            bool: True if successful
        """
        try:
            response, info = fetch_url(
                self.module,
                self.export_uri,
                method='DELETE',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 202, 204]:
                self.module.fail_json(
                    msg=f"Failed to delete NFS export: HTTP {info['status']}",
                    status=info['status']
                )
            
            self.changed = True
            self.module.log(f"NFS export {self.export_name} deleted successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error deleting NFS export: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error deleting NFS export: {str(e)}")


def main():
    """Main function to execute the module."""
    module = AnsibleModule(
        argument_spec={
            'base_uri': {'type': 'str', 'required': True},
            'username': {'type': 'str', 'required': True},
            'password': {'type': 'str', 'required': True, 'no_log': True},
            'export_name': {'type': 'str', 'required': True},
            'export_path': {'type': 'str', 'required': True},
            'clients': {'type': 'list', 'required': True},
            'read_only': {'type': 'bool', 'required': False, 'default': False},
            'state': {
                'type': 'str',
                'required': False,
                'choices': ['present', 'absent'],
                'default': 'present'
            },
            'validate_certs': {
                'type': 'bool',
                'required': False,
                'default': False
            },
            'timeout': {
                'type': 'int',
                'required': False,
                'default': 120
            }
        },
        supports_check_mode=True
    )
    
    # Initialize OneFS NFS export handler
    nfs_export = OneFSNFSExport(module)
    
    # Get current export state
    current_export = nfs_export.get_export()
    
    # Handle state based on desired state
    if nfs_export.state == 'absent':
        if current_export is not None:
            if not module.check_mode:
                nfs_export.delete_export()
            module.exit_json(changed=True, export=current_export)
        else:
            module.exit_json(changed=False, export={})
    else:  # state == 'present'
        if current_export is None:
            if not module.check_mode:
                nfs_export.create_export()
                # Get the created export details
                nfs_export.get_export()
            module.exit_json(changed=True, export=nfs_export.export_details)
        else:
            if not module.check_mode:
                nfs_export.update_export()
                # Get the updated export details
                nfs_export.get_export()
            module.exit_json(changed=nfs_export.changed, export=nfs_export.export_details)


if __name__ == '__main__':
    main()
