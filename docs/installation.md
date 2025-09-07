# Installation Guide

This guide provides step-by-step instructions for installing and configuring the Comprehensive Toolkit module in your Odoo environment.

## 🔧 System Requirements

### Odoo Version Support
- **Odoo 16.0+** (Primary support)
- **Python 3.8+**
- **PostgreSQL 12+** (recommended)

### Dependencies
The module requires the following Odoo core modules:
- `base` (User management, core functionality)
- `web` (Web interface components)

## 📥 Installation Methods

### Method 1: Manual Installation

1. **Download the Module**
   ```bash
   # Clone from repository
   git clone https://github.com/kaozaza2/comprehensive_toolkit.git
   
   # Or download and extract ZIP file
   ```

2. **Copy to Addons Directory**
   ```bash
   # Copy to your Odoo addons directory
   cp -r comprehensive_toolkit /path/to/odoo/addons/
   
   # Or create symbolic link
   ln -s /path/to/comprehensive_toolkit /path/to/odoo/addons/
   ```

3. **Update Addons Path**
   Ensure your Odoo configuration includes the addons path:
   ```ini
   # In odoo.conf
   addons_path = /path/to/odoo/addons,/path/to/custom/addons
   ```

4. **Restart Odoo Server**
   ```bash
   # Restart with update
   ./odoo-bin -u all -d your_database --stop-after-init
   ./odoo-bin -d your_database
   ```

### Method 2: Docker Installation

1. **Add to Docker Compose**
   ```yaml
   services:
     odoo:
       image: odoo:16.0
       volumes:
         - ./comprehensive_toolkit:/mnt/extra-addons/comprehensive_toolkit
       environment:
         - ADDONS_PATH=/mnt/extra-addons
   ```

2. **Build and Run**
   ```bash
   docker-compose up -d
   ```

### Method 3: Development Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/kaozaza2/comprehensive_toolkit.git
   cd comprehensive_toolkit
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

## ⚙️ Configuration

### 1. Install the Module

1. **Access Odoo Interface**
   - Navigate to **Apps** menu
   - Click **Update Apps List**
   - Search for "Comprehensive Toolkit"
   - Click **Install**

2. **Verify Installation**
   - Check for new menu: **Comprehensive Toolkit**
   - Verify dashboard access
   - Test mixin functionality

### 2. Initial Setup

#### Security Groups Configuration

The module creates three security groups automatically:

1. **Comprehensive Toolkit / Manager**
   - Full access to all features
   - Can manage all logs and configurations
   - Can perform bulk operations

2. **Comprehensive Toolkit / User**
   - Standard user access
   - Can use all mixin features
   - Limited administrative access

3. **Comprehensive Toolkit / Viewer**
   - Read-only access
   - Can view logs and statistics
   - Cannot modify records

#### Assign Users to Groups

1. Navigate to **Settings → Users & Companies → Users**
2. Edit user accounts
3. In **Access Rights** tab, assign appropriate toolkit groups
4. Save changes

### 3. Database Setup

#### Required Tables
The module automatically creates the following tables:
- `tk_ownership_log` - Ownership change tracking
- `tk_assignment_log` - Assignment activity logging
- `tk_access_log` - Access permission changes
- `tk_responsibility_log` - Responsibility tracking
- `tk_accessible_group` - Custom access groups

#### Data Migration (Existing Systems)

If upgrading from a previous version or migrating data:

```python
# Example migration script
def migrate_existing_data(env):
    # Migrate existing ownership data
    existing_records = env['your.existing.model'].search([])
    for record in existing_records:
        if hasattr(record, 'owner_field'):
            record.owner_id = record.owner_field
    
    # Update access levels
    records_to_update = env['your.model'].search([])
    records_to_update.write({'access_level': 'internal'})
```

## 🔐 Security Configuration

### File Permissions
Ensure proper file permissions for the module:
```bash
# Set ownership
chown -R odoo:odoo /path/to/comprehensive_toolkit

# Set permissions
chmod -R 644 /path/to/comprehensive_toolkit
chmod 755 /path/to/comprehensive_toolkit
```

### Database Permissions
Grant necessary database permissions:
```sql
-- Grant permissions to Odoo database user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO odoo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO odoo_user;
```

## 📊 Post-Installation Verification

### 1. Functionality Tests

#### Test Ownership Features
```python
# Create test record
test_record = env['tk.project.task'].create({'name': 'Test Task'})

# Test ownership transfer
test_record.transfer_ownership(other_user.id, reason="Installation test")

# Verify logging
logs = env['tk.ownership.log'].search([('res_id', '=', test_record.id)])
assert len(logs) > 0
```

#### Test Assignment Features
```python
# Test assignment
test_record.assign_to_users([user1.id, user2.id], reason="Test assignment")

# Verify assignment status
assert test_record.assignment_status == 'assigned'
assert user1 in test_record.assigned_user_ids
```

### 2. Dashboard Verification
1. Navigate to **Comprehensive Toolkit → Dashboard**
2. Verify statistics are displaying correctly
3. Check date filters are working
4. Confirm user-specific counters are accurate

### 3. Log Verification
1. Navigate to **Comprehensive Toolkit → Logs**
2. Check all log types are accessible:
   - Ownership Logs
   - Assignment Logs
   - Access Logs
   - Responsibility Logs

## 🚨 Troubleshooting

### Common Installation Issues

#### Module Not Appearing in Apps List
```bash
# Update apps list manually
./odoo-bin -u base -d your_database --stop-after-init

# Check addons path
./odoo-bin --addons-path=/your/path --stop-after-init
```

#### Permission Errors
```bash
# Fix file permissions
sudo chown -R odoo:odoo /path/to/module
sudo chmod -R 755 /path/to/module
```

#### Database Errors
```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'tk_%';

-- Recreate missing tables if needed
```

#### Import Errors
Check Python import paths and dependencies:
```python
# Test imports
try:
    from odoo import models, fields, api
    print("Odoo imports successful")
except ImportError as e:
    print(f"Import error: {e}")
```

### Performance Optimization

#### Database Indexing
```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tk_ownership_log_res_id 
ON tk_ownership_log(model_name, res_id);

CREATE INDEX IF NOT EXISTS idx_tk_assignment_log_date 
ON tk_assignment_log(create_date);
```

#### Cache Configuration
```ini
# In odoo.conf
max_cron_threads = 2
db_maxconn = 64
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
```

## 🔄 Updates and Upgrades

### Updating the Module
```bash
# Pull latest changes
git pull origin main

# Update in Odoo
./odoo-bin -u comprehensive_toolkit -d your_database --stop-after-init
```

### Backup Before Updates
```bash
# Backup database
pg_dump your_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup files
tar -czf module_backup_$(date +%Y%m%d_%H%M%S).tar.gz comprehensive_toolkit/
```

## 📞 Support

If you encounter issues during installation:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review Odoo logs: `/var/log/odoo/odoo.log`
3. Verify system requirements
4. Check GitHub issues: [https://github.com/kaozaza2/comprehensive_toolkit/issues](https://github.com/kaozaza2/comprehensive_toolkit/issues)

---

**Next Steps**: After successful installation, proceed to the [User Guide](user-guide.md) for detailed usage instructions.
