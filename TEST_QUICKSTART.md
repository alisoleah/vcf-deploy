# Test Environment Quick Start

## What Was Created

✅ **Git Repository Initialized** - Local git repository with branch strategy
✅ **prod Branch** - Production-ready code (current branch: `prod`)
✅ **test Branch** - Test environment with mock modules (current branch: `test`)
✅ **Mock Modules** - `mock_vcf_installer_api.py` and `mock_sddc_manager_api.py`
✅ **Test Configuration** - `inventory/test.ini` and `group_vars/test.yml`
✅ **Test Playbooks** - `site_test.yml` and `05_vcf_deployment_test.yml`
✅ **Documentation** - `TEST_README.md` and `BRANCH_STRATEGY.md`
✅ **Test Vault Template** - `credentials/test/vault.yml.example`

## Current Status

You are currently on the **test** branch.

## Next Steps

### 1. Configure Your Isilon IP

Edit `inventory/test.ini` and replace `YOUR_ISILON_IP_HERE` with your actual Isilon IP address:

```ini
[storage_hosts]
isilon-lab ansible_host=YOUR_ISILON_IP_HERE
```

### 2. Create Test Vault

```bash
# Create vault password file
echo "your-test-vault-password" > credentials/.vault_pass
chmod 600 credentials/.vault_pass

# Copy the example vault file
cp credentials/test/vault.yml.example credentials/test/vault.yml

# Edit and add your real Isilon credentials
ansible-vault edit credentials/test/vault.yml --vault-password-file credentials/.vault_pass
```

Update the vault file with your actual Isilon credentials:
```yaml
isilon_hostname: "your-isilon-hostname"
isilon_username: "root"
isilon_password: "your-real-isilon-password"
```

### 3. Test Storage Preparation

Run the storage preparation playbook to test Isilon integration:

```bash
ansible-playbook -i inventory/test.ini playbooks/02_storage_prep.yml --vault-password-file credentials/.vault_pass
```

This will:
- Connect to your Isilon appliance
- Create NFS exports
- Configure SyncIQ policies (if enabled)
- Validate the configuration

### 4. Test Mock Deployment

Run the mock deployment playbook to test VCF deployment workflow:

```bash
ansible-playbook -i inventory/test.ini playbooks/05_vcf_deployment_test.yml --vault-password-file credentials/.vault_pass
```

This will:
- Validate the deployment specification
- Submit mock deployment
- Monitor mock task status
- Return success without actual API calls

### 5. Run Full Test Workflow

Run the complete test workflow:

```bash
ansible-playbook -i inventory/test.ini playbooks/site_test.yml --vault-password-file credentials/.vault_pass
```

This will:
- Run storage preparation (real Isilon)
- Generate VCF payload
- Run mock deployment
- Display test summary

## Branch Management

### Switch to Production Branch

```bash
git checkout prod
```

### Switch to Test Branch

```bash
git checkout test
```

### View Branches

```bash
git branch -a
```

### View Commit History

```bash
git log --oneline --all
```

## Push to GitHub (Optional)

If you want to push to GitHub:

```bash
# Create GitHub repository
gh repo create vcf-automation-framework --private --source=.

# Push both branches
git push -u origin prod
git push -u origin test
```

## AWX Integration

To integrate with AWX:

1. Create AWX project pointing to this repository
2. Set branch to `test`
3. Configure inventory with your Isilon
4. Add vault password credential
5. Create job templates for test playbooks

See `TEST_README.md` for detailed AWX setup instructions.

## Documentation

- **TEST_README.md** - Complete test environment documentation
- **BRANCH_STRATEGY.md** - Git branch strategy and workflow
- **RUNBOOK.md** - Production deployment runbook
- **README.md** - General framework information

## Support

For issues or questions:
- Check `TEST_README.md` for troubleshooting
- Review `BRANCH_STRATEGY.md` for branch management
- Refer to `RUNBOOK.md` for deployment procedures
