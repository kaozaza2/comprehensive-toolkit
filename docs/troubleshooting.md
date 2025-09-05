# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Issue: Module Not Found After Installation
**Symptoms:**
- Module doesn't appear in Apps list
- Import errors when trying to use mixins

**Solutions:**
1. **Check Addons Path**
   ```bash
   # Verify module is in correct addons directory
   ls -la /path/to/odoo/addons/comprehensive_toolkit
   ```

2. **Update Apps List**
   - Go to Apps → Update Apps List
   - Search for "Comprehensive Toolkit"
   - If still not found, restart Odoo server

3. **Check Server Logs**
   ```bash
   tail -f /var/log/odoo/odoo.log
   ```
   Look for import errors or missing dependencies

4. **Verify Dependencies**
   ```python
   # Check if base modules are available
   self.env['res.users']  # Should work
   self.env['res.groups']  # Should work
   ```

#### Issue: Database Migration Errors
**Symptoms:**
- Error during module installation
- Tables not created properly
- Field conflicts

**Solutions:**
1. **Check for Conflicting Modules**
   ```sql
   -- Check for existing owner_id fields
   SELECT table_name, column_name 
   FROM information_schema.columns 
   WHERE column_name = 'owner_id';
   ```

2. **Manual Migration**
   ```python
   # In Python console
   env['base'].env.cr.execute("DROP TABLE IF EXISTS tk_ownership_log CASCADE;")
   env['base'].env.cr.commit()
   # Then reinstall module
   ```

3. **Clean Installation**
   - Uninstall module completely
   - Remove all related tables
   - Reinstall from scratch

### Runtime Issues

#### Issue: Permission Denied Errors
**Symptoms:**
```
AccessError: You don't have permission to transfer ownership
```

**Diagnosis:**
```python
# Check user permissions
record = env['your.model'].browse(record_id)
print(f"Can transfer: {record.can_transfer}")
print(f"Current owner: {record.owner_id.name}")
print(f"Current user: {env.user.name}")
print(f"User groups: {env.user.groups_id.mapped('name')}")
```

**Solutions:**
1. **Check Ownership**
   - Only owners can transfer ownership
   - System admins can override

2. **Verify Group Membership**
   ```python
   # Add user to appropriate group
   env.user.groups_id = [(4, env.ref('base.group_system').id)]
   ```

3. **Check Record Rules**
   - Review ir.rule records for the model
   - Ensure rules don't block legitimate access

#### Issue: Assignment Not Working
**Symptoms:**
- Can't assign users to records
- Assignment buttons not visible
- Assignment operations fail silently

**Diagnosis:**
```python
record = env['your.model'].browse(record_id)
print(f"Can assign: {record.can_assign}")
print(f"Is assigned: {record.is_assigned}")
print(f"Assigned users: {record.assigned_user_ids.mapped('name')}")

# Check computed field logic
record._compute_can_assign()
```

**Solutions:**
1. **Check Assignment Logic**
   ```python
   # Override if needed
   @api.depends('owner_id', 'assigned_user_ids')
   def _compute_can_assign(self):
       super()._compute_can_assign()
       for record in self:
           # Add custom logic
           if record.state == 'locked':
               record.can_assign = False
   ```

2. **Verify User Existence**
   ```python
   # Check if users exist and are active
   users = env['res.users'].browse(user_ids)
   print(f"Active users: {users.filtered(lambda u: u.active)}")
   ```

#### Issue: Access Control Not Working
**Symptoms:**
- Users can see records they shouldn't
- Access levels not being respected
- Custom groups not working

**Diagnosis:**
```python
record = env['your.model'].browse(record_id)
user = env['res.users'].browse(user_id)

print(f"Access level: {record.access_level}")
print(f"User has access: {record._check_user_access(user)}")
print(f"Allowed users: {record.allowed_user_ids.mapped('name')}")
print(f"User groups: {user.groups_id.mapped('name')}")
print(f"Allowed groups: {record.allowed_group_ids.mapped('name')}")
```

**Solutions:**
1. **Check Access Logic**
   ```python
   # Debug step by step
   def debug_access(self, user):
       if self.access_level == 'public':
           return True
       elif self.access_level == 'internal':
           return user.has_group('base.group_user')
       elif self.access_level == 'restricted':
           return user in self.allowed_user_ids
       # etc.
   ```

2. **Verify Custom Groups**
   ```python
   # Check custom group setup
   group = env['tk.accessible.group'].browse(group_id)
   print(f"Group active: {group.active}")
   print(f"Group users: {group.user_ids.mapped('name')}")
   ```

