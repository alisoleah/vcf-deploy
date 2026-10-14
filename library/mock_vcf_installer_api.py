#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mock VCF Installer API Module
This module simulates VCF Installer API interactions for testing purposes.
It validates input parameters and returns mock responses without making actual API calls.
"""

from ansible.module_utils.basic import AnsibleModule
import json
import time
import uuid


def validate_deployment_spec(deployment_spec):
    """Validate the structure of a VCF deployment specification."""
    required_fields = [
        'sddcManagerSpec',
        'esxiSpecs',
        'networkSpecs',
        'nsxtSpec'
    ]

    if not isinstance(deployment_spec, dict):
        return False, "Deployment spec must be a dictionary"

    for field in required_fields:
        if field not in deployment_spec:
            return False, f"Missing required field: {field}"

    return True, "Valid"


def validate_spec(base_uri, username, password, deployment_spec, timeout):
    """Validate VCF deployment specification (mock)."""
    is_valid, message = validate_deployment_spec(deployment_spec)

    return {
        'changed': False,
        'result': {
            'valid': is_valid,
            'message': message,
            'errors': [] if is_valid else [message]
        }
    }


def submit_deployment(base_uri, username, password, deployment_spec, timeout):
    """Submit VCF deployment (mock)."""
    # Validate spec first
    is_valid, message = validate_deployment_spec(deployment_spec)
    if not is_valid:
        return {
            'failed': True,
            'msg': f"Deployment spec validation failed: {message}"
        }

    # Generate mock task ID
    task_id = str(uuid.uuid4())

    return {
        'changed': True,
        'task_id': task_id,
        'result': {
            'id': task_id,
            'status': 'IN_PROGRESS',
            'message': 'Deployment submitted successfully (mock)'
        }
    }


def get_task_status(base_uri, username, password, task_id, timeout):
    """Get task status (mock)."""
    # Simulate task completion after a few calls
    # In real testing, this would track state

    return {
        'changed': False,
        'result': {
            'id': task_id,
            'status': 'COMPLETED',
            'progress': 100,
            'message': 'Deployment completed successfully (mock)',
            'startTime': '2024-01-01T00:00:00Z',
            'endTime': '2024-01-01T01:00:00Z'
        }
    }


def get_bundles(base_uri, username, password, timeout):
    """Get available VCF bundles (mock)."""
    return {
        'changed': False,
        'result': {
            'bundles': [
                {
                    'id': 'bundle-1',
                    'version': '9.1.0.0',
                    'type': 'VCF',
                    'description': 'VCF 9.1 Bundle (mock)'
                }
            ]
        }
    }


def get_releases(base_uri, username, password, timeout):
    """Get available VCF releases (mock)."""
    return {
        'changed': False,
        'result': {
            'releases': [
                {
                    'id': 'release-1',
                    'version': '9.1.0',
                    'description': 'VCF 9.1 Release (mock)'
                }
            ]
        }
    }


def main():
    """Main module entry point."""
    module_args = dict(
        base_uri=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        operation=dict(
            type='str',
            required=True,
            choices=[
                'validate_spec',
                'submit_deployment',
                'get_task_status',
                'get_bundles',
                'get_releases'
            ]
        ),
        deployment_spec=dict(type='dict', required=False),
        task_id=dict(type='str', required=False),
        validate_certs=dict(type='bool', default=False),
        timeout=dict(type='int', default=300)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    base_uri = module.params['base_uri']
    username = module.params['username']
    password = module.params['password']
    operation = module.params['operation']
    deployment_spec = module.params.get('deployment_spec')
    task_id = module.params.get('task_id')
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']

    # Log mock operation
    module.log(f"Mock VCF Installer API - Operation: {operation}")
    module.log(f"Mock VCF Installer API - Base URI: {base_uri}")
    module.log(f"Mock VCF Installer API - Username: {username}")

    # Check mode
    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"Would execute operation: {operation} (check mode)"
        )

    # Execute operation
    try:
        if operation == 'validate_spec':
            if not deployment_spec:
                module.fail_json(msg="deployment_spec is required for validate_spec operation")
            result = validate_spec(base_uri, username, password, deployment_spec, timeout)

        elif operation == 'submit_deployment':
            if not deployment_spec:
                module.fail_json(msg="deployment_spec is required for submit_deployment operation")
            result = submit_deployment(base_uri, username, password, deployment_spec, timeout)

        elif operation == 'get_task_status':
            if not task_id:
                module.fail_json(msg="task_id is required for get_task_status operation")
            result = get_task_status(base_uri, username, password, task_id, timeout)

        elif operation == 'get_bundles':
            result = get_bundles(base_uri, username, password, timeout)

        elif operation == 'get_releases':
            result = get_releases(base_uri, username, password, timeout)

        else:
            module.fail_json(msg=f"Unknown operation: {operation}")

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Mock VCF Installer API error: {str(e)}")


if __name__ == '__main__':
    main()
