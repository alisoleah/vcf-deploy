# VCF Automation Framework - Complete Runbook

## Overview

This runbook provides step-by-step instructions for deploying VMware Cloud Foundation (VCF) versions 9.0 and 9.1 using the Ansible-based automation framework. The framework automates the entire deployment lifecycle from hardware preparation through Day 2 operations.

---

## Prerequisites

### System Requirements
- **Ansible Core**: 2.15.0 or later
- **Python**: 3.8 or later
- **Docker/Podman**: For execution environment (optional but recommended)
- **Operating System**: Linux (Rocky Linux 9 recommended for EE) or Windows with WSL2

### Infrastructure Requirements
- **BMC Access**: iDRAC, iLO, or Redfish-compliant management interfaces for all physical servers
- **Storage**: Dell PowerScale/Isilon cluster with OneFS API access
- **VCF Installer**: VCF Installer appliance deployed and accessible
- **Network**: Management, vSAN, vMotion, vSphere, and NSX VLANs configured
- **DNS/NTP**: Configured and accessible from all hosts

### Software to Install
```bash
# Install Ansible Core
pip install ansible-core>=2.15.0

# Install Python dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml

# Optional: Install Ansible Builder for execution environment
pip install ansible-builder
```

---

## Step 1: Initial Setup

### 1.1 Clone or Navigate to Project
```bash
cd C:\Users\galala\vcf-automation-framework
```

### 1.2 Create Required Directories
```bash
mkdir -p logs
mkdir -p retry
mkdir -p credentials/prod
mkdir -p credentials/staging
mkdir -p credentials/dev
```

### 1.3 Verify Project Structure
Ensure the following directories exist:
- `inventory/` - Host inventory files
- `group_vars/` - Configuration variables
- `roles/` - Ansible roles
- `playbooks/` - Playbook files
- `library/` - Custom Ansible modules
- `templates/` - Jinja2 templates
- `credentials/` - Encrypted vault files

---

## Step 2: Configure Inventory

### 2.1 Edit Inventory File
Edit `inventory/inventory.ini` to add your hosts:

```ini
[vcf_hosts]
host01 ansible_host=192.168.1.101
host02 ansible_host=192.168.1.102
host03 ansible_host=192.168.1.103
host04 ansible_host=192.168.1.104

[bmc_hosts]
bmc01 ansible_host=192.168.0.101
bmc02 ansible_host=192.168.0.102
bmc03 ansible_host=192.168.0.103
bmc04 ansible_host=192.168.0.104

[storage_hosts]
powerscale ansible_host=192.168.2.100

[vcf_installer]
vcf-installer ansible_host=192.168.1.200
```

### 2.2 Configure SSH Access
Ensure SSH keys are set up for passwordless access to hosts:
```bash
# Generate SSH key if not exists
ssh-keygen -t rsa -b 4096

# Copy to hosts
ssh-copy-id root@192.168.1.101
ssh-copy-id root@192.168.1.102
# ... repeat for all hosts
```

---

## Step 3: Configure Variables

### 3.1 Edit Main Configuration
Edit `group_vars/main.yml` to set your environment parameters:

**Key Sections to Configure:**

1. **Environment Configuration** (lines 9-10)
   ```yaml
   vcf_environment: "production"  # or staging, development
   vcf_version: "9.1"  # or 9.0
   ```

2. **Workflow Configuration** (lines 26-32)
   ```yaml
   workflow:
     type: "VCF"  # Options: VCF, VCF_EXTEND, VCF_COMPLETE
     skip_preflight: false
     skip_hardware_prep: false
     skip_storage_prep: false
     skip_day2_operations: false
     dry_run: false
   ```

3. **Hardware Configuration** (lines 37-50)
   ```yaml
   hardware:
     bmc_type: "idrac"  # or ilo, redfish
     bios:
       boot_mode: "uefi"
       virtualization: true
     raid:
       controller_mode: "raid"
       cache_policy: "writeback"
   ```

4. **Network Configuration** (lines 84-108)
   - Management VLAN, MTU, gateway
   - DNS and NTP servers
   - vSAN, vMotion, vSphere, NSX VLANs

5. **VCF Deployment Specification** (lines 113-132)
   - Domain name
   - SDDC Manager hostname/IP
   - ESXi host count
   - License keys (referenced from vault)

6. **Day 2 Operations** (lines 148-180)
   - VCF Automation appliance configuration
   - VCF Operations appliance configuration
   - Set `enabled: false` to skip

