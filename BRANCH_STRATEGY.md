# Branch Strategy

## Overview

This repository uses Git branches to separate production and test environments, ensuring clean isolation between production-ready code and test-specific customizations.

## Branches

### `prod` Branch
- **Purpose**: Production-ready code for actual VCF deployments
- **Stability**: Stable, tested code
- **Usage**: Deployed to production environments
- **Contents**:
  - Production inventory configuration
  - Production variables and credentials
  - Real VCF Installer and SDDC Manager API modules
  - Complete deployment playbooks
  - No test-specific modifications

### `test` Branch
- **Purpose**: Test environment for lab testing with Isilon and AWX
- **Stability**: Development/testing code
- **Usage**: Lab testing, development, validation
- **Contents**:
  - Test inventory with Isilon configuration
  - Test variables with simulation mode
  - Mock VCF Installer and SDDC Manager API modules
  - Test-specific playbooks
  - AWX integration configuration

## Branch Structure

```
vcf-automation-framework/
├── prod/                    # Production branch
│   ├── inventory/
│   │   └── inventory.ini    # Production inventory
│   ├── group_vars/
│   │   └── main.yml         # Production config
│   ├── credentials/
│   │   └── prod/            # Production credentials
│   ├── library/
│   │   ├── vcf_installer_api.py      # Real module
│   │   └── sddc_manager_api.py       # Real module
│   └── playbooks/
│       └── site.yml         # Production playbook
│
└── test/                    # Test branch
    ├── inventory/
    │   ├── inventory.ini    # Production inventory (inherited)
    │   └── test.ini         # Test inventory
    ├── group_vars/
    │   ├── main.yml         # Production config (inherited)
    │   └── test.yml         # Test config
    ├── credentials/
    │   ├── prod/            # Production credentials (inherited)
    │   └── test/            # Test credentials
    ├── library/
    │   ├── vcf_installer_api.py      # Real module (inherited)
    │   ├── sddc_manager_api.py       # Real module (inherited)
    │   ├── mock_vcf_installer_api.py  # Mock module (test only)
    │   └── mock_sddc_manager_api.py   # Mock module (test only)
    ├── playbooks/
    │   ├── site.yml         # Production playbook (inherited)
    │   └── site_test.yml    # Test playbook
    └── TEST_README.md        # Test documentation
```

## Workflow

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout prod
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Develop your feature on the feature branch
   - Test locally

3. **Test on Test Branch**
   ```bash
   git checkout test
   git merge feature/your-feature
   # Run test scenarios
   ```

4. **Merge to Production**
   ```bash
   git checkout prod
   git merge feature/your-feature
   # After validation
   ```

5. **Clean Up**
   ```bash
   git branch -d feature/your-feature
   ```

### Testing Workflow

1. **Switch to Test Branch**
   ```bash
   git checkout test
   ```

2. **Configure Test Environment**
   - Edit `inventory/test.ini`
   - Create `credentials/test/vault.yml`
   - Configure Isilon credentials

3. **Run Test Scenarios**
   ```bash
   # Storage preparation test
   ansible-playbook -i inventory/test.ini playbooks/02_storage_prep.yml

   # Payload generation test
   ansible-playbook -i inventory/test.ini playbooks/04_vcf_payload_gen.yml

   # Mock deployment test
   ansible-playbook -i inventory/test.ini playbooks/05_vcf_deployment_test.yml

   # Full test workflow
   ansible-playbook -i inventory/test.ini playbooks/site_test.yml
   ```

4. **Validate Results**
   - Check Isilon NFS exports
   - Review generated JSON payloads
   - Verify mock API responses
   - Check logs in `./logs/`

### Production Deployment Workflow

1. **Switch to Production Branch**
   ```bash
   git checkout prod
   ```

2. **Configure Production Environment**
   - Edit `inventory/inventory.ini`
   - Create `credentials/prod/vault.yml`
   - Configure production credentials

3. **Run Production Deployment**
   ```bash
   ansible-playbook -i inventory/inventory.ini playbooks/site.yml
   ```

## Merging Guidelines

### Safe Merges

✅ **Feature → Test**
- New features should be tested on test branch first
- Validate with mock components
- Test with real Isilon if applicable

✅ **Feature → Prod**
- After successful testing on test branch
- Code review completed
- No test-specific code included

✅ **Prod → Test**
- Sync production fixes to test branch
- Keep test branch up to date
- Ensure compatibility with test environment

### Never Merge

❌ **Test → Prod**
- Test-specific code should never go to production
- Mock modules should not be in production
- Test configuration should not be in production

❌ **Test-Specific Files to Prod**
- `inventory/test.ini`
- `group_vars/test.yml`
- `library/mock_*.py`
- `playbooks/*_test.yml`
- `credentials/test/`

## Cherry-Picking

If you need to move specific changes from test to prod:

```bash
# Get the commit hash from test branch
git log test

# Cherry-pick specific commits to prod
git checkout prod
git cherry-pick <commit-hash>
```

Use this for:
- Bug fixes that apply to both environments
- Configuration improvements
- Documentation updates

## GitHub Integration

### Setting Up GitHub Repository

1. **Create GitHub Repository**
   ```bash
   gh repo create vcf-automation-framework --private --source=.
   ```

2. **Push Branches**
   ```bash
   git push -u origin prod
   git push -u origin test
   ```

3. **Set Default Branch**
   - Go to repository Settings → Branches
   - Set default branch to `prod`

### Pull Requests

1. **Create Pull Request**
   - From feature branch to test branch
   - For testing and validation

2. **After Test Validation**
   - Create PR from test to prod (only for production-ready code)
   - Or cherry-pick specific commits

## Best Practices

1. **Always Test First**
   - Test on test branch before production
   - Validate with mock components
   - Test with real infrastructure when possible

2. **Keep Branches Clean**
   - Don't merge test-specific code to prod
   - Use feature branches for development
   - Delete merged feature branches

3. **Document Changes**
   - Commit messages should be clear
   - Reference issues or tickets
   - Document breaking changes

4. **Regular Syncing**
   - Keep test branch synced with prod
   - Merge prod fixes to test regularly
   - Resolve conflicts promptly

5. **Credential Security**
   - Never commit vault files
   - Use `.gitignore` for sensitive files
   - Rotate credentials regularly

## Troubleshooting

### Branch Conflicts

If you encounter merge conflicts:

```bash
# When merging test to prod
git checkout prod
git merge test
# Resolve conflicts
git add .
git commit
```

### Lost Changes

If you accidentally committed to wrong branch:

```bash
# Create patch from wrong branch
git format-patch -1 <commit-hash>

# Apply to correct branch
git checkout correct-branch
git am <patch-file>
```

### Reset Branch

If you need to reset a branch:

```bash
# Reset to match another branch
git checkout test
git reset --hard prod
```

⚠️ **Warning**: This will discard all changes on the branch

## Summary

- **`prod`** = Production code, stable, deployable
- **`test`** = Test code, development, lab testing
- **Feature branches** = For development work
- **Never merge test → prod** directly
- **Always test before production**
- **Keep credentials secure**
