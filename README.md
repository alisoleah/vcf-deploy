# VCF Automation Framework

Enterprise-grade automation framework for VMware Cloud Foundation (VCF) versions 9.0 and 9.1 deployment using Ansible and Python.

## Overview

This framework provides end-to-end automation for deploying VMware Cloud Foundation, including:

- Physical hardware preparation (BIOS/UEFI, RAID, ESXi installation) via Redfish API
- Dell PowerScale/Isilon storage cluster configuration via OneFS API
- Pre-flight validation (DNS, NTP, network, hardware resources)
- Dynamic VCF deployment specification generation (version-aware for 9.0 and 9.1)
- VCF Installer API interaction for deployment submission and monitoring
- Day 2 operations: VCF Automation and VCF Operations appliance deployment via SDDC Manager API

## Features

- **Version-Aware**: Automatically handles differences between VCF 9.0 and 9.1 API specifications
- **Modular Design**: Role-based architecture for easy maintenance and extensibility
- **Secure**: Ansible Vault integration for credential management
- **Idempotent**: Safe to run multiple times without side effects
- **Containerized**: Ansible Builder support for consistent execution environments
- **Comprehensive Logging**: Detailed logging for troubleshooting and audit trails

## Prerequisites

- Ansible Core 2.15.0 or later
- Python 3.8 or later
- Docker/Podman for execution environment (optional)
- Access to BMC interfaces (iDRAC, iLO, or Redfish-compliant)
- Access to Dell PowerScale/Isilon OneFS API
- VCF Installer appliance deployed and accessible

## Quick Start

### 1. Configure Inventory

Edit `inventory/inventory.ini` to add your hosts:

```ini
[vcf_hosts]
host01 ansible_host=192.168.1.101
host02 ansible_host=192.168.1.102

[bmc_hosts]
bmc01 ansible_host=192.168.0.101
bmc02 ansible_host=192.168.0.102

[storage_hosts]
powerscale ansible_host=192.168.2.100
```

### 2. Configure Variables

Edit `group_vars/main.yml` to set your configuration parameters.

### 3. Configure Credentials

Encrypt credentials for your environment:

```bash
# Create vault password file
echo "your-vault-password" > credentials/.vault_pass

# Encrypt vault file
ansible-vault encrypt credentials/prod/vault.yml --vault-password-file credentials/.vault_pass

# Add your sensitive values
ansible-vault edit credentials/prod/vault.yml --vault-password-file credentials/.vault_pass
```

### 4. Run Deployment

```bash
# Set environment variable
export ANSIBLE_VAULT_PASSWORD_FILE=credentials/.vault_pass

# Run the master playbook
ansible-playbook -i inventory/inventory.ini playbooks/site.yml
```

## Project Structure

```
vcf-automation-framework/
├── ansible.cfg                      # Ansible configuration
├── execution-environment.yml       # Ansible Builder definition
├── requirements.yml                # Ansible collection requirements
├── requirements.txt                # Python dependencies
├── bindep.txt                      # System package dependencies
├── inventory/                       # Inventory files
├── group_vars/                      # Group variables
│   └── main.yml                   # CENTRAL VARIABLE FILE
├── roles/                           # Ansible roles
│   ├── hardware_prep/              # BIOS/RAID/ESXi configuration
│   ├── storage_prep/               # OneFS NFS/SyncIQ configuration
│   ├── preflight_validation/       # DNS/NTP/Network checks
│   ├── vcf_payload_gen/            # JSON generation & validation
│   ├── vcf_deployment/             # API interaction & monitoring
│   └── day2_operations/            # Day 2 appliance deployment
├── playbooks/                       # Playbooks
│   ├── 01_hardware_prep.yml
│   ├── 02_storage_prep.yml
│   ├── 03_preflight_validation.yml
│   ├── 04_vcf_payload_gen.yml
│   ├── 05_vcf_deployment.yml
│   ├── 06_day2_operations.yml
│   └── site.yml                    # Master playbook
├── library/                         # Custom Ansible modules
│   ├── redfish_bios_config.py
│   ├── redfish_raid_config.py
│   ├── onefs_nfs_export.py
│   ├── onefs_synciq.py
│   ├── vcf_installer_api.py
│   └── sddc_manager_api.py
├── templates/                       # Jinja2 templates
│   ├── vcf_deployment_spec_9.0.json.j2
│   └── vcf_deployment_spec_9.1.json.j2
└── credentials/                     # Encrypted vault files
    ├── prod/
    ├── staging/
    └── dev/
```

