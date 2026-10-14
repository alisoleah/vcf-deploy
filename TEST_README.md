# VCF Automation Framework - Test Environment

This is the test version of the VCF Automation Framework, customized for lab testing with Isilon storage, AWX automation, and laptop virtualization.

## Branch Strategy

This repository uses Git branches to separate production and test environments:

- **`prod` branch** - Production-ready code for actual VCF deployments
- **`test` branch** - Test environment with mock components and lab-specific configuration

## Test Environment Features

### What's Different from Production

1. **Hardware Preparation** - Skipped (no BMC interfaces in test environment)
2. **Mock VCF Installer** - Uses mock API module instead of real VCF Installer
3. **Mock SDDC Manager** - Uses mock API module instead of real SDDC Manager
4. **Real Isilon Integration** - Actual PowerScale/Isilon API for storage testing
5. **AWX Integration** - Configured for AWX automation platform
6. **Test Configuration** - Separate test inventory and variables
7. **Simulation Mode** - Enabled for testing without actual infrastructure

## Test Scenarios

### Scenario 1: Storage Preparation (Real Isilon)
Test Isilon/PowerScale integration with real API calls.

```bash
ansible-playbook -i inventory/test.ini playbooks/02_storage_prep.yml --vault-password-file credentials/.vault_pass
```

**What it tests:**
- NFS export configuration
- SyncIQ policy setup
- OneFS API authentication
- Storage validation

### Scenario 2: Payload Generation
Test VCF JSON payload generation.

```bash
ansible-playbook -i inventory/test.ini playbooks/04_vcf_payload_gen.yml --vault-password-file credentials/.vault_pass
```

**What it tests:**
- JSON template rendering
- Variable substitution
- VCF 9.0/9.1 schema selection
- Configuration validation

### Scenario 3: Mock Deployment
Test VCF deployment workflow with mock VCF Installer.

```bash
ansible-playbook -i inventory/test.ini playbooks/05_vcf_deployment_test.yml --vault-password-file credentials/.vault_pass
```

**What it tests:**
- VCF Installer API structure
- Deployment specification validation
- Task submission and monitoring
- Error handling

### Scenario 4: Full Test Workflow
Complete end-to-end test with real Isilon and mock VCF components.

```bash
ansible-playbook -i inventory/test.ini playbooks/site_test.yml --vault-password-file credentials/.vault_pass
```

**What it tests:**
- Complete workflow execution
- Integration between components
- Configuration consistency
- Logging and monitoring

## Setup Instructions

### Step 1: Switch to Test Branch

```bash
cd /c/Users/galala/vcf-automation-framework
git checkout test
```

### Step 2: Configure Test Inventory

Edit `inventory/test.ini` and add your Isilon IP:

```ini
[storage_hosts]
isilon-lab ansible_host=YOUR_ISILON_IP_HERE
```

### Step 3: Create Test Vault

```bash
# Create vault password file
echo "your-test-vault-password" > credentials/.vault_pass
chmod 600 credentials/.vault_pass

# Create test vault file
ansible-vault create credentials/test/vault.yml --vault-password-file credentials/.vault_pass
```

Add the following to your test vault:

```yaml
---
# Isilon Credentials
isilon_hostname: "your-isilon-hostname"
isilon_username: "root"
isilon_password: "your-isilon-password"

# Network Configuration (Test Values)
mgmt_vlan: 100
mgmt_netmask: "255.255.255.0"
mgmt_gateway: "192.168.1.1"
vsan_vlan: 101
vmotion_vlan: 102
vsphere_vlan: 103
nsx_vlan: 104

# DNS and NTP (Test Values)
dns_server_1: "8.8.8.8"
dns_server_2: "8.8.4.4"
ntp_server_1: "time.google.com"
ntp_server_2: "time.cloudflare.com"

# VCF Deployment (Test Values)
domain_name: "vcf-test.local"
sddc_manager_hostname: "sddc-manager.vcf-test.local"
sddc_manager_ip: "192.168.1.10"
vcf_admin_password: "TestPassword123!"
esxi_root_password: "TestPassword123!"

# License Keys (Test Values)
nsx_license_key: "TEST-NSX-LICENSE"
vsan_license_key: "TEST-VSAN-LICENSE"
vcenter_license_key: "TEST-VCENTER-LICENSE"

# Certificate Information
cert_state: "California"
cert_locality: "Palo Alto"
cert_organization: "Test Company"

# SyncIQ Target (Optional)
synciq_target_host: ""
```