### Performance Issues

#### Issue: Slow Computed Field Calculations
**Symptoms:**
- Form views load slowly
- List views take long time to render
- Database queries are slow

**Diagnosis:**
```python
# Profile computed fields
import time
start = time.time()
records._compute_can_assign()
print(f"Computation took: {time.time() - start:.2f} seconds")
```

**Solutions:**
1. **Optimize Computed Fields**
   ```python
   @api.depends('owner_id', 'co_owner_ids')
   def _compute_is_owned_by_me(self):
       # Optimize for batch processing
       user_id = self.env.user.id
       for record in self:
           record.is_owned_by_me = (
               record.owner_id.id == user_id or 
               user_id in record.co_owner_ids.ids
           )
   ```

2. **Add Database Indexes**
   ```python
   owner_id = fields.Many2one('res.users', index=True)
   assignment_deadline = fields.Datetime(index=True)
   ```

3. **Use Search Instead of Compute**
   ```python
   # For simple cases, use search methods
   def _search_is_owned_by_me(self, operator, value):
       if operator == '=' and value:
           return [
               '|', ('owner_id', '=', self.env.user.id),
               ('co_owner_ids', 'in', [self.env.user.id])
           ]
   ```

#### Issue: Memory Usage Problems
**Symptoms:**
- Server runs out of memory
- Large recordsets cause issues
- Batch operations fail

**Solutions:**
1. **Process Records in Batches**
   ```python
   def bulk_transfer_ownership(self, new_owner_id):
       batch_size = 100
       for i in range(0, len(self), batch_size):
           batch = self[i:i+batch_size]
           for record in batch:
               record.transfer_ownership(new_owner_id)
           # Commit after each batch
           self.env.cr.commit()
   ```

2. **Use SQL for Large Operations**
   ```python
   def bulk_update_access_level(self, access_level):
       self.env.cr.execute("""
           UPDATE your_model_table 
           SET access_level = %s 
           WHERE id IN %s
       """, (access_level, tuple(self.ids)))
   ```

### Data Issues

#### Issue: Orphaned Log Records
**Symptoms:**
- Log tables growing very large
- References to deleted records
- Performance degradation

**Diagnosis:**
```sql
-- Check for orphaned logs
SELECT COUNT(*) FROM tk_ownership_log 
WHERE res_id NOT IN (SELECT id FROM your_model_table);
```

**Solutions:**
1. **Clean Up Orphaned Records**
   ```sql
   -- Remove orphaned ownership logs
   DELETE FROM tk_ownership_log 
   WHERE res_id NOT IN (SELECT id FROM your_model_table);
   
   -- Similar for other log tables
   DELETE FROM tk_assignment_log 
   WHERE res_id NOT IN (SELECT id FROM your_model_table);
   ```

2. **Implement Cascade Deletion**
   ```python
   @api.unlink
   def unlink(self):
       # Clean up logs before deletion
       self.env['tk.ownership.log'].search([
           ('model_name', '=', self._name),
           ('res_id', 'in', self.ids)
       ]).unlink()
       return super().unlink()
   ```

#### Issue: Inconsistent Data States
**Symptoms:**
- Records show as assigned but no assigned users
- Ownership dates don't match transfers
- Computed fields show wrong values

**Diagnosis:**
```python
# Check data consistency
records = env['your.model'].search([])
for record in records:
    if record.is_assigned and not record.assigned_user_ids:
        print(f"Inconsistent assignment: {record.name}")
    
    if record.owner_id and not record.ownership_date:
        print(f"Missing ownership date: {record.name}")
```

**Solutions:**
1. **Data Migration Script**
   ```python
   def fix_data_consistency(self):
       # Fix assignment status
       assigned_records = self.search([
           ('assigned_user_ids', '!=', False),
           ('assignment_status', '=', 'unassigned')
       ])
       assigned_records.write({'assignment_status': 'assigned'})
       
       # Fix ownership dates
       owned_records = self.search([
           ('owner_id', '!=', False),
           ('ownership_date', '=', False)
       ])
       owned_records.write({'ownership_date': fields.Datetime.now()})
   ```

2. **Add Data Validation**
   ```python
   @api.constrains('assigned_user_ids', 'assignment_status')
   def _check_assignment_consistency(self):
       for record in self:
           if record.assigned_user_ids and record.assignment_status == 'unassigned':
               raise ValidationError(_("Assignment status inconsistent with assigned users"))
   ```

### Integration Issues

#### Issue: Conflicts with Other Modules
**Symptoms:**
- Field name conflicts
- Method name conflicts
- View inheritance issues