## Configuration

### Main Configuration (group_vars/main.yml)

All primary variables are centralized in `group_vars/main.yml`. Key sections include:

- **Environment Configuration**: Target environment and VCF version
- **Hardware Configuration**: BMC settings, BIOS/RAID parameters
- **Storage Configuration**: PowerScale/Isilon settings, NFS exports, SyncIQ policies
- **Network Configuration**: VLANs, MTU, DNS, NTP settings
- **VCF Deployment Specification**: SDDC manager, ESXi hosts, NSX, vSAN, vCenter
- **Validation Thresholds**: DNS, NTP, network, hardware resource requirements
- **Logging and Monitoring**: Log levels, polling intervals, timeouts

### Credential Management

Credentials are stored in encrypted vault files organized by environment:

- `credentials/prod/vault.yml` - Production credentials
- `credentials/staging/vault.yml` - Staging credentials
- `credentials/dev/vault.yml` - Development credentials

Each vault contains:
- BMC credentials for each host
- VCF Installer API credentials
- Storage (PowerScale) API credentials
- vCenter credentials (if existing)
- License keys

## Custom Modules

### redfish_bios_config

Configure BIOS/UEFI settings via Redfish API.

**Parameters:**
- `base_uri`: Redfish API base URI
- `username`: Authentication username
- `password`: Authentication password
- `boot_mode`: Boot mode (uefi or bios)
- `virtualization`: Enable/disable virtualization
- `power_management`: Enable/disable power management

### redfish_raid_config

Configure hardware RAID controller settings via Redfish API.

**Parameters:**
- `base_uri`: Redfish API base URI
- `username`: Authentication username
- `password`: Authentication password
- `controller_mode`: RAID mode (raid or hba)
- `cache_policy`: Cache policy (writeback or writethrough)

### onefs_nfs_export

Configure NFS exports on Dell PowerScale/Isilon via OneFS API.

**Parameters:**
- `base_uri`: OneFS API base URI
- `username`: Authentication username
- `password`: Authentication password
- `export_name`: Export name
- `export_path`: File system path
- `clients`: Allowed client networks/hostnames
- `read_only`: Read-only or read-write access
- `state`: present or absent

### onefs_synciq

Configure SyncIQ replication policies on Dell PowerScale/Isilon via OneFS API.

**Parameters:**
- `base_uri`: OneFS API base URI
- `username`: Authentication username
- `password`: Authentication password
- `policy_name`: Policy name
- `source_path`: Source file system path
- `target_host`: Target cluster hostname/IP
- `target_path`: Target file system path
- `target_username`: Target authentication username
- `target_password`: Target authentication password
- `schedule`: Replication schedule
- `enabled`: Enable or disable policy
- `state`: present or absent

### vcf_installer_api

Interact with VCF Installer API for deployment operations.

**Parameters:**
- `base_uri`: VCF Installer API base URI
- `username`: Authentication username
- `password`: Authentication password
- `operation`: API operation (submit_deployment, validate_spec, get_task_status, get_bundles, get_releases)
- `deployment_spec`: VCF deployment specification (JSON)
- `task_id`: Task ID for status queries

### sddc_manager_api

Interact with SDDC Manager API for Day 2 operations.

**Parameters:**
- `base_uri`: SDDC Manager API base URI
- `username`: Authentication username
- `password`: Authentication password
- `operation`: API operation (deploy_automation, deploy_operations, get_appliance_status, validate_registration, get_fleet_status)
- `appliance_spec`: Appliance deployment specification (JSON)
- `appliance_id`: Appliance ID for status queries

## Execution Environment

Build a containerized execution environment using Ansible Builder:

```bash
ansible-builder build -f execution-environment.yml -t vcf-automation-ee:latest
```

Run playbooks in the execution environment:

```bash
ansible-playbook -i inventory/inventory.ini playbooks/site.yml --containerized
```

## Workflow

The framework executes the following phases:

1. **Hardware Preparation**: Configure BIOS/UEFI, RAID, and ESXi installation via Redfish API
2. **Storage Preparation**: Configure NFS exports, netgroups, and SyncIQ policies via OneFS API
3. **Pre-Flight Validation**: Validate DNS, NTP, network connectivity, and hardware resources
4. **VCF Payload Generation**: Generate version-specific deployment specification (9.0 or 9.1)
5. **VCF Deployment**: Submit specification to VCF Installer API and monitor deployment progress
6. **Day 2 Operations**: Deploy VCF Automation and VCF Operations appliances via SDDC Manager API and validate registrations