### Step 4: Create Required Directories

```bash
mkdir -p logs
mkdir -p credentials/test
```

### Step 5: Test Storage Preparation

```bash
ansible-playbook -i inventory/test.ini playbooks/02_storage_prep.yml --vault-password-file credentials/.vault_pass
```

Verify that NFS exports are created on your Isilon appliance.

## AWX Integration

### Setup AWX Project

1. Create a new AWX project pointing to this repository
2. Set the branch to `test`
3. Update strategy: `git pull`

### Configure AWX Inventory

1. Create a new inventory in AWX
2. Add your Isilon appliance as a host
3. Add any virtual ESXi hosts if available

### Configure AWX Credentials

1. Create credential type for Ansible Vault
2. Add your vault password
3. Create SSH credential for test hosts
4. Create machine credential for Isilon API

### Create AWX Job Templates

1. **test-storage-prep**
   - Playbook: `playbooks/02_storage_prep.yml`
   - Inventory: Test inventory
   - Credentials: Vault + SSH

2. **test-payload-gen**
   - Playbook: `playbooks/04_vcf_payload_gen.yml`
   - Inventory: Test inventory
   - Credentials: Vault

3. **test-deployment-mock**
   - Playbook: `playbooks/05_vcf_deployment_test.yml`
   - Inventory: Test inventory
   - Credentials: Vault

4. **test-full-workflow**
   - Playbook: `playbooks/site_test.yml`
   - Inventory: Test inventory
   - Credentials: Vault + SSH

### Create AWX Workflow

Create a workflow that chains the job templates:
1. test-storage-prep
2. test-payload-gen
3. test-deployment-mock

## Mock Modules

### mock_vcf_installer_api.py

Simulates VCF Installer API operations:
- `validate_spec` - Validates deployment specification
- `submit_deployment` - Submits deployment (returns mock task ID)
- `get_task_status` - Returns mock task status
- `get_bundles` - Returns mock bundle list
- `get_releases` - Returns mock release list

### mock_sddc_manager_api.py

Simulates SDDC Manager API operations:
- `deploy_automation` - Deploys VCF Automation appliance (mock)
- `deploy_operations` - Deploys VCF Operations appliance (mock)
- `get_appliance_status` - Returns mock appliance status
- `validate_registration` - Validates appliance registration (mock)
- `get_fleet_status` - Returns mock fleet status

## Limitations

### What Cannot Be Tested

1. **Hardware Preparation** - No BMC interfaces (iDRAC/iLO/Redfish)
2. **Real VCF Deployment** - No VCF Installer appliance
3. **Real SDDC Manager** - No deployed VCF environment
4. **ESXi Configuration** - Unless virtual ESXi hosts are set up
5. **Network Configuration** - No actual VLANs or switches
6. **Day 2 Operations** - No SDDC Manager for appliance deployment

### What Can Be Tested

1. ✅ **Storage Preparation** - Real Isilon API integration
2. ✅ **JSON Payload Generation** - Configuration and template validation
3. ✅ **Deployment Workflow** - Mock API interactions
4. ✅ **Configuration Syntax** - YAML and variable validation
5. ✅ **Playbook Logic** - Workflow execution
6. ✅ **AWX Integration** - Job templates and workflows

## Troubleshooting

### Isilon Connection Failed

- Verify Isilon IP in `inventory/test.ini`
- Check Isilon credentials in vault
- Ensure OneFS Platform API is enabled (port 8080)
- Test with: `curl -k https://<isilon-ip>:8080/platform/1`

### Vault Decryption Failed

- Verify vault password file exists
- Check vault password is correct
- Ensure vault file is not corrupted

### Mock Module Not Found

- Verify you're on the `test` branch
- Check mock modules are in `library/` directory
- Ensure Ansible library path is correct in `ansible.cfg`

### AWX Job Fails

- Check AWX project is pointing to `test` branch
- Verify inventory configuration in AWX
- Ensure credentials are properly configured
- Check AWX job logs for detailed errors

## Switching Between Branches

### To Test Environment

```bash
git checkout test
# Run test playbooks
```

### To Production Environment

```bash
git checkout prod
# Run production playbooks
```

## Contributing

When making changes:

1. Make changes on feature branches
2. Test on `test` branch first
3. After validation, merge to `prod` branch
4. Never merge test-specific code to `prod`

## Support

For test environment issues, refer to:
- Main README.md for general framework information
- RUNBOOK.md for deployment procedures
- DESIGN_DOCUMENT.md for architecture details
