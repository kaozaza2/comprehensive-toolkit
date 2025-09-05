# Developer Guide

## Introduction

The Comprehensive Toolkit provides abstract mixins that can be inherited by any Odoo model to add ownership, assignment, access control, and responsibility functionality. This guide explains how to implement and customize these mixins in your own models.

## Core Mixins Overview

### Available Mixins

1. **`tk.ownable.mixin`** - Adds ownership functionality
2. **`tk.assignable.mixin`** - Adds assignment management
3. **`tk.accessible.mixin`** - Adds access control
4. **`tk.responsible.mixin`** - Adds responsibility management
5. **`tk.accessible.group.mixin`** - Enhanced group management

## Quick Implementation

### Basic Example

```python
from odoo import models, fields, api

class MyModel(models.Model):
    _name = 'my.model'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.accessible.mixin',
        'tk.responsible.mixin'
    ]
    
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
```

This gives your model complete ownership, assignment, access control, and responsibility functionality with zero additional code.

## Detailed Implementation Guide

### 1. Ownership Mixin (`tk.ownable.mixin`)

#### Fields Added
```python
owner_id = fields.Many2one('res.users')           # Current owner
co_owner_ids = fields.Many2many('res.users')      # Additional owners
previous_owner_id = fields.Many2one('res.users')  # Last owner
ownership_date = fields.Datetime()                # When ownership started
is_owned = fields.Boolean(compute=True)           # Has owner?
can_transfer = fields.Boolean(compute=True)       # Can current user transfer?
can_release = fields.Boolean(compute=True)        # Can current user release?
can_manage_co_owners = fields.Boolean(compute=True) # Can manage co-owners?
```

#### Methods Available
```python
# Transfer ownership
record.transfer_ownership(new_owner_id, reason="Moving to new team")

# Release ownership
record.release_ownership(reason="No longer needed")

# Claim unowned record
record.claim_ownership(reason="Taking ownership")

# Manage co-owners
record.add_co_owner(user_id, reason="Adding team member")
record.remove_co_owner(user_id, reason="User left team")
record.add_multiple_co_owners([user1_id, user2_id])
```

#### Search Methods
```python
# Find owned records
records = self.env['my.model'].search([('is_owned', '=', True)])

# Find records I can transfer
records = self.env['my.model'].search([('can_transfer', '=', True)])

# Find my owned records
records = self.env['my.model'].search([('is_owned_by_me', '=', True)])
```

### 2. Assignment Mixin (`tk.assignable.mixin`)

#### Fields Added
```python
assigned_user_ids = fields.Many2many('res.users')  # Assigned users
assigner_id = fields.Many2one('res.users')         # Who assigned
assignment_date = fields.Datetime()                # When assigned
assignment_deadline = fields.Datetime()            # Deadline
assignment_status = fields.Selection()             # Status
assignment_priority = fields.Selection()           # Priority
is_assigned = fields.Boolean(compute=True)         # Is assigned?
is_overdue = fields.Boolean(compute=True)          # Is overdue?
can_assign = fields.Boolean(compute=True)          # Can assign?
```

#### Methods Available
```python
# Assign to users
record.assign_to_users(
    user_ids=[user1_id, user2_id],
    deadline=fields.Datetime.now() + timedelta(days=7),
    description="Please complete this task",
    priority='high',
    reason="Urgent project requirement"
)

# Manage assignments
record.add_assignee(user_id, reason="Adding specialist")
record.remove_assignee(user_id, reason="Reassigning work")
record.reassign_to_users([new_user_id])
record.unassign_all(reason="Cancelling task")

# Status management
record.start_assignment(reason="Beginning work")
record.complete_assignment(reason="Task finished")
record.cancel_assignment(reason="Requirements changed")
```

### 3. Access Control Mixin (`tk.accessible.mixin`)

#### Fields Added
```python
access_level = fields.Selection()                  # public/internal/restricted/private
allowed_user_ids = fields.Many2many('res.users')  # Explicit users
allowed_group_ids = fields.Many2many('res.groups') # System groups
custom_access_group_ids = fields.Many2many()      # Custom groups
access_start_date = fields.Datetime()             # Access starts
access_end_date = fields.Datetime()               # Access ends
has_access = fields.Boolean(compute=True)         # Current user access
can_grant_access = fields.Boolean(compute=True)   # Can grant access?
```

#### Methods Available
```python
# Grant access to user
record.grant_access_to_user(
    user_id,
    start_date=fields.Datetime.now(),
    end_date=fields.Datetime.now() + timedelta(days=30),
    reason="Project collaboration"
)

# Revoke access
record.revoke_access_from_user(user_id, reason="Project ended")

# Check access
if record._check_user_access(user):
    # User has access
    pass
```