### 3.2 Validation Thresholds
Review and adjust validation thresholds in `group_vars/main.yml` (lines 196-209):
- DNS timeout and required servers
- NTP max offset
- Network ping settings
- Hardware minimum requirements

---

## Step 4: Configure Credentials

### 4.1 Create Vault Password File
```bash
# Create vault password file
echo "your-secure-vault-password" > credentials/.vault_pass
chmod 600 credentials/.vault_pass
```

### 4.2 Create Vault File
```bash
# Create vault file for your environment
ansible-vault create credentials/prod/vault.yml --vault-password-file credentials/.vault_pass
```

### 4.3 Add Credentials to Vault
Edit the vault file and add the following structure:

```yaml
---
# VCF Installer Credentials
vcf_installer_hostname: "vcf-installer.example.com"
vcf_installer_ip: "192.168.1.200"
vcf_installer_username: "admin@local"
vcf_installer_password: "your-vcf-installer-password"

# BMC Credentials (for each host)
bmc_credentials:
  bmc01:
    username: "root"
    password: "your-bmc-password"
  bmc02:
    username: "root"
    password: "your-bmc-password"
  # ... repeat for all BMC hosts

# Storage Credentials
powerscale_hostname: "powerscale.example.com"
powerscale_username: "root"
powerscale_password: "your-powerscale-password"

# Network Configuration
mgmt_vlan: 100
mgmt_netmask: "255.255.255.0"
mgmt_gateway: "192.168.1.1"
vsan_vlan: 101
vmotion_vlan: 102
vsphere_vlan: 103
nsx_vlan: 104

# DNS and NTP
dns_server_1: "8.8.8.8"
dns_server_2: "8.8.4.4"
ntp_server_1: "time.google.com"
ntp_server_2: "time.cloudflare.com"

# VCF Deployment
domain_name: "vcf.local"
sddc_manager_hostname: "sddc-manager.vcf.local"
sddc_manager_ip: "192.168.1.10"
vcf_admin_password: "your-secure-admin-password"
esxi_root_password: "your-esxi-root-password"

# License Keys
nsx_license_key: "your-nsx-license-key"
vsan_license_key: "your-vsan-license-key"
vcenter_license_key: "your-vcenter-license-key"

# Day 2 Operations (if enabled)
vcf_automation_hostname: "vcf-automation.vcf.local"
vcf_automation_ip: "192.168.1.201"
vcf_automation_cpu: 8
vcf_automation_memory: 32
vcf_automation_disk: 200
vcf_automation_license_key: "your-vcf-automation-license"
vcf_automation_portgroup: "Management Network"

vcf_operations_hostname: "vcf-operations.vcf.local"
vcf_operations_ip: "192.168.1.202"
vcf_operations_cpu: 8
vcf_operations_memory: 32
vcf_operations_disk: 200
vcf_operations_license_key: "your-vcf-operations-license"
vcf_operations_portgroup: "Management Network"

# SyncIQ Target
synciq_target_host: "backup-powerscale.example.com"

# Certificate Information
cert_state: "California"
cert_locality: "Palo Alto"
cert_organization: "Your Company"
```

### 4.4 Verify Vault
```bash
# Verify vault can be decrypted
ansible-vault view credentials/prod/vault.yml --vault-password-file credentials/.vault_pass
```

---

## Step 5: Build Execution Environment (Optional but Recommended)

### 5.1 Install Ansible Builder
```bash
pip install ansible-builder
```

### 5.2 Build Container Image
```bash
ansible-builder build -f execution-environment.yml -t vcf-automation-ee:latest
```

### 5.3 Verify Image
```bash
docker images | grep vcf-automation-ee
```

---

## Step 6: Pre-Deployment Validation

### 6.1 Test Inventory Connectivity
```bash
# Test connectivity to all hosts
ansible -i inventory/inventory.ini all -m ping

# Test with vault
export ANSIBLE_VAULT_PASSWORD_FILE=credentials/.vault_pass
ansible -i inventory/inventory.ini all -m ping
```

### 6.2 Verify Variable Syntax
```bash
# Check for syntax errors in playbooks
ansible-playbook playbooks/site.yml --syntax-check
```

### 6.3 Dry Run (Optional)
Set `workflow.dry_run: true` in `group_vars/main.yml` to test without making changes.

---

## Step 7: Execute Deployment