## Day 2 Operations Configuration

Day 2 operations deploy VCF Automation and VCF Operations appliances to the Fleet layer. These appliances provide advanced automation and operations capabilities for VCF.

### Enabling Day 2 Operations

Day 2 operations are controlled by configuration in `group_vars/main.yml`:

```yaml
vcf_automation:
  enabled: true  # Set to false to skip VCF Automation deployment
  appliance:
    hostname: "{{ vault_vcf_automation_hostname }}"
    ip_address: "{{ vault_vcf_automation_ip }}"
    sizing:
      cpu: 8
      memory_gb: 32
      disk_gb: 200
    license_key: "{{ vault_vcf_automation_license_key }}"

vcf_operations:
  enabled: true  # Set to false to skip VCF Operations deployment
  appliance:
    hostname: "{{ vault_vcf_operations_hostname }}"
    ip_address: "{{ vault_vcf_operations_ip }}"
    sizing:
      cpu: 8
      memory_gb: 32
      disk_gb: 200
    license_key: "{{ vault_vcf_operations_license_key }}"
```

### Skipping Day 2 Operations

To skip Day 2 operations while running the initial deployment:

```yaml
workflow:
  skip_day2_operations: true
```

### Vault Configuration

Add the following to your vault file:

```yaml
vcf_automation:
  hostname: "vcf-automation.example.com"
  ip_address: "192.168.1.201"
  cpu: 8
  memory: 32
  disk: 200
  license_key: "{{ vault_vcf_automation_license_key }}"
  portgroup: "Management Network"

vcf_operations:
  hostname: "vcf-operations.example.com"
  ip_address: "192.168.1.202"
  cpu: 8
  memory: 32
  disk: 200
  license_key: "{{ vault_vcf_operations_license_key }}"
  portgroup: "Management Network"
```

### Running Day 2 Operations Separately

You can run Day 2 operations independently after the initial VCF deployment:

```bash
ansible-playbook -i inventory/inventory.ini playbooks/06_day2_operations.yml
```

## VCF Version Differences

### VCF 9.0
- Basic workflow types: VCF, VCF_EXTEND, VCF_COMPLETE
- Limited LACP networking support
- Basic convergence support

### VCF 1.1
- Enhanced workflow types for fleet management
- Improved LACP/LAG configuration
- Extended `useExistingDeployment` properties
- New `vcfOperationsSpec` and `vcfAutomationSpec` sections
- Enhanced `nsxtSpec` with additional networking parameters
- Support for custom internal CIDR blocks

## Troubleshooting

### Common Issues

**Redfish API Connection Failed**
- Verify BMC IP address and credentials
- Check firewall rules allowing access to BMC ports
- Ensure BMC supports Redfish API

**OneFS API Authentication Failed**
- Verify PowerScale hostname and credentials
- Check API port (default: 8080)
- Ensure OneFS Platform API is enabled

**VCF Installer API Connection Failed**
- Verify VCF Installer appliance is accessible
- Check API credentials (default: admin@local)
- Ensure VCF Installer is in ready state

**Validation Failures**
- Check DNS and NTP server connectivity
- Verify network MTU settings
- Ensure hardware meets minimum requirements

**SDDC Manager API Connection Failed**
- Verify SDDC Manager is accessible and in ready state
- Check API credentials (same as VCF admin credentials)
- Ensure SDDC Manager API port (443) is accessible
- Verify SDDC Manager hostname resolution

**Day 2 Appliance Deployment Failed**
- Check vCenter resource availability (CPU, memory, disk)
- Verify network portgroup exists and is accessible
- Ensure license keys are valid and not expired
- Check Fleet layer capacity

**Registration Validation Failed**
- Appliances may take time to initialize (retry logic is built-in)
- Verify vCenter and NSX endpoints are accessible from appliances
- Check network connectivity between appliances and management components
- Ensure registration endpoints are available in SDDC Manager API

### Logging

Logs are written to:
- Ansible log: `./logs/ansible.log` (configured in ansible.cfg)
- Module logs: Output to console and JSON format

## Contributing

When contributing to this framework:

1. Follow the existing code style and structure
2. Add comprehensive documentation for new features
3. Include error handling and logging in custom modules
4. Test changes in multiple environments before submitting
5. Update this README with any new features or breaking changes

## License

This project is proprietary and confidential. All rights reserved.

## Support

For issues or questions, please contact the VCF Automation Framework team.
