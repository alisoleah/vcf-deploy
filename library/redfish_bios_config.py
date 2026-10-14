#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible Module: redfish_bios_config
Description: Configure BIOS/UEFI settings on servers via Redfish API
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
module: redfish_bios_config
short_description: Configure BIOS/UEFI settings via Redfish API
description:
    - This module configures BIOS/UEFI settings on physical servers using the Redfish API.
    - Supports Dell iDRAC, HPE iLO, and other Redfish-compliant BMCs.
    - Can configure boot mode, virtualization settings, power management, and other BIOS parameters.
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
    boot_mode:
        description:
            - Boot mode to configure (uefi or bios).
        required: false
        type: str
        choices: ['uefi', 'bios']
    virtualization:
        description:
            - Enable or disable virtualization support.
        required: false
        type: bool
    power_management:
        description:
            - Enable or disable power management features.
        required: false
        type: bool
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
    - Changes to BIOS settings typically require a server reboot to take effect.
    - Some settings may not be available on all server platforms.
author:
    - VCF Automation Framework Team
'''

EXAMPLES = '''
- name: Configure BIOS settings via Redfish
  redfish_bios_config:
    base_uri: "https://bmc01.example.com"
    username: "root"
    password: "{{ vault_bmc_password }}"
    boot_mode: "uefi"
    virtualization: true
    power_management: true
    validate_certs: false
    timeout: 60
  delegate_to: localhost

- name: Set BIOS to legacy mode
  redfish_bios_config:
    base_uri: "https://bmc02.example.com"
    username: "root"
    password: "{{ vault_bmc_password }}"
    boot_mode: "bios"
    virtualization: false
  delegate_to: localhost
'''

RETURN = '''
changed:
    description: Whether the BIOS configuration was changed.
    type: bool
    returned: always
settings:
    description: The current BIOS settings after configuration.
    type: dict
    returned: always
reboot_required:
    description: Whether a reboot is required for changes to take effect.
    type: bool
    returned: always
'''


class RedfishBiosConfig:
    """Class to handle Redfish BIOS configuration operations."""

    def __init__(self, module):
        """
        Initialize the RedfishBiosConfig class.

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
        self.bios_uri = None
        self.bios_settings_uri = None
        
        # Result tracking
        self.changed = False
        self.reboot_required = False
        self.current_settings = {}

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

    def get_bios_uri(self, system_uri):
        """
        Get the BIOS URI from the system URI.

        Args:
            system_uri: URI of the system

        Returns:
            str: BIOS URI or None if not found
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
            
            if 'Bios' in data:
                bios_uri = data['Bios']['@odata.id']
                self.bios_uri = f"{self.base_uri}{bios_uri}"
                return self.bios_uri
            else:
                self.module.fail_json(msg="BIOS resource not found in system")
                
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting BIOS URI: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting BIOS URI: {str(e)}")

    def get_current_bios_settings(self):
        """
        Get the current BIOS settings from the BMC.

        Returns:
            dict: Current BIOS settings
        """
        try:
            response, info = fetch_url(
                self.module,
                self.bios_uri,
                method='GET',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get BIOS settings: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            
            # Store current settings
            self.current_settings = data
            
            # Check for BIOS settings URI (for configuration)
            if 'Settings' in data and '@odata.id' in data['Settings']:
                self.bios_settings_uri = f"{self.base_uri}{data['Settings']['@odata.id']}"
            
            return self.current_settings
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting BIOS settings: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting BIOS settings: {str(e)}")

    def configure_bios_settings(self):
        """
        Configure BIOS settings based on module parameters.

        Returns:
            bool: True if changes were made, False otherwise
        """
        if not self.bios_settings_uri:
            self.module.fail_json(msg="BIOS settings URI not available for configuration")
        
        # Build configuration payload
        config = {}
        
        # Boot mode configuration
        if self.module.params['boot_mode']:
            boot_mode = self.module.params['boot_mode'].upper()
            config['BootMode'] = boot_mode
        
        # Virtualization configuration
        if self.module.params['virtualization'] is not None:
            config['ProcVirtualization'] = 'Enabled' if self.module.params['virtualization'] else 'Disabled'
        
        # Power management configuration
        if self.module.params['power_management'] is not None:
            config['PowerProfile'] = 'Performance' if self.module.params['power_management'] else 'Balanced'
        
        # Check if any changes are needed
        if not config:
            self.module.log("No BIOS configuration parameters provided")
            return False
        
        # Check if current settings match desired settings
        changes_needed = False
        for key, value in config.items():
            if key in self.current_settings and self.current_settings[key] != value:
                changes_needed = True
                break
            elif key not in self.current_settings:
                changes_needed = True
                break
        
        if not changes_needed:
            self.module.log("BIOS settings already match desired configuration")
            return False
        
        # Apply configuration
        try:
            response, info = fetch_url(
                self.module,
                self.bios_settings_uri,
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
                    msg=f"Failed to configure BIOS settings: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            self.changed = True
            self.reboot_required = True
            self.module.log("BIOS configuration applied successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error configuring BIOS: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error configuring BIOS: {str(e)}")


def main():
    """Main function to execute the module."""
    module = AnsibleModule(
        argument_spec={
            'base_uri': {'type': 'str', 'required': True},
            'username': {'type': 'str', 'required': True},
            'password': {'type': 'str', 'required': True, 'no_log': True},
            'boot_mode': {
                'type': 'str',
                'required': False,
                'choices': ['uefi', 'bios']
            },
            'virtualization': {
                'type': 'bool',
                'required': False
            },
            'power_management': {
                'type': 'bool',
                'required': False
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
    
    # Initialize Redfish BIOS configuration handler
    bios_config = RedfishBiosConfig(module)
    
    # Get system URI
    system_uri = bios_config.get_system_uri()
    
    # Get BIOS URI
    bios_config.get_bios_uri(system_uri)
    
    # Get current BIOS settings
    bios_config.get_current_bios_settings()
    
    # If not in check mode, apply configuration
    if not module.check_mode:
        bios_config.configure_bios_settings()
    
    # Return results
    module.exit_json(
        changed=bios_config.changed,
        settings=bios_config.current_settings,
        reboot_required=bios_config.reboot_required
    )


if __name__ == '__main__':
    main()
