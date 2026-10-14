# VCF Automation Framework - Test Environment Runbook

## Overview

This runbook provides step-by-step instructions for testing the VCF Automation Framework in a lab environment using:
- Real Isilon/PowerScale storage appliance
- Mock VCF Installer and SDDC Manager API modules
- AWX automation platform (optional)
- Laptop with virtualization capability

---

## Prerequisites

### System Requirements
- **Ansible Core**: 2.15.0 or later
- **Python**: 3.8 or later
- **Operating System**: Windows with WSL2 (Ubuntu) or Linux
- **Git**: For branch management

### Infrastructure Requirements
- **Isilon/PowerScale appliance** - Real storage for testing
- **AWX** (optional) - Running on Ubuntu WSL
- **Virtualization** (optional) - VMware Workstation/VirtualBox for ESXi VMs

### Software to Install
```bash
# Install Ansible Core
pip install ansible-core>=2.15.0

# Install Python dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml
```

---

## Step 1: Switch to Test Branch

Ensure you're on the test branch:

```bash
cd /c/Users/galala/vcf-automation-framework
git checkout test
```

Verify current branch:
```bash
git branch
```

---

## Step 2: Configure Test Inventory

### 2.1 Edit Test Inventory File

Edit `inventory/test.ini` and configure your Isilon appliance:

```ini
[storage_hosts]
# Replace with your actual Isilon IP address
isilon-lab ansible_host=YOUR_ISILON_IP_HERE
```

### 2.2 (Optional) Add Virtual ESXi Hosts

If you have virtual ESXi hosts, uncomment and configure:

```ini
[vcf_hosts]
esxi-vm01 ansible_host=192.168.122.101
esxi-vm02 ansible_host=192.168.122.102
```

---

## Step 3: Create Test Vault

### 3.1 Create Vault Password File

```bash
echo "your-secure-test-password" > credentials/.vault_pass
chmod 600 credentials/.vault_pass
```

### 3.2 Create Test Vault File

```bash
# Copy the example vault file
cp credentials/test/vault.yml.example credentials/test/vault.yml

# Edit and add your credentials
ansible-vault edit credentials/test/vault.yml --vault-password-file credentials/.vault_pass
```

### 3.3 Add Your Credentials

Update the vault file with your actual Isilon credentials:

```yaml
---
# Isilon Credentials (REQUIRED - replace with real values)
isilon_hostname: "your-isilon-hostname"
isilon_username: "root"
isilon_password: "your-real-isilon-password"

# Network Configuration (Test Values - can keep defaults)
mgmt_vlan: 100
mgmt_netmask: "255.255.255.0"
mgmt_gateway: "192.168.1.1"
vsan_vlan: 101
vmotion_vlan: 102
vsphere_vlan: 103
nsx_vlan: 104

# DNS and NTP (Test Values - can keep defaults)
dns_server_1: "8.8.8.8"
dns_server_2: "8.8.4.4"
ntp_server_1: "time.google.com"
ntp_server_2: "time.cloudflare.com"

# VCF Deployment (Test Values - can keep defaults)
domain_name: "vcf-test.local"
sddc_manager_hostname: "sddc-manager.vcf-test.local"
sddc_manager_ip: "192.168.1.10"
vcf_admin_password: "TestPassword123!"
esxi_root_password: "TestPassword123!"

# License Keys (Test Values - can keep defaults)
nsx_license_key: "TEST-NSX-LICENSE"
vsan_license_key: "TEST-VSAN-LICENSE"
vcenter_license_key: "TEST-VCENTER-LICENSE"

# Certificate Information (Test Values - can keep defaults)
cert_state: "California"
cert_locality: "Palo Alto"
cert_organization: "Test Company"

# SyncIQ Target (Optional - leave empty if not testing replication)
synciq_target_host: ""
```

### 3.4 Verify Vault

```bash
ansible-vault view credentials/test/vault.yml --vault-password-file credentials/.vault_pass
```

---

## Step 4: Create Required Directories

```bash
mkdir -p logs
mkdir -p retry
```

---

## Step 5: Test Scenario 1 - Storage Preparation

This tests real Isilon integration with actual API calls.

### 5.1 Run Storage Preparation Playbook

```bash
ansible-playbook -i inventory/test.ini playbooks/02_storage_prep.yml --vault-password-file credentials/.vault_pass
```

### 5.2 What This Does

- Connects to your Isilon appliance via OneFS API
- Creates NFS exports for vSAN and vMotion
- Configures SyncIQ replication policies (if enabled)
- Validates storage configuration

### 5.3 Verify Results

1. Log in to your Isilon web interface
2. Check NFS exports under `/ifs/vcf-test`
3. Verify SyncIQ policies if enabled
4. Review logs: `tail -f logs/vcf-automation-test.log`

