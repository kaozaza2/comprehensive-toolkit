# Installation Guide

## System Requirements

- **Odoo Version**: 16.0 or higher
- **Python**: 3.8+
- **Dependencies**: `base`, `web` (automatically installed)

## Installation Methods

### Method 1: Manual Installation

1. **Download the Module**
   ```bash
   git clone https://github.com/kaozaza2/comprehensive_toolkit.git
   ```

2. **Copy to Addons Directory**
   ```bash
   cp -r comprehensive_toolkit /path/to/odoo/addons/
   ```

3. **Update Apps List**
   - Go to Apps → Update Apps List
   - Search for "Comprehensive Toolkit"
   - Click Install

### Method 2: Development Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/kaozaza2/comprehensive_toolkit.git
   cd comprehensive_toolkit
   ```

2. **Install in Development Mode**
   ```bash
   # Add to Odoo configuration
   --addons-path=/path/to/comprehensive_toolkit,/path/to/other/addons
   ```

3. **Restart Odoo Server**
   ```bash
   ./odoo-bin -u comprehensive_toolkit -d your_database
   ```

## Post-Installation Setup

### 1. Verify Installation

After installation, verify the module is working:

1. Navigate to **Comprehensive Toolkit** menu
2. Check that all submenu items are accessible:
   - Dashboard
   - Example Models
   - Access Management
   - Activity Logs
   - Quick Actions

### 2. Set Up User Permissions

Configure user access levels:

```python
# Basic Users - Can use all mixin functionality
Group: base.group_user

# System Administrators - Full access including log deletion
Group: base.group_system
```

### 3. Configure Security Groups

The module automatically creates security rules for:
- **Regular Users**: Read/Write/Create access to most models
- **System Admins**: Full access including deletion rights
- **Log Protection**: Users cannot delete audit logs (admins can)

### 4. Test Example Models

Test the installation with provided examples:

1. Go to **Comprehensive Toolkit → Example Models → Project Tasks**
2. Create a test task
3. Verify all mixin functionality works:
   - Ownership management
   - Assignment features
   - Access control
   - Responsibility delegation

## Configuration Options

### Database Configuration

No special database configuration required. The module creates its own tables automatically.

### Server Configuration

Add to `odoo.conf` if needed:
```ini
[options]
# No special configuration required for this module
```

### Environment Variables

No special environment variables required.

## Upgrade Instructions

### From Previous Versions

1. **Backup Database**
   ```bash
   pg_dump your_database > backup_before_upgrade.sql
   ```

2. **Update Module Files**
   ```bash
   git pull origin main
   ```

3. **Upgrade Module**
   ```bash
   ./odoo-bin -u comprehensive_toolkit -d your_database
   ```

4. **Verify Upgrade**
   - Check logs for any errors
   - Test key functionality
   - Verify data integrity

### Migration Notes

- **v1.0.0**: Initial release - no migration needed
- **Future versions**: Migration scripts will be provided as needed

## Troubleshooting Installation

### Common Issues

1. **Module Not Found**
   ```
   Error: Module 'comprehensive_toolkit' not found
   ```
   **Solution**: Ensure module is in correct addons path and restart server

2. **Permission Denied**
   ```
   Error: Permission denied accessing models
   ```
   **Solution**: Update apps list and check user groups

3. **Database Migration Errors**
   ```
   Error: Column 'owner_id' already exists
   ```
   **Solution**: Check for conflicting modules with similar fields

### Debug Mode

Enable debug mode to see detailed error messages:
```
http://your-domain/web?debug=1
```

### Log Analysis

Check Odoo logs for installation issues:
```bash
tail -f /var/log/odoo/odoo.log
```

## Uninstallation

### Clean Uninstall

1. **Remove Module Data**
   - Go to Apps → Comprehensive Toolkit
   - Click Uninstall
   - Confirm data removal

2. **Manual Cleanup** (if needed)
   ```sql
   -- Remove module tables (use with caution)
   DROP TABLE IF EXISTS tk_ownership_log CASCADE;
   DROP TABLE IF EXISTS tk_assignment_log CASCADE;
   DROP TABLE IF EXISTS tk_access_log CASCADE;
   DROP TABLE IF EXISTS tk_responsibility_log CASCADE;
   ```

### Keep Data

To uninstall but keep data:
1. Disable the module instead of uninstalling
2. Data will remain in database for future use

## Verification Checklist

After installation, verify:

- [ ] Module appears in Apps list
- [ ] Main menu "Comprehensive Toolkit" is visible
- [ ] Dashboard loads without errors
- [ ] Example models can be created
- [ ] All wizards open correctly
- [ ] Security permissions are working
- [ ] Logs are being created for operations

---

*For installation support, check the [Troubleshooting Guide](troubleshooting.md) or contact support.*
