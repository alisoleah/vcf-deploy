# VCF 9.0/9.1 Automation Framework - Design Document

## Executive Summary

This document outlines the design for an enterprise-grade, fully automated end-to-end deployment framework for VMware Cloud Foundation (VCF) versions 9.0 and 9.1. The solution utilizes Ansible (with custom modules, roles, and execution environments) and Python to interact with physical hardware management APIs, storage APIs, and VCF OpenAPI endpoints.

## 1. VCF 9.0 vs 9.1 OpenAPI Differences

### 1.1 VCF Installer API Evolution

**VCF 9.0 (Initial Release):**
- Introduced VCF Installer appliance replacing Cloud Builder
- OpenAPI 3.0.1 specification for VCF Installer
- Initial set of 5 new operations in VCF Installer API
- Core endpoints: `/v1/sddcs`, `/v1/sddcs/validations`, `/v1/tokens`, `/v1/bundles`, `/v1/tasks`

**VCF 9.1 (Enhanced Release):**
- Expanded VCF Installer API with additional 5 new operations
- Enhanced SDK coverage including VCF Operations and VCF Automation
- Unified SDK approach for Python and Java
- Improved error handling and validation endpoints
- New endpoints for fleet management and deferred components

### 1.2 Key API Endpoint Differences

| Endpoint Category | VCF 9.0 | VCF 9.1 | Notes |
|-------------------|---------|---------|-------|
| SDDC Management | `/v1/sddcs` | `/v1/sddcs` + `/v1/sddcs/{id}/spec` | 9.1 adds spec retrieval |
| Validations | `/v1/sddcs/validations` | `/v1/sddcs/validations` + `/v1/sddcs/validations/{id}` + `/v1/sddcs/validations/latest` | 9.1 adds granular validation tracking |
| Bundles | `/v1/bundles` | `/v1/bundles` + `/v1/bundles/{id}` + `/v1/bundles/download-status` | 9.1 adds download monitoring |
| Releases | `/v1/releases` | `/v1/releases` + `/v1/releases/{sku}/release-components` + `/v1/releases/system` | 9.1 adds component tracking |
| VCF Services | `/v1/vcf-services` | `/v1/vcf-services` + `/v1/vcf-services/{id}` | 9.1 adds service-specific operations |
| Deferred Components | Not available | `/v1/system/vcf-management-components` | 9.1 adds deferred deployment support |

### 1.3 JSON Payload Schema Differences

**VCF 9.0 Schema:**
- Basic `workflowType` options: `VCF`, `VCF_EXTEND`, `VCF_COMPLETE`
- Limited LACP networking support through JSON only
- Basic convergence support for existing vSphere

**VCF 9.1 Schema:**
- Enhanced `workflowType` with additional options for fleet management
- Improved LACP/LAG configuration with explicit uplink references
- Extended `useExistingDeployment` properties across all components
- New `vcfOperationsSpec` and `vcfAutomationSpec` sections
- Enhanced `nsxtSpec` with additional networking parameters
- Support for custom internal CIDR blocks (default: 198.18.0.0/15)

## 2. High-Level Deployment Workflow

### 2.1 Deployment Phases

