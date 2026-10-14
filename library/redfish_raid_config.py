#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible Module: redfish_raid_config
Description: Configure hardware RAID controller settings via Redfish API
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
module: redfish_raid_config
short_description: Configure hardware RAID controller settings via Redfish API
description:
    - This module configures hardware RAID controller settings on physical servers using the Redfish API.
    - Supports Dell iDRAC, HPE iLO, and other Redfish-compliant BMCs.
    - Can configure RAID mode, cache policy, and create/delete virtual disks.
options:
    base_uri:
        description:
            - Base URI of the Redfish API (e.g., https://bmc-hostname).
        required: true
        type: str
    username:
        description:
            - Username for Redfish API authentication.
        required: true
        type: str
    password:
        description:
            - Password for Redfish API authentication.
        required: true
        type: str
    controller_mode:
        description:
            - RAID controller mode (raid or hba).
        required: false
        type: str
        choices: ['raid', 'hba']
    cache_policy:
        description:
            - Cache policy for the RAID controller.
        required: false
        type: str
        choices: ['writeback', 'writethrough']
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
        default: 60
notes:
    - This module requires the Redfish API to be accessible on the BMC.
    - RAID configuration changes may require a server reboot to take effect.
    - Some RAID controller operations may result in data loss.
author:
    - VCF Automation Framework Team
'''

EXAMPLES = '''
- name: Configure RAID controller via Redfish
  redfish_raid_config:
    base_uri: "https://bmc01.example.com"
    username: "root"
    password: "{{ vault_bmc_password }}"
    controller_mode: "raid"
    cache_policy: "writeback"
    validate_certs: false
    timeout: 60
  delegate_to: localhost

- name: Set controller to HBA mode
  redfish_raid_config:
    base_uri: "https://bmc02.example.com"
    username: "root"
    password: "{{ vault_bmc_password }}"
    controller_mode: "hba"
  delegate_to: localhost
'''

RETURN = '''
changed:
    description: Whether the RAID configuration was changed.
    type: bool
    returned: always
controllers:
    description: List of RAID controllers and their configuration.
    type: list
    returned: always
reboot_required:
    description: Whether a reboot is required for changes to take effect.
    type: bool
    returned: always
'''


class RedfishRAIDConfig:
    """Class to handle Redfish RAID configuration operations."""

    def __init__(self, module):
        """
        Initialize the RedfishRAIDConfig class.

        Args:
            module: AnsibleModule instance
        """
        self.module = module
        self.base_uri = module.params['base_uri']
        self.username = module.params['username']
        self.password = module.params['password']
        self.validate_certs = module.params['validate_certs']
        self.timeout = module.params['timeout']
        
        # Build API endpoints
        self.systems_uri = f"{self.base_uri}/redfish/v1/Systems"
        self.storage_uri = None
        
        # Result tracking
        self.changed = False
        self.reboot_required = False
        self.controllers = []

    def get_system_uri(self):
        """
        Get the URI of the first system in the Redfish service.

        Returns:
            str: System URI or None if not found
        """
        try:
            response, info = fetch_url(
                self.module,
                self.systems_uri,
                method='GET',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get systems list: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            
            if 'Members' in data and len(data['Members']) > 0:
                return data['Members'][0]['@odata.id']
            else:
                self.module.fail_json(msg="No systems found in Redfish service")
                
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting systems: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting systems: {str(e)}")

    def get_storage_uri(self, system_uri):
        """
        Get the storage URI from the system URI.

        Args:
            system_uri: URI of the system

        Returns:
            str: Storage URI or None if not found
        """
        try:
            response, info = fetch_url(
                self.module,
                f"{self.base_uri}{system_uri}",
                method='GET',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get system details: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            
            if 'Storage' in data:
                storage_uri = data['Storage']['@odata.id']
                self.storage_uri = f"{self.base_uri}{storage_uri}"
                return self.storage_uri
            else:
                self.module.fail_json(msg="Storage resource not found in system")
                
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting storage URI: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting storage URI: {str(e)}")

    def get_raid_controllers(self):
        """
        Get the list of RAID controllers from the storage subsystem.

        Returns:
            list: List of RAID controllers
        """
        try:
            response, info = fetch_url(
                self.module,
                self.storage_uri,
                method='GET',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get storage subsystems: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            
            controllers = []
            
            if 'Members' in data:
                for member in data['Members']:
                    controller_uri = f"{self.base_uri}{member['@odata.id']}"
                    controller_response, controller_info = fetch_url(
                        self.module,
                        controller_uri,
                        method='GET',
                        url_username=self.username,
                        url_password=self.password,
                        validate_certs=self.validate_certs,
                        timeout=self.timeout
                    )
                    
                    if controller_info['status'] == 200:
                        controller_data = json.loads(controller_response.read())
                        controllers.append(controller_data)
            
            self.controllers = controllers
            return controllers
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting RAID controllers: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting RAID controllers: {str(e)}")

    def configure_raid_controller(self, controller):
        """
        Configure a RAID controller based on module parameters.

        Args:
            controller: Controller configuration dictionary

        Returns:
            bool: True if changes were made, False otherwise
        """
        # Check if controller supports configuration
        if 'Links' not in controller or 'Settings' not in controller['Links']:
            self.module.log(f"Controller {controller.get('Id', 'unknown')} does not support configuration")
            return False
        
        settings_uri = f"{self.base_uri}{controller['Links']['Settings']['@odata.id']}"
        
        # Build configuration payload
        config = {}
        
        # Controller mode configuration
        if self.module.params['controller_mode']:
            config['RAIDMode'] = self.module.params['controller_mode'].upper()
        
        # Cache policy configuration
        if self.module.params['cache_policy']:
            config['CachePolicy'] = self.module.params['cache_policy'].upper()
        
        # Check if any changes are needed
        if not config:
            self.module.log("No RAID configuration parameters provided")
            return False
        
        # Apply configuration
        try:
            response, info = fetch_url(
                self.module,
                settings_uri,
                method='PATCH',
                body=json.dumps(config),
                headers={'Content-Type': 'application/json'},
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 202, 204]:
                self.module.fail_json(
                    msg=f"Failed to configure RAID controller: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            self.changed = True
            self.reboot_required = True
            self.module.log(f"RAID controller {controller.get('Id', 'unknown')} configured successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error configuring RAID controller: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error configuring RAID controller: {str(e)}")


def main():
    """Main function to execute the module."""
    module = AnsibleModule(
        argument_spec={
            'base_uri': {'type': 'str', 'required': True},
            'username': {'type': 'str', 'required': True},
            'password': {'type': 'str', 'required': True, 'no_log': True},
            'controller_mode': {
                'type': 'str',
                'required': False,
                'choices': ['raid', 'hba']
            },
            'cache_policy': {
                'type': 'str',
                'required': False,
                'choices': ['writeback', 'writethrough']
            },
            'validate_certs': {
                'type': 'bool',
                'required': False,
                'default': False
            },
            'timeout': {
                'type': 'int',
                'required': False,
                'default': 60
            }
        },
        supports_check_mode=True
    )
    
    # Initialize Redfish RAID configuration handler
    raid_config = RedfishRAIDConfig(module)
    
    # Get system URI
    system_uri = raid_config.get_system_uri()
    
    # Get storage URI
    raid_config.get_storage_uri(system_uri)
    
    # Get RAID controllers
    raid_config.get_raid_controllers()
    
    # If not in check mode, apply configuration
    if not module.check_mode:
        for controller in raid_config.controllers:
            raid_config.configure_raid_controller(controller)
    
    # Return results
    module.exit_json(
        changed=raid_config.changed,
        controllers=raid_config.controllers,
        reboot_required=raid_config.reboot_required
    )


if __name__ == '__main__':
    main()