### 7.1 Set Environment Variable
```bash
# Linux/Mac
export ANSIBLE_VAULT_PASSWORD_FILE=credentials/.vault_pass

# Windows PowerShell
$env:ANSIBLE_VAULT_PASSWORD_FILE="credentials\.vault_pass"
```

### 7.2 Run Full Deployment
```bash
# Run master playbook
ansible-playbook -i inventory/inventory.ini playbooks/site.yml

# Or with execution environment
ansible-playbook -i inventory/inventory.ini playbooks/site.yml --containerized
```

### 7.3 Run Individual Phases

If you need to run specific phases separately:

**Hardware Preparation Only:**
```bash
ansible-playbook -i inventory/inventory.ini playbooks/01_hardware_prep.yml
```

**Storage Preparation Only:**
```bash
ansible-playbook -i inventory/inventory.ini playbooks/02_storage_prep.yml
```

**Pre-Flight Validation Only:**
```bash
ansible-playbook -i inventory/inventory.ini playbooks/03_preflight_validation.yml
```

**VCF Payload Generation Only:**
```bash
ansible-playbook -i inventory/inventory.ini playbooks/04_vcf_payload_gen.yml
```

**VCF Deployment Only:**
```bash
ansible-playbook -i inventory/inventory.ini playbooks/05_vcf_deployment.yml
```

**Day 2 Operations Only:**
```bash
ansible-playbook -i inventory/inventory.ini playbooks/06_day2_operations.yml
```

### 7.4 Skip Specific Phases

Modify `group_vars/main.yml` to skip phases:
```yaml
workflow:
  skip_hardware_prep: true  # Skip if already configured
  skip_storage_prep: true   # Skip if already configured
  skip_preflight: true      # Skip if already validated
  skip_day2_operations: true # Skip Day 2 operations
```

---

## Step 8: Monitor Deployment

### 8.1 Check Logs
```bash
# View Ansible log
tail -f logs/ansible.log
```

### 8.2 Monitor Task Progress
The framework includes built-in polling logic for:
- VCF Installer API task status
- SDDC Manager API appliance deployment status
- Registration validation status

### 8.3 Check Deployment Status
The framework will display progress during execution. Key milestones:
- Hardware configuration completed
- Storage configuration completed
- Pre-flight validation passed
- VCF payload generated
- VCF deployment submitted
- VCF deployment in progress
- Day 2 appliances deployed (if enabled)

---

## Step 9: Post-Deployment Verification

### 9.1 Verify VCF Deployment
1. Access SDDC Manager UI: `https://<sddc-manager-hostname>`
2. Verify workload domain is deployed
3. Check vCenter, NSX, and vSAN status
4. Verify ESXi hosts are in cluster

### 9.2 Verify Day 2 Operations (if enabled)
1. Check VCF Automation appliance status
2. Check VCF Operations appliance status
3. Verify registration with vCenter and NSX
4. Check Fleet layer health

### 9.3 Review Logs
```bash
# Check for any errors or warnings
grep -i error logs/ansible.log
grep -i warning logs/ansible.log
```

---

## Step 10: Troubleshooting

### Common Issues and Solutions

**Redfish API Connection Failed**
- Verify BMC IP address and credentials in vault
- Check firewall rules allowing access to BMC ports (443, 80)
- Ensure BMC supports Redfish API
- Test with curl: `curl -k https://<bmc-ip>/redfish/v1`

**OneFS API Authentication Failed**
- Verify PowerScale hostname and credentials
- Check API port (default: 8080)
- Ensure OneFS Platform API is enabled
- Test with curl: `curl -k https://<powerscale>:8080/platform/1`

**VCF Installer API Connection Failed**
- Verify VCF Installer appliance is accessible
- Check API credentials (default: admin@local)
- Ensure VCF Installer is in ready state
- Test with curl: `curl -k https://<vcf-installer>/v1`

**Validation Failures**
- Check DNS and NTP server connectivity
- Verify network MTU settings
- Ensure hardware meets minimum requirements
- Review validation thresholds in `group_vars/main.yml`

**SDDC Manager API Connection Failed**
- Verify SDDC Manager is accessible and in ready state
- Check API credentials (same as VCF admin)
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

### Debug Mode
Enable debug logging in `group_vars/main.yml`:
```yaml
logging:
  level: "DEBUG"
```

### Verbose Ansible Output
```bash
ansible-playbook -i inventory/inventory.ini playbooks/site.yml -vvv
```

---

## Step 11: Maintenance and Updates

### 11.1 Update Credentials
```bash
ansible-vault edit credentials/prod/vault.yml --vault-password-file credentials/.vault_pass
```

