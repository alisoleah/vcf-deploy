#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible Module: vcf_installer_api
Description: Interact with VCF Installer API for deployment operations
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
module: vcf_installer_api
short_description: Interact with VCF Installer API for deployment operations
description:
    - This module interacts with the VMware Cloud Foundation (VCF) Installer API.
    - Supports VCF versions 9.0 and 9.1.
    - Can submit deployment specifications, validate configurations, and monitor deployment tasks.
options:
    base_uri:
        description:
            - Base URI of the VCF Installer API (e.g., https://vcf-installer).
        required: true
        type: str
    username:
        description:
            - Username for VCF Installer API authentication.
        required: true
        type: str
    password:
        description:
            - Password for VCF Installer API authentication.
        required: true
        type: str
    operation:
        description:
            - The API operation to perform.
        required: true
        type: str
        choices: ['submit_deployment', 'validate_spec', 'get_task_status', 'get_bundles', 'get_releases']
    deployment_spec:
        description:
            - The VCF deployment specification (JSON format).
        required: false
        type: dict
    task_id:
        description:
            - The task ID for status queries.
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
    - This module requires the VCF Installer appliance to be deployed and accessible.
    - The module uses the VCF Installer REST API (OpenAPI 3.0.1 specification).
    - Different VCF versions (9.0 vs 9.1) have different API capabilities.
author:
    - VCF Automation Framework Team
'''

EXAMPLES = '''
- name: Submit VCF deployment specification
  vcf_installer_api:
    base_uri: "https://vcf-installer.example.com"
    username: "admin@local"
    password: "{{ vault_vcf_api_password }}"
    operation: "submit_deployment"
    deployment_spec: "{{ vcf_deployment_spec }}"
    validate_certs: false
  delegate_to: localhost

- name: Get deployment task status
  vcf_installer_api:
    base_uri: "https://vcf-installer.example.com"
    username: "admin@local"
    password: "{{ vault_vcf_api_password }}"
    operation: "get_task_status"
    task_id: "{{ deployment_task_id }}"
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
task_id:
    description: The task ID for async operations (if applicable).
    type: str
    returned: sometimes
'''


class VCFInstallerAPI:
    """Class to handle VCF Installer API operations."""

    def __init__(self, module):
        """
        Initialize the VCFInstallerAPI class.

        Args:
            module: AnsibleModule instance
        """
        self.module = module
        self.base_uri = module.params['base_uri']
        self.username = module.params['username']
        self.password = module.params['password']
        self.operation = module.params['operation']
        self.deployment_spec = module.params['deployment_spec']
        self.task_id = module.params['task_id']
        self.validate_certs = module.params['validate_certs']
        self.timeout = module.params['timeout']
        
        # Build API endpoints
        self.api_base = f"{self.base_uri}/v1"
        self.sddcs_uri = f"{self.api_base}/sddcs"
        self.validations_uri = f"{self.api_base}/sddcs/validations"
        self.tasks_uri = f"{self.api_base}/tasks"
        self.bundles_uri = f"{self.api_base}/bundles"
        self.releases_uri = f"{self.api_base}/releases"
        self.tokens_uri = f"{self.api_base}/tokens"
        
        # Result tracking
        self.changed = False
        self.result = {}
        self.return_task_id = None

    def get_auth_token(self):
        """
        Get authentication token from VCF Installer API.

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

    def submit_deployment(self):
        """
        Submit a VCF deployment specification.

        Returns:
            dict: Deployment submission result
        """
        token = self.get_auth_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.sddcs_uri,
                method='POST',
                body=json.dumps(self.deployment_spec),
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201, 202]:
                self.module.fail_json(
                    msg=f"Failed to submit deployment: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            data = json.loads(response.read())
            self.changed = True
            self.return_task_id = data.get('id', '')
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error submitting deployment: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error submitting deployment: {str(e)}")

    def validate_spec(self):
        """
        Validate a VCF deployment specification.

        Returns:
            dict: Validation result
        """
        token = self.get_auth_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.validations_uri,
                method='POST',
                body=json.dumps(self.deployment_spec),
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201, 202]:
                self.module.fail_json(
                    msg=f"Failed to validate spec: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            data = json.loads(response.read())
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error validating spec: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error validating spec: {str(e)}")

    def get_task_status(self):
        """
        Get the status of a deployment task.

        Returns:
            dict: Task status information
        """
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        task_uri = f"{self.tasks_uri}/{self.task_id}"
        
        try:
            response, info = fetch_url(
                self.module,
                task_uri,
                method='GET',
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get task status: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting task status: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting task status: {str(e)}")

    def get_bundles(self):
        """
        Get available VCF bundles.

        Returns:
            dict: Bundles information
        """
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.bundles_uri,
                method='GET',
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get bundles: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting bundles: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting bundles: {str(e)}")

    def get_releases(self):
        """
        Get available VCF releases.

        Returns:
            dict: Releases information
        """
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.releases_uri,
                method='GET',
                headers=headers,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] != 200:
                self.module.fail_json(
                    msg=f"Failed to get releases: HTTP {info['status']}",
                    status=info['status']
                )
            
            data = json.loads(response.read())
            self.result = data
            
            return data
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting releases: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting releases: {str(e)}")


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
                'choices': ['submit_deployment', 'validate_spec', 'get_task_status', 'get_bundles', 'get_releases']
            },
            'deployment_spec': {'type': 'dict', 'required': False},
            'task_id': {'type': 'str', 'required': False},
            'validate_certs': {'type': 'bool', 'required': False, 'default': False},
            'timeout': {'type': 'int', 'required': False, 'default': 300}
        },
        supports_check_mode=True
    )
    
    # Initialize VCF Installer API handler
    vcf_api = VCFInstallerAPI(module)
    
    # Execute the requested operation
    if vcf_api.operation == 'submit_deployment':
        if not module.check_mode:
            vcf_api.submit_deployment()
        module.exit_json(
            changed=vcf_api.changed,
            result=vcf_api.result,
            task_id=vcf_api.return_task_id
        )
    elif vcf_api.operation == 'validate_spec':
        vcf_api.validate_spec()
        module.exit_json(changed=False, result=vcf_api.result)
    elif vcf_api.operation == 'get_task_status':
        vcf_api.get_task_status()
        module.exit_json(changed=False, result=vcf_api.result)
    elif vcf_api.operation == 'get_bundles':
        vcf_api.get_bundles()
        module.exit_json(changed=False, result=vcf_api.result)
    elif vcf_api.operation == 'get_releases':
        vcf_api.get_releases()
        module.exit_json(changed=False, result=vcf_api.result)


if __name__ == '__main__':
    main()
