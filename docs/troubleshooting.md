# Troubleshooting Guide

Common issues and solutions for the Comprehensive Toolkit module.

## 🚨 Installation Issues

### Module Not Appearing in Apps List

**Problem**: The Comprehensive Toolkit module doesn't appear in the Apps list after installation.

**Solutions**:
1. **Update Apps List**:
   ```bash
   # Command line
   ./odoo-bin -u base -d your_database --stop-after-init
   
   # Or in Odoo interface
   Apps → Update Apps List
   ```

2. **Check Addons Path**:
   ```bash
   # Verify addons path includes your module directory
   ./odoo-bin --addons-path=/path/to/addons --stop-after-init
   ```

3. **Check Module Structure**:
   - Ensure `__manifest__.py` exists and is valid
   - Verify all required files are present
   - Check file permissions

4. **Check Logs**:
   ```bash
   tail -f /var/log/odoo/odoo.log
   ```

### Import Errors

**Problem**: Module fails to install with import errors.

**Common Error**: `ImportError: No module named 'comprehensive_toolkit'`

**Solutions**:
1. **Check Python Path**:
   ```python
   import sys
   print(sys.path)
   ```

2. **Verify Dependencies**:
   ```python
   # Test basic Odoo imports
   try:
       from odoo import models, fields, api
       print("Odoo imports successful")
   except ImportError as e:
       print(f"Import error: {e}")
   ```

3. **Check Module Dependencies**:
   - Ensure `base` and `web` modules are installed
   - Verify dependency chain in `__manifest__.py`

### Database Errors

**Problem**: Database-related errors during installation.

**Common Errors**:
- `relation "tk_ownership_log" does not exist`
- `column "owner_id" does not exist`

**Solutions**:
1. **Force Module Update**:
   ```bash
   ./odoo-bin -u comprehensive_toolkit -d your_database --stop-after-init
   ```

2. **Check Database Permissions**:
   ```sql
   -- Check if user has necessary permissions
   SELECT * FROM information_schema.role_table_grants 
   WHERE grantee = 'your_odoo_user';
   ```

3. **Manual Table Creation** (if needed):
   ```sql
   -- Check if tables exist
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name LIKE 'tk_%';
   ```

## 🔐 Permission Issues

### AccessError: You Don't Have Permission

**Problem**: Users getting permission denied errors when using toolkit features.

**Solutions**:
1. **Check User Groups**:
   - Navigate to Settings → Users & Companies → Users
   - Verify user has appropriate toolkit groups assigned
   - Add user to "Comprehensive Toolkit / User" group

2. **Check Model Access Rights**:
   ```python
   # Check if user has access to model
   self.env['tk.ownership.log'].check_access_rights('read')
   self.env['tk.ownership.log'].check_access_rights('write')
   ```

3. **Verify Record Rules**:
   - Check if custom record rules are blocking access
   - Review security.xml configuration

### Ownership Transfer Fails

**Problem**: Cannot transfer ownership even when user should have permission.

**Debugging Steps**:
1. **Check Ownership Status**:
   ```python
   record = self.env['your.model'].browse(record_id)
   print(f"Owner: {record.owner_id.name}")
   print(f"Can transfer: {record.can_transfer}")
   print(f"Current user: {self.env.user.name}")
   ```

2. **Verify Permissions**:
   ```python
   # Check if user is owner or has system rights
   is_owner = record.owner_id == self.env.user
   is_system = self.env.user.has_group('base.group_system')
   print(f"Is owner: {is_owner}, Is system: {is_system}")
   ```

### Assignment Permission Denied

**Problem**: Cannot assign records to users.

**Common Causes**:
- User is not owner, co-owner, or already assigned
- Record has restricted access level
- Missing group permissions

**Solutions**:
1. **Check Assignment Permissions**:
   ```python
   print(f"Can assign: {record.can_assign}")
   print(f"Access level: {record.access_level}")
   print(f"User has access: {record.has_access}")
   ```

2. **Grant Necessary Access**:
   ```python
   # Grant access if needed
   if record.access_level == 'restricted':
       record.grant_access([user.id], reason="Assignment access")
   ```

## 🔧 Performance Issues

### Slow Dashboard Loading