### 4. Responsibility Mixin (`tk.responsible.mixin`)

#### Fields Added
```python
responsible_user_ids = fields.Many2many('res.users')      # Primary responsible
secondary_responsible_ids = fields.Many2many('res.users') # Secondary responsible
responsibility_type = fields.Selection()                  # Type of responsibility
responsibility_start_date = fields.Datetime()             # When started
responsibility_end_date = fields.Datetime()               # When ends
can_delegate = fields.Boolean(compute=True)               # Can delegate?
```

#### Methods Available
```python
# Assign responsibility
record.assign_responsibility(
    user_ids=[user1_id, user2_id],
    responsibility_type='primary',
    end_date=fields.Datetime.now() + timedelta(days=90),
    description="Responsible for project oversight",
    reason="Team restructuring"
)

# Delegate responsibility
record.delegate_responsibility([new_user_id], reason="Vacation coverage")

# Manage responsible users
record.add_responsible_user(user_id, is_secondary=False)
record.remove_responsible_user(user_id, is_secondary=True)
```

## Advanced Customization

### Extending Mixin Functionality

#### Override Computed Fields
```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['tk.ownable.mixin']
    
    @api.depends('owner_id', 'state')
    def _compute_can_transfer(self):
        # Custom logic for transfer permissions
        super()._compute_can_transfer()
        for record in self:
            if record.state == 'locked':
                record.can_transfer = False
```

#### Custom Permission Logic
```python
def _compute_can_assign(self):
    super()._compute_can_assign()
    for record in self:
        # Additional business rules
        if record.department_id.manager_id == self.env.user:
            record.can_assign = True
        elif record.priority == 'urgent' and not record.is_assigned:
            record.can_assign = True
```

#### Add Custom Fields
```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['tk.assignable.mixin']
    
    # Custom assignment fields
    assignment_category = fields.Selection([
        ('development', 'Development'),
        ('testing', 'Testing'),
        ('review', 'Review')
    ])
    
    estimated_hours = fields.Float('Estimated Hours')
    actual_hours = fields.Float('Actual Hours')
```

### Integration with Existing Models

#### Retrofit Existing Models
```python
# Add to existing model
class SaleOrder(models.Model):
    _inherit = ['sale.order', 'tk.ownable.mixin', 'tk.assignable.mixin']
    
    # Existing fields remain unchanged
    # New mixin fields are automatically added
```

#### Handle Field Conflicts
```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['tk.ownable.mixin']
    
    # If you already have an 'owner_id' field
    _owner_field = 'record_owner_id'  # Use different field name
    
    record_owner_id = fields.Many2one('res.users', string='Record Owner')
```

## View Integration

### Form View Integration
```xml
<record id="view_my_model_form" model="ir.ui.view">
    <field name="name">my.model.form</field>
    <field name="model">my.model</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <!-- Ownership Actions -->
                <button name="%(comprehensive_toolkit.action_transfer_ownership_wizard)d" 
                        string="Transfer Ownership" type="action" 
                        invisible="not can_transfer"/>
                
                <!-- Assignment Actions -->
                <button name="%(comprehensive_toolkit.action_bulk_assign_wizard)d" 
                        string="Assign Users" type="action" 
                        invisible="not can_assign"/>
                
                <!-- Access Management -->
                <button name="%(comprehensive_toolkit.action_manage_access_wizard)d" 
                        string="Manage Access" type="action" 
                        invisible="not can_grant_access"/>
                
                <!-- Responsibility Actions -->
                <button name="%(comprehensive_toolkit.action_delegate_responsibility_wizard)d" 
                        string="Delegate" type="action" 
                        invisible="not can_delegate"/>
            </header>
            <sheet>
                <!-- Your existing fields -->
                <group>
                    <field name="name"/>
                    <field name="description"/>
                </group>
                
                <notebook>
                    <!-- Ownership Tab -->
                    <page string="Ownership">
                        <group>
                            <field name="owner_id"/>
                            <field name="co_owner_ids" widget="many2many_tags"/>
                            <field name="ownership_date"/>
                        </group>
                    </page>
                    
                    <!-- Assignment Tab -->
                    <page string="Assignment">
                        <group>
                            <field name="assigned_user_ids" widget="many2many_tags"/>
                            <field name="assignment_deadline"/>
                            <field name="assignment_status"/>
                            <field name="assignment_priority"/>
                        </group>
                    </page>
                    
                    <!-- Access Control Tab -->
                    <page string="Access Control">
                        <group>
                            <field name="access_level"/>
                            <field name="allowed_user_ids" widget="many2many_tags"/>
                            <field name="custom_access_group_ids" widget="many2many_tags"/>
                        </group>
                    </page>
                    
                    <!-- Responsibility Tab -->
                    <page string="Responsibility">
                        <group>
                            <field name="responsible_user_ids" widget="many2many_tags"/>
                            <field name="secondary_responsible_ids" widget="many2many_tags"/>
                            <field name="responsibility_type"/>
                        </group>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

### Search View Integration
```xml
<record id="view_my_model_search" model="ir.ui.view">
    <field name="name">my.model.search</field>
    <field name="model">my.model</field>
    <field name="arch" type="xml">
        <search>
            <field name="name"/>
            
            <!-- Mixin-based filters -->
            <filter string="My Records" name="owned_by_me" 
                    domain="[('owner_id', '=', uid)]"/>
            <filter string="Assigned to Me" name="assigned_to_me" 
                    domain="[('assigned_user_ids', 'in', [uid])]"/>
            <filter string="My Responsibilities" name="responsible_me" 
                    domain="[('responsible_user_ids', 'in', [uid])]"/>
            <filter string="Overdue" name="overdue" 
                    domain="[('is_overdue', '=', True)]"/>
            
            <group expand="1" string="Group By">
                <filter string="Owner" name="group_owner" 
                        context="{'group_by': 'owner_id'}"/>
                <filter string="Assignment Status" name="group_assignment" 
                        context="{'group_by': 'assignment_status'}"/>
            </group>
        </search>
    </field>