### 11.2 Update Configuration
Edit `group_vars/main.yml` as needed for configuration changes.

### 11.3 Re-run Specific Phases
For reconfiguration, run specific playbooks:
```bash
# Re-run storage configuration
ansible-playbook -i inventory/inventory.ini playbooks/02_storage_prep.yml

# Re-run Day 2 operations
ansible-playbook -i inventory/inventory.ini playbooks/06_day2_operations.yml
```

### 11.4 Update Execution Environment
```bash
ansible-builder build -f execution-environment.yml -t vcf-automation-ee:latest --force
```

---

## Step 12: Best Practices

### Security
- Never commit vault files to version control
- Use strong vault passwords
- Rotate credentials regularly
- Limit vault file access permissions (chmod 600)
- Use SSH keys instead of passwords for host access

### Version Control
- Keep `group_vars/main.yml` in version control (without secrets)
- Exclude `credentials/` directory from git (already in .gitignore)
- Document configuration changes in commit messages
- Tag releases for major deployments

### Testing
- Test in staging environment before production
- Use dry run mode to validate changes
- Run pre-flight validation before deployment
- Review logs after each deployment

### Monitoring
- Monitor deployment logs for errors
- Set up alerts for deployment failures
- Track deployment time metrics
- Review resource utilization post-deployment

---

## Appendix A: File Reference

### Key Configuration Files
- `inventory/inventory.ini` - Host inventory
- `group_vars/main.yml` - Main configuration variables
- `ansible.cfg` - Ansible configuration
- `execution-environment.yml` - Container EE definition
- `requirements.txt` - Python dependencies
- `requirements.yml` - Ansible collections

### Playbooks
- `playbooks/site.yml` - Master playbook
- `playbooks/01_hardware_prep.yml` - Hardware preparation
- `playbooks/02_storage_prep.yml` - Storage preparation
- `playbooks/03_preflight_validation.yml` - Pre-flight validation
- `playbooks/04_vcf_payload_gen.yml` - VCF payload generation
- `playbooks/05_vcf_deployment.yml` - VCF deployment
- `playbooks/06_day2_operations.yml` - Day 2 operations

### Custom Modules
- `library/redfish_bios_config.py` - BIOS configuration
- `library/redfish_raid_config.py` - RAID configuration
- `library/onefs_nfs_export.py` - NFS export configuration
- `library/onefs_synciq.py` - SyncIQ configuration
- `library/vcf_installer_api.py` - VCF Installer API
- `library/sddc_manager_api.py` - SDDC Manager API

### Templates
- `templates/vcf_deployment_spec_9.0.json.j2` - VCF 9.0 payload template
- `templates/vcf_deployment_spec_9.1.json.j2` - VCF 9.1 payload template

---

## Appendix B: VCF Version Differences

### VCF 9.0
- Basic workflow types: VCF, VCF_EXTEND, VCF_COMPLETE
- Limited LACP networking support
- Basic convergence support
- 5 VCF Installer API operations

### VCF 9.1
- Enhanced workflow types for fleet management
- Improved LACP/LAG configuration
- Extended `useExistingDeployment` properties
- New `vcfOperationsSpec` and `vcfAutomationSpec` sections
- Enhanced `nsxtSpec` with additional networking parameters
- Support for custom internal CIDR blocks
- 10 VCF Installer API operations
- Deferred component deployment support

---

## Appendix C: Quick Reference Commands

```bash
# Set vault password
export ANSIBLE_VAULT_PASSWORD_FILE=credentials/.vault_pass

# Run full deployment
ansible-playbook -i inventory/inventory.ini playbooks/site.yml

# Run with verbose output
ansible-playbook -i inventory/inventory.ini playbooks/site.yml -vvv

# Run specific playbook
ansible-playbook -i inventory/inventory.ini playbooks/03_preflight_validation.yml

# Check inventory
ansible -i inventory/inventory.ini all -m ping

# View vault
ansible-vault view credentials/prod/vault.yml --vault-password-file credentials/.vault_pass

# Edit vault
ansible-vault edit credentials/prod/vault.yml --vault-password-file credentials/.vault_pass

# Build execution environment
ansible-builder build -f execution-environment.yml -t vcf-automation-ee:latest

# Syntax check
ansible-playbook playbooks/site.yml --syntax-check
```

---

## Support

For issues or questions, please contact the VCF Automation Framework team or refer to the project documentation in `README.md` and `DESIGN_DOCUMENT.md`.