**Problem**: Dashboard takes long time to load or times out.

**Solutions**:
1. **Add Database Indexes**:
   ```sql
   -- Add indexes for better performance
   CREATE INDEX IF NOT EXISTS idx_tk_ownership_log_res_id 
   ON tk_ownership_log(model_name, res_id);
   
   CREATE INDEX IF NOT EXISTS idx_tk_assignment_log_date 
   ON tk_assignment_log(create_date);
   
   CREATE INDEX IF NOT EXISTS idx_tk_access_log_user 
   ON tk_access_log(user_id);
   ```

2. **Optimize Date Queries**:
   ```python
   # Use specific date ranges instead of large periods
   def _compute_statistics(self):
       # Instead of searching all records
       recent_date = fields.Date.today() - timedelta(days=30)
       domain = [('create_date', '>=', recent_date)]
   ```

3. **Use Stored Computed Fields**:
   ```python
   # Mark computed fields as stored for better performance
   my_count = fields.Integer('My Count', compute='_compute_count', store=True)
   ```

### Many2many Field Performance

**Problem**: Slow performance when dealing with large co-owner or assignee lists.

**Solutions**:
1. **Limit Related Field Loading**:
   ```python
   # Use specific fields instead of loading all
   co_owners = record.co_owner_ids.with_context(prefetch_fields=False)
   ```

2. **Batch Operations**:
   ```python
   # Instead of individual operations
   for record in records:
       record.add_co_owner(user.id)
   
   # Use bulk operations
   records.write({'co_owner_ids': [(4, user.id)]})
   ```

### Memory Issues with Large Datasets

**Problem**: Out of memory errors when processing many records.

**Solutions**:
1. **Use Batch Processing**:
   ```python
   def process_large_dataset(self):
       batch_size = 100
       offset = 0
       
       while True:
           records = self.search([], limit=batch_size, offset=offset)
           if not records:
               break
               
           # Process batch
           for record in records:
               record.process_toolkit_data()
               
           offset += batch_size
           self.env.cr.commit()  # Commit each batch
   ```

2. **Optimize Queries**:
   ```python
   # Use read() instead of browse() for simple data
   data = self.env['your.model'].read(['owner_id', 'assigned_user_ids'])
   ```

## 🐛 Data Issues

### Missing Log Entries

**Problem**: Actions are not being logged properly.

**Debugging**:
1. **Check Log Method Calls**:
   ```python
   # Verify logging is called
   def transfer_ownership(self, new_owner_id, reason=None):
       # ... ownership logic ...
       self._log_ownership_change('transfer', old_owner, new_owner, reason)
   ```

2. **Check Log Model Access**:
   ```python
   # Test log creation manually
   self.env['tk.ownership.log'].create({
       'model_name': 'test.model',
       'res_id': 1,
       'action': 'test',
       'reason': 'Testing log creation'
   })
   ```

3. **Verify User Permissions**:
   - Ensure user can write to log models
   - Check record rules don't prevent log creation

### Inconsistent Computed Fields

**Problem**: Computed fields showing incorrect values.

**Solutions**:
1. **Force Recomputation**:
   ```python
   # Recompute specific fields
   records._compute_is_owned()
   records._compute_can_assign()
   
   # Or recompute all
   records.recompute()
   ```

2. **Check Dependencies**:
   ```python
   # Ensure @api.depends is correct
   @api.depends('owner_id', 'co_owner_ids')  # Must include all dependencies
   def _compute_is_owned_by_me(self):
       # ...
   ```

3. **Clear Cache**:
   ```python
   # Clear field cache
   records.invalidate_cache(['is_owned', 'can_assign'])
   ```

### Orphaned Records

**Problem**: Records with invalid owner/assignee references.

**Solutions**:
1. **Find Orphaned Records**:
   ```sql
   -- Find records with invalid owner_id
   SELECT * FROM your_table 
   WHERE owner_id NOT IN (SELECT id FROM res_users WHERE active = true);
   ```

2. **Clean Up Data**:
   ```python
   # Remove invalid references
   invalid_records = self.env['your.model'].search([
       ('owner_id.active', '=', False)
   ])
   invalid_records.write({'owner_id': False})
   ```

