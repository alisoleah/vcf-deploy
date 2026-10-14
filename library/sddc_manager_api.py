#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible Module: sddc_manager_api
Description: Interact with SDDC Manager API for Day 2 operations
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
module: sddc_manager_api
short_description: Interact with SDDC Manager API for Day 2 operations
description:
    - This module interacts with the VMware Cloud Foundation (VCF) SDDC Manager API.
    - Supports VCF versions 9.0 and 9.1.
    - Can deploy VCF Automation and VCF Operations appliances, validate registrations, and manage Fleet layer.
options:
    base_uri:
        description:
            - Base URI of the SDDC Manager API (e.g., https://sddc-manager).
        required: true
        type: str
    username:
        description:
            - Username for SDDC Manager API authentication.
        required: true
        type: str
    password:
        description:
            - Password for SDDC Manager API authentication.
        required: true
        type: str
    operation:
        description:
            - The API operation to perform.
        required: true
        type: str
        choices: ['deploy_automation', 'deploy_operations', 'get_appliance_status', 'validate_registration', 'get_fleet_status']
    appliance_spec:
        description:
            - The appliance deployment specification (JSON format).
        required: false
        type: dict
    appliance_id:
        description:
            - The appliance ID for status queries.
        required: false
        type: str
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
        default: 300
notes:
    - This module requires the SDDC Manager to be deployed and accessible.
    - The module uses the SDDC Manager REST API (OpenAPI 3.0.1 specification).
    - Different VCF versions (9.0 vs 9.1) may have different API capabilities.
author:
    - VCF Automation Framework Team
'''

EXAMPLES = '''
- name: Deploy VCF Automation appliance
  sddc_manager_api:
    base_uri: "https://sddc-manager.example.com"
    username: "admin@local"
    password: "{{ vault_vcf_admin_password }}"
    operation: "deploy_automation"
    appliance_spec: "{{ vcf_automation_appliance_spec }}"
    validate_certs: false
  delegate_to: localhost

- name: Validate VCF Automation registration
  sddc_manager_api:
    base_uri: "https://sddc-manager.example.com"
    username: "admin@local"
    password: "{{ vault_vcf_admin_password }}"
    operation: "validate_registration"
    appliance_id: "{{ vcf_automation_appliance_id }}"
  delegate_to: localhost
'''

RETURN = '''
changed:
    description: Whether the operation resulted in a change.
    type: bool
    returned: always
result:
    description: The result of the API operation.
    type: dict
    returned: always
appliance_id:
    description: The appliance ID for async operations (if applicable).
    type: str
    returned: sometimes
registration_status:
    description: The registration status with vCenter and NSX.
    type: dict
    returned: sometimes
'''


class SDDCManagerAPI:
    """Class to handle SDDC Manager API operations."""

    def __init__(self, module):
        """
        Initialize the SDDCManagerAPI class.

        Args:
            module: AnsibleModule instance
        """
        self.module = module
        self.base_uri = module.params['base_uri']
        self.username = module.params['username']
        self.password = module.params['password']
        self.operation = module.params['operation']
        self.appliance_spec = module.params['appliance_spec']
        self.appliance_id = module.params['appliance_id']
        self.validate_certs = module.params['validate_certs']
        self.timeout = module.params['timeout']
        
        # Build API endpoints
        self.api_base = f"{self.base_uri}/v1"
        self.fleet_uri = f"{self.api_base}/fleet"
        self.automation_uri = f"{self.api_base}/vcf-automation"
        self.operations_uri = f"{self.api_base}/vcf-operations"
        self.tokens_uri = f"{self.api_base}/tokens"
        
        # Result tracking
        self.changed = False
        self.result = {}
        self.return_appliance_id = None
        self.registration_status = {}

    def get_auth_token(self):
        """
        Get authentication token from SDDC Manager API.

        Returns:
            str: Authentication token
        """
        try:
            auth_payload = {
                'username': self.username,
                'password': self.password
            }
            
            response, info = fetch_url(
                self.module,
                self.tokens_uri,
                method='POST',
                body=json.dumps(auth_payload),
                headers={'Content-Type': 'application/json'},
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201]:
                self.module.fail_json(
                    msg=f"Failed to get authentication token: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            token = data.get('token', '')
            
            if not token:
                self.module.fail_json(msg="No token returned from authentication")
            
            return token
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting auth token: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting auth token: {str(e)}")

    def deploy_automation_appliance(self):
        """
        Deploy VCF Automation appliance.

        Returns:
            dict: Deployment result
        """
        token = self.get_auth_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.automation_uri,
                method='POST',
                body=json.dumps(self.appliance_spec),
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201, 202]:
                self.module.fail_json(
                    msg=f"Failed to deploy VCF Automation appliance: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            data = json.loads(response.read())
            self.changed = True
            self.return_appliance_id = data.get('id', '')
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error deploying VCF Automation appliance: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error deploying VCF Automation appliance: {str(e)}")

    def deploy_operations_appliance(self):
        """
        Deploy VCF Operations appliance.

        Returns:
            dict: Deployment result
        """
        token = self.get_auth_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.operations_uri,
                method='POST',
                body=json.dumps(self.appliance_spec),
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201, 202]:
                self.module.fail_json(
                    msg=f"Failed to deploy VCF Operations appliance: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            data = json.loads(response.read())
            self.changed = True
            self.return_appliance_id = data.get('id', '')
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error deploying VCF Operations appliance: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error deploying VCF Operations appliance: {str(e)}")

    def get_appliance_status(self):
        """
        Get the status of an appliance deployment.

        Returns:
            dict: Appliance status information
        """
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Determine which endpoint to use based on appliance_id prefix
        if self.appliance_id.startswith('automation'):
            appliance_uri = f"{self.automation_uri}/{self.appliance_id}"
        elif self.appliance_id.startswith('operations'):
            appliance_uri = f"{self.operations_uri}/{self.appliance_id}"
        else:
            self.module.fail_json(msg="Cannot determine appliance type from ID")
        
        try:
            response, info = fetch_url(
                self.module,
                appliance_uri,
                method='GET',
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get appliance status: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting appliance status: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting appliance status: {str(e)}")

    def validate_registration(self):
        """
        Validate appliance registration with vCenter and NSX.

        Returns:
            dict: Registration status
        """
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Determine which endpoint to use based on appliance_id prefix
        if self.appliance_id.startswith('automation'):
            registration_uri = f"{self.automation_uri}/{self.appliance_id}/registration"
        elif self.appliance_id.startswith('operations'):
            registration_uri = f"{self.operations_uri}/{self.appliance_id}/registration"
        else:
            self.module.fail_json(msg="Cannot determine appliance type from ID")
        
        try:
            response, info = fetch_url(
                self.module,
                registration_uri,
                method='GET',
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to validate registration: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            self.registration_status = data
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error validating registration: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error validating registration: {str(e)}")

    def get_fleet_status(self):
        """
        Get the status of the Fleet layer.

        Returns:
            dict: Fleet status information
        """
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.fleet_uri,
                method='GET',
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get fleet status: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting fleet status: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting fleet status: {str(e)}")


def main():
    """Main function to execute the module."""
    module = AnsibleModule(
        argument_spec={
            'base_uri': {'type': 'str', 'required': True},
            'username': {'type': 'str', 'required': True},
            'password': {'type': 'str', 'required': True, 'no_log': True},
            'operation': {
                'type': 'str',
                'required': True,
                'choices': ['deploy_automation', 'deploy_operations', 'get_appliance_status', 'validate_registration', 'get_fleet_status']
            },
            'appliance_spec': {'type': 'dict', 'required': False},
            'appliance_id': {'type': 'str', 'required': False},
            'validate_certs': {'type': 'bool', 'required': False, 'default': False},
            'timeout': {'type': 'int', 'required': False, 'default': 300}
        },
        supports_check_mode=True
    )
    
    # Initialize SDDC Manager API handler
    sddc_api = SDDCManagerAPI(module)
    
    # Execute the requested operation
    if sddc_api.operation == 'deploy_automation':
        if not module.check_mode:
            sddc_api.deploy_automation_appliance()
        module.exit_json(
            changed=sddc_api.changed,
            result=sddc_api.result,
            appliance_id=sddc_api.return_appliance_id
        )
    elif sddc_api.operation == 'deploy_operations':
        if not module.check_mode:
            sddc_api.deploy_operations_appliance()
        module.exit_json(
            changed=sddc_api.changed,
            result=sddc_api.result,
            appliance_id=sddc_api.return_appliance_id
        )
    elif sddc_api.operation == 'get_appliance_status':
        sddc_api.get_appliance_status()
        module.exit_json(changed=False, result=sddc_api.result)
    elif sddc_api.operation == 'validate_registration':
        sddc_api.validate_registration()
        module.exit_json(
            changed=False,
            result=sddc_api.result,
            registration_status=sddc_api.registration_status
        )
    elif sddc_api.operation == 'get_fleet_status':
        sddc_api.get_fleet_status()
        module.exit_json(changed=False, result=sddc_api.result)


if __name__ == '__main__':
    main()