### 5.4 Troubleshooting

**Connection Failed:**
- Verify Isilon IP in `inventory/test.ini`
- Check Isilon credentials in vault
- Ensure OneFS Platform API is enabled (port 8080)
- Test with: `curl -k https://<isilon-ip>:8080/platform/1`

**Export Creation Failed:**
- Check if export path already exists
- Verify Isilon has sufficient permissions
- Review logs for specific error messages

---

## Step 6: Test Scenario 2 - Payload Generation

This tests VCF JSON payload generation without actual deployment.

### 6.1 Run Payload Generation Playbook

```bash
ansible-playbook -i inventory/test.ini playbooks/04_vcf_payload_gen.yml --vault-password-file credentials/.vault_pass
```

### 6.2 What This Does

- Generates VCF deployment specification JSON
- Uses version-specific templates (9.0 or 9.1)
- Validates JSON structure
- Substitutes variables from configuration

### 6.3 Verify Results

- Check generated JSON in output
- Verify all required fields are present
- Review variable substitution
- Validate against VCF schema

### 6.4 Troubleshooting

**Template Error:**
- Verify template files exist in `templates/`
- Check Jinja2 syntax in templates
- Ensure all required variables are defined

**Variable Error:**
- Check `group_vars/test.yml` for missing variables
- Verify vault variables are accessible
- Review variable references in templates

---

## Step 7: Test Scenario 3 - Mock Deployment

This tests VCF deployment workflow using mock API modules.

### 7.1 Run Mock Deployment Playbook

```bash
ansible-playbook -i inventory/test.ini playbooks/05_vcf_deployment_test.yml --vault-password-file credentials/.vault_pass
```

### 7.2 What This Does

- Validates deployment specification (mock)
- Submits mock deployment to VCF Installer
- Returns mock task ID
- Monitors mock task status
- No actual API calls to VCF Installer

### 7.3 Verify Results

- Check output for mock task ID
- Verify validation passes
- Review mock task status
- Check logs for mock operations

### 7.4 Troubleshooting

**Mock Module Not Found:**
- Verify you're on `test` branch
- Check mock modules are in `library/` directory
- Ensure Ansible library path is correct in `ansible.cfg`

**Validation Failed:**
- Check deployment specification structure
- Verify required fields are present
- Review validation error messages

---

## Step 8: Test Scenario 4 - Full Test Workflow

This runs the complete test workflow with real Isilon and mock VCF components.

### 8.1 Run Full Test Workflow

```bash
ansible-playbook -i inventory/test.ini playbooks/site_test.yml --vault-password-file credentials/.vault_pass
```

### 8.2 What This Does

1. Displays test configuration
2. Runs storage preparation (real Isilon)
3. Generates VCF payload
4. Runs mock deployment
5. Displays test summary

### 8.3 Verify Results

- Check each phase completes successfully
- Review Isilon NFS exports created
- Verify JSON payload generated
- Check mock deployment task status
- Review test summary

### 8.4 Troubleshooting

**Phase Failed:**
- Identify which phase failed
- Review specific phase troubleshooting above
- Check logs for detailed error messages
- Verify configuration for failed phase

---

## Step 9: AWX Integration (Optional)

If you want to use AWX for automation:

### 9.1 Create AWX Project

1. Log in to AWX web interface
2. Navigate to Projects → Add
3. Configure:
   - Name: `vcf-automation-test`
   - SCM Type: Git
   - SCM URL: Your repository URL
   - Branch: `test`
   - Update Strategy: Git Pull

### 9.2 Configure AWX Inventory

1. Navigate to Inventories → Add
2. Name: `vcf-test-inventory`
3. Add hosts:
   - Isilon appliance IP
   - Virtual ESXi hosts (if any)

### 9.3 Configure AWX Credentials

1. Create Vault credential:
   - Type: Ansible Vault
   - Password: Your vault password

2. Create SSH credential (if using ESXi hosts):
   - Type: Machine
   - Username: root
   - SSH Key: Your SSH private key

### 9.4 Create AWX Job Templates

1. **test-storage-prep**
   - Job Type: Run
   - Inventory: vcf-test-inventory
   - Project: vcf-automation-test
   - Playbook: playbooks/02_storage_prep.yml
   - Credentials: Vault + SSH

2. **test-payload-gen**
   - Job Type: Run
   - Inventory: vcf-test-inventory
   - Project: vcf-automation-test
   - Playbook: playbooks/04_vcf_payload_gen.yml
   - Credentials: Vault

3. **test-deployment-mock**
   - Job Type: Run
   - Inventory: vcf-test-inventory
   - Project: vcf-automation-test
   - Playbook: playbooks/05_vcf_deployment_test.yml
   - Credentials: Vault