```
Phase 1: Physical Hardware Preparation
├── BIOS/UEFI Configuration (Redfish API)
├── Hardware RAID Configuration (Redfish/OOB API)
├── Network Interface Configuration
└── ESXi Installation via OOB Management

Phase 2: Storage Cluster Preparation
├── Dell PowerScale/Isilon OneFS API Integration
├── NFS Export Configuration
├── Netgroup Setup
├── SyncIQ Replication Policy Configuration
└── Storage Validation

Phase 3: Pre-Flight Validation
├── DNS Resolution Verification
├── NTP Synchronization Check
├── ESXi Host Readiness Validation
├── Network Connectivity Testing
├── Certificate Validation
└── Resource Availability Check

Phase 4: VCF JSON Payload Generation
├── Inventory Data Collection
├── Version-Specific Schema Selection (9.0 vs 9.1)
├── Dynamic JSON Construction
├── Payload Validation
└── Configuration Profile Creation

Phase 5: VCF Deployment Execution
├── VCF Installer API Authentication
├── JSON Payload Submission (POST /v1/sddcs)
├── Deployment Task Initiation
├── Polling Logic for Task Status (GET /v1/tasks/{id})
├── Log Capture and Monitoring
└── Failure Handling and Rollback

Phase 6: VCF Automation and Operations Rollout (Day 2)
├── SDDC Manager API Authentication
├── VCF Automation Appliance Deployment
│   ├── Appliance sizing configuration
│   ├── Network configuration
│   ├── License key assignment
│   └── Deployment monitoring
├── VCF Operations Appliance Deployment
│   ├── Appliance sizing configuration
│   ├── Network configuration
│   ├── License key assignment
│   └── Deployment monitoring
└── Registration Validation
    ├── VCF Automation to vCenter registration
    ├── VCF Automation to NSX registration
    └── Fleet layer status verification
```

## 3. Proposed Ansible Directory Structure

The project structure has been implemented as per the design document. See the actual directory structure in the repository.

## 4. Required Python Dependencies

See `requirements.txt` for the complete list of Python dependencies.

## 5. Execution Environment Configuration

See `execution-environment.yml` for the Ansible Builder configuration.

## 6. Credential Management Strategy

Credentials are managed using Ansible Vault with environment-specific encrypted vault files in the `credentials/` directory.

## 7. SDDC Manager API Integration (Day 2 Operations)

### 7.1 SDDC Manager API Overview

The SDDC Manager API is different from the VCF Installer API and is used for Day 2 operations:

- **Base URL**: `https://<sddc-manager>/v1`
- **Authentication**: Uses SDDC Manager admin credentials (same as VCF admin)
- **Fleet Endpoints**: `/v1/fleet`, `/v1/vcf-automation`, `/v1/vcf-operations`
- **Registration Endpoints**: `/v1/vcf-automation/{id}/registration`, `/v1/vcf-operations/{id}/registration`

### 7.2 SDDC Manager API Operations

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| Deploy VCF Automation | POST `/v1/vcf-automation` | Deploy VCF Automation appliance to Fleet layer |
| Deploy VCF Operations | POST `/v1/vcf-operations` | Deploy VCF Operations appliance to Fleet layer |
| Get Appliance Status | GET `/v1/vcf-automation/{id}` or `/v1/vcf-operations/{id}` | Check appliance deployment status |
| Validate Registration | GET `/v1/vcf-automation/{id}/registration` | Validate VCF Automation registration with vCenter/NSX |
| Get Fleet Status | GET `/v1/fleet` | Get overall Fleet layer health status |

### 7.3 Day 2 Appliance Configuration

Appliance sizing and networking are parameterized in `group_vars/main.yml`:

```yaml
vcf_automation:
  enabled: true
  appliance:
    hostname: "{{ vault_vcf_automation_hostname }}"
    ip_address: "{{ vault_vcf_automation_ip }}"
    netmask: "{{ vault_mgmt_netmask }}"
    gateway: "{{ network.management.gateway }}"
    sizing:
      cpu: "{{ vault_vcf_automation_cpu | default(8) }}"
      memory_gb: "{{ vault_vcf_automation_memory | default(32) }}"
      disk_gb: "{{ vault_vcf_automation_disk | default(200) }}"
    license_key: "{{ vault_vcf_automation_license_key }}"
  networking:
    portgroup: "{{ vault_vcf_automation_portgroup }}"
  registration:
    vcenter: "{{ vcf_deployment.sddc_manager.hostname }}"
    nsx: "{{ vcf_deployment.sddc_manager.hostname }}"
```

### 7.4 Registration Validation

After appliance deployment, the framework validates:
- VCF Automation registration with vCenter
- VCF Automation registration with NSX
- Fleet layer health status

Registration validation includes retry logic with configurable delays to accommodate appliance initialization time.