3. **Prevent Future Issues**:
   ```python
   # Add validation
   @api.constrains('owner_id')
   def _check_owner_active(self):
       for record in self:
           if record.owner_id and not record.owner_id.active:
               raise ValidationError("Cannot assign inactive user as owner")
   ```

## 🔍 Debugging Tools

### Enable Debug Mode

1. **Activate Developer Mode**:
   - Settings → Activate Developer Mode
   - Or add `?debug=1` to URL

2. **Check Field Values**:
   ```python
   # In debug console
   record = env['your.model'].browse(1)
   print(f"Owner: {record.owner_id}")
   print(f"Can transfer: {record.can_transfer}")
   print(f"Access level: {record.access_level}")
   ```

### Custom Debug Methods

Add debugging methods to your models:

```python
class DebugMixin(models.AbstractModel):
    _name = 'debug.mixin'
    
    def debug_toolkit_status(self):
        """Print current toolkit status for debugging"""
        print(f"=== Toolkit Debug Info for {self._name} ID {self.id} ===")
        
        if hasattr(self, 'owner_id'):
            print(f"Owner: {self.owner_id.name if self.owner_id else 'None'}")
            print(f"Co-owners: {', '.join(self.co_owner_ids.mapped('name'))}")
            print(f"Can transfer: {self.can_transfer}")
        
        if hasattr(self, 'assigned_user_ids'):
            print(f"Assigned to: {', '.join(self.assigned_user_ids.mapped('name'))}")
            print(f"Assignment status: {self.assignment_status}")
            print(f"Can assign: {self.can_assign}")
        
        if hasattr(self, 'access_level'):
            print(f"Access level: {self.access_level}")
            print(f"Has access: {self.has_access}")
        
        if hasattr(self, 'responsible_user_ids'):
            print(f"Responsible: {', '.join(self.responsible_user_ids.mapped('name'))}")
            print(f"Can delegate: {self.can_delegate}")
```

### Log Analysis Queries

```sql
-- Most active users (ownership changes)
SELECT u.name, COUNT(*) as change_count
FROM tk_ownership_log ol
JOIN res_users u ON ol.user_id = u.id
WHERE ol.create_date >= NOW() - INTERVAL '30 days'
GROUP BY u.name
ORDER BY change_count DESC;

-- Most transferred models
SELECT model_name, COUNT(*) as transfer_count
FROM tk_ownership_log
WHERE action = 'transfer'
GROUP BY model_name
ORDER BY transfer_count DESC;

-- Overdue assignments
SELECT m.name, al.create_date, al.deadline
FROM tk_assignment_log al
JOIN your_model m ON al.res_id = m.id
WHERE al.deadline < NOW() AND al.status IN ('assigned', 'in_progress');
```

## 📞 Getting Help

### Community Resources

1. **Documentation**: Check all documentation files in the `docs/` folder
2. **GitHub Issues**: Report bugs at [GitHub Repository](https://github.com/kaozaza2/comprehensive_toolkit/issues)
3. **Odoo Community**: Ask questions on Odoo community forums

### Creating Bug Reports

When reporting issues, include:

1. **Environment Information**:
   ```bash
   # Odoo version
   ./odoo-bin --version
   
   # Python version
   python --version
   
   # Module version
   # Check __manifest__.py version field
   ```

2. **Error Details**:
   - Full error message and traceback
   - Steps to reproduce
   - Expected vs actual behavior

3. **System Information**:
   - Operating system
   - Database version (PostgreSQL)
   - Browser (if UI issue)

4. **Logs**:
   ```bash
   # Include relevant log entries
   tail -n 100 /var/log/odoo/odoo.log
   ```

### Emergency Recovery

If the module causes system issues:

1. **Disable Module Temporarily**:
   ```sql
   UPDATE ir_module_module 
   SET state = 'uninstalled' 
   WHERE name = 'comprehensive_toolkit';
   ```

2. **Restore from Backup**:
   ```bash
   # Restore database backup
   dropdb your_database
   createdb your_database
   psql your_database < backup_file.sql
   ```

3. **Safe Mode Start**:
   ```bash
   # Start without custom modules
   ./odoo-bin --addons-path=/odoo/addons -d your_database
   ```

---

**Remember**: Always backup your database before making significant changes or applying fixes!