4. **test-full-workflow**
   - Job Type: Run
   - Inventory: vcf-test-inventory
   - Project: vcf-automation-test
   - Playbook: playbooks/site_test.yml
   - Credentials: Vault + SSH

### 9.5 Create AWX Workflow

1. Navigate to Templates → Workflows → Add
2. Name: `vcf-test-workflow`
3. Add nodes:
   - test-storage-prep
   - test-payload-gen (after storage prep)
   - test-deployment-mock (after payload gen)

### 9.6 Run AWX Workflow

1. Navigate to Workflows
2. Select vcf-test-workflow
3. Click Launch
4. Monitor execution
5. Review job output

---

## Step 10: Review Logs and Results

### 10.1 Check Ansible Logs

```bash
tail -f logs/vcf-automation-test.log
```

### 10.2 Check for Errors

```bash
grep -i error logs/vcf-automation-test.log
grep -i warning logs/vcf-automation-test.log
```

### 10.3 Review Test Results

- Isilon NFS exports created successfully
- JSON payload generated correctly
- Mock deployment completed
- All test scenarios passed

---

## Step 11: Switch to Production (When Ready)

When you're ready to deploy to production:

### 11.1 Switch to Production Branch

```bash
git checkout prod
```

### 11.2 Configure Production Environment

Follow the production RUNBOOK.md for:
- Configure production inventory
- Create production vault
- Run production deployment

---

## Troubleshooting Guide

### Common Issues

**Vault Decryption Failed**
- Verify vault password file exists
- Check vault password is correct
- Ensure vault file is not corrupted

**Isilon Connection Failed**
- Verify Isilon IP in inventory
- Check Isilon credentials in vault
- Ensure OneFS API is enabled
- Test with curl

**Mock Module Not Found**
- Verify you're on test branch
- Check library directory contains mock modules
- Ensure Ansible library path is correct

**Playbook Syntax Error**
- Run syntax check: `ansible-playbook playbooks/site_test.yml --syntax-check`
- Check YAML indentation
- Verify variable references

**AWX Job Failed**
- Check AWX project is pointing to test branch
- Verify inventory configuration
- Ensure credentials are correct
- Review AWX job logs

### Debug Mode

Enable debug logging in `group_vars/test.yml`:

```yaml
logging:
  level: "DEBUG"
```

### Verbose Ansible Output

```bash
ansible-playbook -i inventory/test.ini playbooks/site_test.yml -vvv --vault-password-file credentials/.vault_pass
```

---

## Quick Reference Commands

```bash
# Switch to test branch
git checkout test

# Switch to production branch
git checkout prod

# View branches
git branch -a

# Run storage preparation test
ansible-playbook -i inventory/test.ini playbooks/02_storage_prep.yml --vault-password-file credentials/.vault_pass

# Run payload generation test
ansible-playbook -i inventory/test.ini playbooks/04_vcf_payload_gen.yml --vault-password-file credentials/.vault_pass

# Run mock deployment test
ansible-playbook -i inventory/test.ini playbooks/05_vcf_deployment_test.yml --vault-password-file credentials/.vault_pass

# Run full test workflow
ansible-playbook -i inventory/test.ini playbooks/site_test.yml --vault-password-file credentials/.vault_pass

# View vault
ansible-vault view credentials/test/vault.yml --vault-password-file credentials/.vault_pass

# Edit vault
ansible-vault edit credentials/test/vault.yml --vault-password-file credentials/.vault_pass

# Syntax check
ansible-playbook playbooks/site_test.yml --syntax-check

# View logs
tail -f logs/vcf-automation-test.log
```

---

## Test Scenarios Summary

| Scenario | Command | What It Tests | Infrastructure |
|----------|---------|---------------|---------------|
| Storage Prep | `02_storage_prep.yml` | Real Isilon API integration | Real Isilon |
| Payload Gen | `04_vcf_payload_gen.yml` | JSON generation and validation | None |
| Mock Deployment | `05_vcf_deployment_test.yml` | VCF deployment workflow | Mock VCF |
| Full Workflow | `site_test.yml` | Complete end-to-end test | Real Isilon + Mock VCF |

---

## Documentation Reference

- **TEST_QUICKSTART.md** - Quick start guide
- **TEST_README.md** - Complete test environment documentation
- **BRANCH_STRATEGY.md** - Git branch management
- **RUNBOOK.md** - Production deployment runbook
- **README.md** - General framework information

---

## Support

For test environment issues:
1. Check this runbook's troubleshooting section
2. Review TEST_README.md for detailed documentation
3. Check logs in `./logs/` directory
4. Verify you're on the correct branch (`test`)