**Solutions:**
1. **Use Different Field Names**
   ```python
   class YourModel(models.Model):
       _inherit = ['your.model', 'tk.ownable.mixin']
       
       # If you already have 'owner_id', use a different name
       record_owner_id = fields.Many2one('res.users', string='Record Owner')
       
       # Override mixin to use your field
       @property
       def owner_id(self):
           return self.record_owner_id
   ```

2. **Customize View Inheritance**
   ```xml
   <record id="view_your_model_form_inherit" model="ir.ui.view">
       <field name="name">your.model.form.inherit</field>
       <field name="model">your.model</field>
       <field name="inherit_id" ref="module.view_your_model_form"/>
       <field name="arch" type="xml">
           <xpath expr="//sheet" position="after">
               <!-- Add mixin tabs here -->
           </xpath>
       </field>
   </record>
   ```

#### Issue: Widget Compatibility
**Symptoms:**
- Many2many widgets not working
- Custom widgets not displaying
- JavaScript errors in browser

**Solutions:**
1. **Use Standard Widgets**
   ```xml
   <!-- Instead of custom widgets, use standard ones -->
   <field name="assigned_user_ids" widget="many2many_tags"/>
   <field name="co_owner_ids" widget="many2many"/>
   ```

2. **Check Odoo Version Compatibility**
   ```xml
   <!-- For older Odoo versions -->
   <field name="progress" widget="percentage"/>
   
   <!-- For newer versions -->
   <field name="progress" widget="progressbar"/>
   ```

## Debugging Tools

### Enable Debug Mode
```python
# In Python console
env['ir.config_parameter'].set_param('base.enable_odoo_debug', True)
```

Or add to URL: `?debug=1`

### Useful SQL Queries

#### Check Mixin Usage
```sql
-- Find models using ownable mixin
SELECT DISTINCT model_name FROM tk_ownership_log;

-- Count operations by model
SELECT model_name, COUNT(*) as operation_count 
FROM tk_ownership_log 
GROUP BY model_name 
ORDER BY operation_count DESC;
```

#### Performance Analysis
```sql
-- Find slow operations
SELECT model_name, action, AVG(EXTRACT(EPOCH FROM (date - LAG(date) OVER (ORDER BY date)))) as avg_duration
FROM tk_ownership_log 
GROUP BY model_name, action;
```

### Python Debugging Snippets

#### Check Field Values
```python
def debug_record(record):
    print(f"Model: {record._name}")
    print(f"ID: {record.id}")
    
    if hasattr(record, 'owner_id'):
        print(f"Owner: {record.owner_id.name if record.owner_id else 'None'}")
        print(f"Can transfer: {record.can_transfer}")
    
    if hasattr(record, 'assigned_user_ids'):
        print(f"Assigned: {record.assigned_user_ids.mapped('name')}")
        print(f"Can assign: {record.can_assign}")
    
    if hasattr(record, 'access_level'):
        print(f"Access level: {record.access_level}")
        print(f"Has access: {record.has_access}")
```

#### Test Permissions
```python
def test_permissions(record, user):
    # Switch to test user
    with record.sudo(user):
        print(f"As {user.name}:")
        print(f"  Can transfer: {record.can_transfer}")
        print(f"  Can assign: {record.can_assign}")
        print(f"  Can delegate: {record.can_delegate}")
        print(f"  Has access: {record.has_access}")
```

## Getting Help

### Log Analysis
1. **Enable Detailed Logging**
   ```python
   import logging
   _logger = logging.getLogger(__name__)
   _logger.setLevel(logging.DEBUG)
   ```

2. **Check Server Logs**
   ```bash
   tail -f /var/log/odoo/odoo.log | grep comprehensive_toolkit
   ```

### Community Support
- **GitHub Issues**: Report bugs and feature requests
- **Odoo Community**: Post questions in forums
- **Documentation**: Check this guide and API reference

### Professional Support
For complex issues or custom implementations:
- Contact module maintainer
- Hire Odoo certified developer
- Consider professional Odoo support

## Prevention Tips

### Code Quality
1. **Always test in development first**
2. **Use version control for customizations**
3. **Document any modifications**
4. **Follow Odoo coding standards**

### Data Management
1. **Regular database backups**
2. **Monitor log table sizes**
3. **Clean up orphaned records**
4. **Test migrations thoroughly**

### Performance
1. **Index frequently searched fields**
2. **Monitor query performance**
3. **Use appropriate batch sizes**
4. **Profile slow operations**

---

*For issues not covered in this guide, check the [GitHub repository](https://github.com/kaozaza2) or contact support.*