</record>
```

## Security Considerations

### Access Rights
The mixins respect Odoo's security model. Ensure your model has appropriate access rules:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_my_model,my.model,model_my_model,base.group_user,1,1,1,1
access_my_model_manager,my.model manager,model_my_model,base.group_system,1,1,1,1
```

### Record Rules
Use record rules for additional security:

```xml
<record id="my_model_rule_owner" model="ir.rule">
    <field name="name">My Model: Owner Access</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="domain_force">[
        '|', ('owner_id', '=', user.id),
        '|', ('co_owner_ids', 'in', [user.id]),
        ('access_level', 'in', ['public', 'internal'])
    ]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
</record>
```

## Performance Optimization

### Database Indexing
Add indexes for frequently searched fields:

```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['tk.ownable.mixin']
    
    owner_id = fields.Many2one('res.users', index=True)
    assignment_deadline = fields.Datetime(index=True)
```

### Computed Field Optimization
```python
@api.depends('owner_id', 'co_owner_ids')
def _compute_is_owned_by_me(self):
    # Optimize for large datasets
    user_id = self.env.user.id
    for record in self:
        record.is_owned_by_me = (
            record.owner_id.id == user_id or 
            user_id in record.co_owner_ids.ids
        )
```

## Testing

### Unit Tests
```python
from odoo.tests.common import TransactionCase

class TestMyModel(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.model = self.env['my.model']
        self.user1 = self.env.ref('base.user_demo')
        self.user2 = self.env.ref('base.user_admin')
    
    def test_ownership_transfer(self):
        record = self.model.create({'name': 'Test Record'})
        
        # Test initial ownership
        self.assertEqual(record.owner_id, self.env.user)
        
        # Test transfer
        record.transfer_ownership(self.user1.id, reason="Test transfer")
        self.assertEqual(record.owner_id, self.user1)
        self.assertEqual(record.previous_owner_id, self.env.user)
    
    def test_assignment(self):
        record = self.model.create({'name': 'Test Record'})
        
        # Test assignment
        record.assign_to_users([self.user1.id, self.user2.id])
        self.assertTrue(record.is_assigned)
        self.assertIn(self.user1, record.assigned_user_ids)
        self.assertIn(self.user2, record.assigned_user_ids)
```

## Migration and Upgrades

### Adding Mixins to Existing Models
```python
# In migration script
def migrate(cr, version):
    # Add mixin fields to existing model
    if not version:
        return
    
    # Add owner_id field with default value
    cr.execute("""
        ALTER TABLE my_existing_table 
        ADD COLUMN owner_id INTEGER 
        REFERENCES res_users(id)
    """)
    
    # Set current user as default owner for existing records
    cr.execute("""
        UPDATE my_existing_table 
        SET owner_id = 1 
        WHERE owner_id IS NULL
    """)
```

## Best Practices

### 1. Field Naming
- Use mixin fields as-is when possible
- Override field names only when conflicts exist
- Document any customizations clearly

### 2. Permission Logic
- Always call `super()` when overriding computed methods
- Add business logic after calling super
- Document permission rules clearly

### 3. Performance
- Index frequently searched fields
- Use proper domain optimization
- Consider batch operations for bulk changes

### 4. User Experience
- Include mixin tabs in form views
- Add appropriate filters in search views
- Use clear button labels and help text

### 5. Testing
- Test all mixin functionality
- Test permission logic thoroughly
- Include edge cases in tests

---

*For more examples, see the [Examples Guide](examples.md) or check the included example models in the module.*
