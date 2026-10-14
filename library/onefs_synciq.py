#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible Module: onefs_synciq
Description: Configure SyncIQ replication policies on Dell PowerScale/Isilon via OneFS API
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
module: onefs_synciq
short_description: Configure SyncIQ replication policies on Dell PowerScale/Isilon via OneFS API
description:
    - This module configures SyncIQ replication policies on Dell PowerScale/Isilon storage clusters using the OneFS API.
    - Can create, modify, and delete SyncIQ policies.
    - Supports configuring source and target paths, schedules, and replication options.
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
    policy_name:
        description:
            - Name of the SyncIQ policy.
        required: true
        type: str
    source_path:
        description:
            - Source file system path for replication.
        required: true
        type: str
    target_host:
        description:
            - Target PowerScale cluster hostname or IP address.
        required: true
        type: str
    target_path:
        description:
            - Target file system path for replication.
        required: true
        type: str
    target_username:
        description:
            - Username for target cluster authentication.
        required: true
        type: str
    target_password:
        description:
            - Password for target cluster authentication.
        required: true
        type: str
    schedule:
        description:
            - Schedule for replication (e.g., daily, hourly, or cron expression).
        required: false
        type: str
        default: daily
    enabled:
        description:
            - Whether the policy is enabled.
        required: false
        type: bool
        default: true
    state:
        description:
            - Desired state of the policy (present or absent).
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
    - SyncIQ policies require proper network connectivity between source and target clusters.
    - The module uses the OneFS Platform API (RESTful interface).
author:
    - VCF Automation Framework Team
'''

EXAMPLES = '''
- name: Create SyncIQ policy for VCF replication
  onefs_synciq:
    base_uri: "https://powerscale.example.com:8080"
    username: "root"
    password: "{{ vault_powerscale_password }}"
    policy_name: "vcf-replication"
    source_path: "/ifs/vcf"
    target_host: "powerscale-backup.example.com"
    target_path: "/ifs/vcf-backup"
    target_username: "root"
    target_password: "{{ vault_synciq_target_password }}"
    schedule: "daily"
    enabled: true
    state: present
    validate_certs: false
  delegate_to: localhost

- name: Delete SyncIQ policy
  onefs_synciq:
    base_uri: "https://powerscale.example.com:8080"
    username: "root"
    password: "{{ vault_powerscale_password }}"
    policy_name: "vcf-replication"
    state: absent
  delegate_to: localhost
'''

RETURN = '''
changed:
    description: Whether the SyncIQ policy was changed.
    type: bool
    returned: always
policy:
    description: Details of the SyncIQ policy configuration.
    type: dict
    returned: always
