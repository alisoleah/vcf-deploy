#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mock SDDC Manager API Module
This module simulates SDDC Manager API interactions for testing purposes.
It validates input parameters and returns mock responses without making actual API calls.
"""

from ansible.module_utils.basic import AnsibleModule
import json
import uuid


def validate_appliance_spec(appliance_spec):
    """Validate the structure of an appliance specification."""
    required_fields = ['spec']

    if not isinstance(appliance_spec, dict):
        return False, "Appliance spec must be a dictionary"

    if 'spec' not in appliance_spec:
        return False, "Missing required field: spec"

    spec = appliance_spec['spec']
    spec_required = ['name', 'type', 'sizing', 'network']

    for field in spec_required:
        if field not in spec:
            return False, f"Missing required field in spec: {field}"

    return True, "Valid"


def deploy_automation(base_uri, username, password, appliance_spec, timeout):
    """Deploy VCF Automation appliance (mock)."""
    is_valid, message = validate_appliance_spec(appliance_spec)
    if not is_valid:
        return {
            'failed': True,
            'msg': f"Appliance spec validation failed: {message}"
        }

    # Generate mock appliance ID
    appliance_id = str(uuid.uuid4())

    return {
        'changed': True,
        'appliance_id': appliance_id,
        'result': {
            'id': appliance_id,
            'name': appliance_spec['spec']['name'],
            'type': 'VCF_AUTOMATION',
            'status': 'DEPLOYING',
            'message': 'VCF Automation appliance deployment started (mock)'
        }
    }


def deploy_operations(base_uri, username, password, appliance_spec, timeout):
    """Deploy VCF Operations appliance (mock)."""
    is_valid, message = validate_appliance_spec(appliance_spec)
    if not is_valid:
        return {
            'failed': True,
            'msg': f"Appliance spec validation failed: {message}"
        }

    # Generate mock appliance ID
    appliance_id = str(uuid.uuid4())

    return {
        'changed': True,
        'appliance_id': appliance_id,
        'result': {
            'id': appliance_id,
            'name': appliance_spec['spec']['name'],
            'type': 'VCF_OPERATIONS',
            'status': 'DEPLOYING',
            'message': 'VCF Operations appliance deployment started (mock)'
        }
    }


def get_appliance_status(base_uri, username, password, appliance_id, timeout):
    """Get appliance deployment status (mock)."""
    return {
        'changed': False,
        'result': {
            'id': appliance_id,
            'status': 'COMPLETED',
            'progress': 100,
            'message': 'Appliance deployment completed successfully (mock)',
            'health': 'HEALTHY'
        }
    }


def validate_registration(base_uri, username, password, appliance_id, timeout):
    """Validate appliance registration (mock)."""
    return {
        'changed': False,
        'result': {
            'applianceId': appliance_id,
            'vcenterRegistered': True,
            'nsxRegistered': True,
            'status': 'REGISTERED',
            'message': 'Appliance registration validated successfully (mock)'
        }
    }


def get_fleet_status(base_uri, username, password, timeout):
    """Get fleet layer status (mock)."""
    return {
        'changed': False,
        'result': {
            'status': 'HEALTHY',
            'appliances': [
                {
                    'id': 'mock-automation-1',
                    'name': 'vcf-automation',
                    'type': 'VCF_AUTOMATION',
                    'status': 'HEALTHY'
                },
                {
                    'id': 'mock-operations-1',
                    'name': 'vcf-operations',
                    'type': 'VCF_OPERATIONS',
                    'status': 'HEALTHY'
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
                'deploy_automation',
                'deploy_operations',
                'get_appliance_status',
                'validate_registration',
                'get_fleet_status'
            ]
        ),
        appliance_spec=dict(type='dict', required=False),
        appliance_id=dict(type='str', required=False),
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
    appliance_spec = module.params.get('appliance_spec')
    appliance_id = module.params.get('appliance_id')
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']

    # Log mock operation
    module.log(f"Mock SDDC Manager API - Operation: {operation}")
    module.log(f"Mock SDDC Manager API - Base URI: {base_uri}")
    module.log(f"Mock SDDC Manager API - Username: {username}")

    # Check mode
    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"Would execute operation: {operation} (check mode)"
        )

    # Execute operation
    try:
        if operation == 'deploy_automation':
            if not appliance_spec:
                module.fail_json(msg="appliance_spec is required for deploy_automation operation")
            result = deploy_automation(base_uri, username, password, appliance_spec, timeout)

        elif operation == 'deploy_operations':
            if not appliance_spec:
                module.fail_json(msg="appliance_spec is required for deploy_operations operation")
            result = deploy_operations(base_uri, username, password, appliance_spec, timeout)

        elif operation == 'get_appliance_status':
            if not appliance_id:
                module.fail_json(msg="appliance_id is required for get_appliance_status operation")
            result = get_appliance_status(base_uri, username, password, appliance_id, timeout)

        elif operation == 'validate_registration':
            if not appliance_id:
                module.fail_json(msg="appliance_id is required for validate_registration operation")
            result = validate_registration(base_uri, username, password, appliance_id, timeout)

        elif operation == 'get_fleet_status':
            result = get_fleet_status(base_uri, username, password, timeout)

        else:
            module.fail_json(msg=f"Unknown operation: {operation}")

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Mock SDDC Manager API error: {str(e)}")


if __name__ == '__main__':
    main()