'''


class OneFSSyncIQ:
    """Class to handle OneFS SyncIQ policy operations."""

    def __init__(self, module):
        """
        Initialize the OneFSSyncIQ class.

        Args:
            module: AnsibleModule instance
        """
        self.module = module
        self.base_uri = module.params['base_uri']
        self.username = module.params['username']
        self.password = module.params['password']
        self.policy_name = module.params['policy_name']
        self.source_path = module.params['source_path']
        self.target_host = module.params['target_host']
        self.target_path = module.params['target_path']
        self.target_username = module.params['target_username']
        self.target_password = module.params['target_password']
        self.schedule = module.params['schedule']
        self.enabled = module.params['enabled']
        self.state = module.params['state']
        self.validate_certs = module.params['validate_certs']
        self.timeout = module.params['timeout']
        
        # Build API endpoints
        self.policies_uri = f"{self.base_uri}/platform/1/sync/policies"
        self.policy_uri = f"{self.policies_uri}/{self.policy_name}"
        
        # Result tracking
        self.changed = False
        self.policy_details = {}

    def get_policy(self):
        """
        Get the current configuration of the SyncIQ policy.

        Returns:
            dict: Policy configuration or None if not found
        """
        try:
            response, info = fetch_url(
                self.module,
                self.policy_uri,
                method='GET',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] == 200:
                data = json.loads(response.read())
                self.policy_details = data
                return data
            elif info['status'] == 404:
                return None
            else:
                self.module.fail_json(
                    msg=f"Failed to get SyncIQ policy: HTTP {info['status']}",
                    status=info['status']
                )
                
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error getting SyncIQ policy: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error getting SyncIQ policy: {str(e)}")

    def create_policy(self):
        """
        Create a new SyncIQ policy.

        Returns:
            bool: True if successful
        """
        # Build policy configuration
        policy_config = {
            'name': self.policy_name,
            'action': 'sync',
            'source_root_path': self.source_path,
            'target_root_path': self.target_path,
            'target_host': self.target_host,
            'target_user': self.target_username,
            'target_password': self.target_password,
            'enabled': self.enabled,
            'schedule': self._build_schedule()
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.policies_uri,
                method='POST',
                body=json.dumps(policy_config),
                headers={'Content-Type': 'application/json'},
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 201, 202]:
                self.module.fail_json(
                    msg=f"Failed to create SyncIQ policy: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            self.changed = True
            self.module.log(f"SyncIQ policy {self.policy_name} created successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error creating SyncIQ policy: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error creating SyncIQ policy: {str(e)}")

    def update_policy(self):
        """
        Update an existing SyncIQ policy.

        Returns:
            bool: True if changes were made, False otherwise
        """
        # Check if current configuration matches desired configuration
        current_enabled = self.policy_details.get('enabled', False)
        if current_enabled == self.enabled:
            self.module.log("SyncIQ policy already matches desired configuration")
            return False
        
        # Build update configuration
        policy_config = {
            'enabled': self.enabled,
            'schedule': self._build_schedule()
        }
        
        try:
            response, info = fetch_url(
                self.module,
                self.policy_uri,
                method='PUT',
                body=json.dumps(policy_config),
                headers={'Content-Type': 'application/json'},
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 202]:
                self.module.fail_json(
                    msg=f"Failed to update SyncIQ policy: HTTP {info['status']}",
                    status=info['status'],
                    response=response.read() if response else None
                )
            
            self.changed = True
            self.module.log(f"SyncIQ policy {self.policy_name} updated successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error updating SyncIQ policy: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error updating SyncIQ policy: {str(e)}")

    def delete_policy(self):
        """
        Delete an existing SyncIQ policy.

        Returns:
            bool: True if successful
        """
        try:
            response, info = fetch_url(
                self.module,
                self.policy_uri,
                method='DELETE',
                url_username=self.username,
                url_password=self.password,
                validate_certs=self.validate_certs,
                timeout=self.timeout
            )
            
            if info['status'] not in [200, 202, 204]:
                self.module.fail_json(
                    msg=f"Failed to delete SyncIQ policy: HTTP {info['status']}",
                    status=info['status']
                )
            
            self.changed = True
            self.module.log(f"SyncIQ policy {self.policy_name} deleted successfully")
            return True
            
        except HTTPError as e:
            self.module.fail_json(msg=f"HTTP error deleting SyncIQ policy: {str(e)}")
        except Exception as e:
            self.module.fail_json(msg=f"Error deleting SyncIQ policy: {str(e)}")

    def _build_schedule(self):
        """
        Build the schedule configuration based on the schedule parameter.

        Returns:
            dict: Schedule configuration
        """
        if self.schedule == 'daily':
            return {
                'frequency': 'daily',
                'time': '02:00'
            }
        elif self.schedule == 'hourly':
            return {
                'frequency': 'hourly'
            }
        else:
            # Assume it's a cron expression
            return {
                'frequency': 'custom',
                'pattern': self.schedule
            }


def main():
    """Main function to execute the module."""
    module = AnsibleModule(
        argument_spec={
            'base_uri': {'type': 'str', 'required': True},
            'username': {'type': 'str', 'required': True},
            'password': {'type': 'str', 'required': True, 'no_log': True},
            'policy_name': {'type': 'str', 'required': True},
            'source_path': {'type': 'str', 'required': True},
            'target_host': {'type': 'str', 'required': True},
            'target_path': {'type': 'str', 'required': True},
            'target_username': {'type': 'str', 'required': True},
            'target_password': {'type': 'str', 'required': True, 'no_log': True},
            'schedule': {'type': 'str', 'required': False, 'default': 'daily'},
            'enabled': {'type': 'bool', 'required': False, 'default': True},
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
    
    # Initialize OneFS SyncIQ handler
    synciq = OneFSSyncIQ(module)
    
    # Get current policy state
    current_policy = synciq.get_policy()
    
    # Handle state based on desired state
    if synciq.state == 'absent':
        if current_policy is not None:
            if not module.check_mode:
                synciq.delete_policy()
            module.exit_json(changed=True, policy=current_policy)
        else:
            module.exit_json(changed=False, policy={})
    else:  # state == 'present'
        if current_policy is None:
            if not module.check_mode:
                synciq.create_policy()
                # Get the created policy details
                synciq.get_policy()
            module.exit_json(changed=True, policy=synciq.policy_details)
        else:
            if not module.check_mode:
                synciq.update_policy()
                # Get the updated policy details
                synciq.get_policy()
            module.exit_json(changed=synciq.changed, policy=synciq.policy_details)


if __name__ == '__main__':
    main()
