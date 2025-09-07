# Developer Guide

This guide provides technical documentation for developers who want to integrate the Comprehensive Toolkit mixins into their custom Odoo models.

## 🏗️ Architecture Overview

The Comprehensive Toolkit consists of four main abstract models (mixins) that can be inherited by any Odoo model:

- `tk.ownable.mixin` - Ownership management
- `tk.assignable.mixin` - Assignment functionality  
- `tk.accessible.mixin` - Access control
- `tk.responsible.mixin` - Responsibility tracking

Each mixin is completely independent and can be used individually or in combination.

## 🔧 Basic Implementation

### Simple Model with One Mixin

```python
from odoo import models, fields, api

class MyCustomModel(models.Model):
    _name = 'my.custom.model'
    _inherit = ['tk.ownable.mixin']  # Add ownership functionality
    _description = 'My Custom Model with Ownership'
    
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
```

### Model with Multiple Mixins

```python
class ProjectTask(models.Model):
    _name = 'my.project.task'
    _inherit = [
        'tk.ownable.mixin',           # Ownership management
        'tk.assignable.mixin',        # Assignment functionality
        'tk.accessible.mixin',        # Access control
        'tk.responsible.mixin'        # Responsibility management
    ]
    _description = 'Project Task with Full Toolkit'
    
    name = fields.Char('Task Name', required=True)
    project_id = fields.Many2one('project.project', 'Project')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'), 
        ('done', 'Done')
    ], default='draft')
```

## 🎯 Ownable Mixin Implementation

### Core Fields Added
```python
# Automatically added to your model
owner_id = fields.Many2one('res.users', 'Owner')
co_owner_ids = fields.Many2many('res.users', 'Co-owners')
previous_owner_id = fields.Many2one('res.users', 'Previous Owner')
ownership_date = fields.Datetime('Ownership Date')

# Computed fields
is_owned = fields.Boolean('Is Owned', compute='_compute_is_owned')
can_transfer = fields.Boolean('Can Transfer', compute='_compute_can_transfer')
is_owned_by_me = fields.Boolean('Owned by Me', compute='_compute_is_owned_by_me')
```

### Available Methods
```python
# Transfer ownership
record.transfer_ownership(new_user_id, reason="Project handover")

# Add/remove co-owners
record.add_co_owner(user_id, reason="Collaboration")
record.remove_co_owner(user_id, reason="No longer needed")
record.add_multiple_co_owners([user1_id, user2_id], reason="Team expansion")
record.remove_all_co_owners(reason="Project restructure")

# Ownership lifecycle
record.claim_ownership(reason="Taking responsibility")
record.release_ownership(reason="No longer needed")

# Utility methods
is_owner = record.is_owner_or_co_owner(user)
all_owners = record.get_all_owners()  # Returns recordset
```

### Custom Ownership Logic
```python
class CustomModel(models.Model):
    _name = 'custom.model'
    _inherit = ['tk.ownable.mixin']
    
    def custom_ownership_check(self):
        """Add custom business logic"""
        if self.state == 'locked':
            raise ValidationError("Cannot change ownership of locked records")
        return super().transfer_ownership()
    
    @api.model
    def create(self, vals):
        """Auto-assign ownership on creation"""
        record = super().create(vals)
        if not record.owner_id:
            record.owner_id = self.env.user
        return record
```

## 📋 Assignable Mixin Implementation

### Core Fields Added
```python
assigned_user_ids = fields.Many2many('res.users', 'Assigned To')
assignment_status = fields.Selection([...], 'Assignment Status')
assignment_priority = fields.Selection([...], 'Priority')
assignment_deadline = fields.Datetime('Deadline')
assignment_description = fields.Text('Description')

# Computed fields
is_assigned = fields.Boolean('Is Assigned', compute='_compute_is_assigned')
is_overdue = fields.Boolean('Is Overdue', compute='_compute_is_overdue')
is_assigned_to_me = fields.Boolean('Assigned to Me', compute='_compute_is_assigned_to_me')
```

### Available Methods
```python
# Assignment operations
record.assign_to_users([user1_id, user2_id], 
                      deadline=datetime.now() + timedelta(days=7),
                      description="Complete feature",
                      priority='high',
                      reason="Urgent requirement")

record.add_assignee(user_id, reason="Additional help needed")
record.remove_assignee(user_id, reason="No longer required")
record.unassign_all_users(reason="Task cancelled")

# Status management
record.start_assignment(reason="Work begun")
record.complete_assignment(reason="Task finished") 
record.cancel_assignment(reason="No longer needed")
```

### Smart Assignment Permissions
The mixin includes intelligent permission checking:
```python
def _compute_can_assign(self):
    """Smart permission calculation"""
    for record in self:
        # Considers ownership, access levels, current assignments
        has_ownership = record.owner_id == self.env.user
        has_access = record._check_access_permissions()
        is_assigned = self.env.user in record.assigned_user_ids
        
        record.can_assign = has_ownership or has_access or is_assigned
```

## 🔐 Accessible Mixin Implementation

### Core Fields Added
```python
access_level = fields.Selection([
    ('public', 'Public'),
    ('internal', 'Internal'), 
    ('restricted', 'Restricted'),
    ('private', 'Private')
], 'Access Level')

allowed_user_ids = fields.Many2many('res.users', 'Allowed Users')
allowed_group_ids = fields.Many2many('res.groups', 'Allowed Groups')
custom_access_group_ids = fields.Many2many('tk.accessible.group', 'Custom Groups')

# Time-based access
access_start_date = fields.Datetime('Access Start Date')
access_end_date = fields.Datetime('Access End Date')

# Computed fields
has_access = fields.Boolean('Has Access', compute='_compute_has_access')
is_access_expired = fields.Boolean('Access Expired', compute='_compute_is_access_expired')
```

### Available Methods
```python
# Access management
record.grant_access([user1_id, user2_id], reason="Review access")
record.revoke_access([user_id], reason="No longer needed")
record.grant_group_access(group_id, reason="Department access")

# Access checking
has_access = record.check_user_access(user)
access_reason = record.get_access_reason(user)

# Bulk operations
record.set_access_level('restricted', reason="Security requirement")
record.copy_access_from(other_record, reason="Same permissions needed")
```

### Custom Access Groups
```python
# Create custom access group
access_group = self.env['tk.accessible.group'].create({
    'name': 'Project Alpha Team',
    'description': 'Team members for Project Alpha',
    'user_ids': [(6, 0, [user1.id, user2.id, user3.id])],
    'active': True
})

# Apply to records
records.write({
    'custom_access_group_ids': [(4, access_group.id)]
})
```

## 👥 Responsible Mixin Implementation

### Core Fields Added
```python
responsible_user_ids = fields.Many2many('res.users', 'Responsible Users')
secondary_responsible_ids = fields.Many2many('res.users', 'Secondary Responsible')
responsibility_type = fields.Selection([...], 'Responsibility Type')
responsibility_start_date = fields.Datetime('Start Date')
responsibility_end_date = fields.Datetime('End Date')
responsibility_description = fields.Text('Description')

# Computed fields
is_responsibility_active = fields.Boolean('Active', compute='_compute_is_responsibility_active')
can_delegate = fields.Boolean('Can Delegate', compute='_compute_can_delegate')
```

### Available Methods
```python
# Responsibility assignment
record.assign_responsibility([user1_id], 
                           responsibility_type='primary',
                           description="Overall coordination",
                           end_date=datetime.now() + timedelta(days=30))

# Delegation
record.delegate_responsibility(user_id, 
                             end_date=datetime.now() + timedelta(days=7),
                             reason="Vacation coverage")

# Management
record.add_secondary_responsible([user1_id, user2_id])
record.remove_responsibility(user_id, reason="Role change")
record.transfer_responsibility(old_user_id, new_user_id, reason="Staff change")
```

## 🏗️ Advanced Integration Patterns

### Custom Workflow Integration
```python
class WorkflowModel(models.Model):
    _name = 'workflow.model'
    _inherit = ['tk.ownable.mixin', 'tk.assignable.mixin']
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved')
    ])
    
    def action_submit_for_review(self):
        """Custom workflow action with toolkit integration"""
        # Assign to reviewers
        reviewer_group = self.env.ref('my_module.group_reviewers')
        reviewers = reviewer_group.users
        
        self.assign_to_users(
            reviewers.ids,
            deadline=fields.Datetime.now() + timedelta(days=3),
            description="Review and approve document",
            priority='normal',
            reason="Workflow submission"
        )
        
        self.state = 'review'
```

### Smart Default Values
```python
class SmartModel(models.Model):
    _name = 'smart.model'
    _inherit = ['tk.accessible.mixin', 'tk.responsible.mixin']
    
    @api.model
    def create(self, vals):
        """Set smart defaults on creation"""
        record = super().create(vals)
        
        # Auto-set access level based on context
        if self.env.context.get('public_create'):
            record.access_level = 'public'
        elif self.env.context.get('department_create'):
            record.access_level = 'restricted'
            record.grant_group_access(self.env.user.groups_id[0].id)
        
        # Auto-assign responsibility to creator
        record.assign_responsibility(
            [self.env.user.id],
            responsibility_type='primary',
            description="Record creator"
        )
        
        return record
```

### Permission Override Patterns
```python
class SecureModel(models.Model):
    _name = 'secure.model'
    _inherit = ['tk.accessible.mixin']
    
    def _compute_can_grant_access(self):
        """Override default permission logic"""
        super()._compute_can_grant_access()
        for record in self:
            # Add custom business rules
            if record.security_level == 'classified':
                record.can_grant_access = self.env.user.has_group('base.group_system')
            elif record.department_id != self.env.user.department_id:
                record.can_grant_access = False
```

## 📊 Dashboard Integration

### Custom Dashboard Widgets
```python
class CustomDashboard(models.TransientModel):
    _inherit = 'tk.comprehensive.dashboard'
    
    # Add custom statistics
    my_custom_count = fields.Integer(
        'Custom Count',
        compute='_compute_custom_statistics'
    )
    
    def _compute_custom_statistics(self):
        for dashboard in self:
            # Add your custom logic
            count = self.env['your.model'].search_count([
                ('assigned_user_ids', 'in', self.env.user.id),
                ('state', '=', 'in_progress')
            ])
            dashboard.my_custom_count = count
```

## 🔍 Search and Domain Helpers

### Smart Domain Functions
```python
def get_accessible_domain(self, model_name):
    """Get domain for records user can access"""
    domain = []
    
    # Public records
    domain.append('|')
    domain.append(('access_level', '=', 'public'))
    
    # Internal records (if internal user)
    if not self.env.user.share:
        domain.append('|')
        domain.append(('access_level', '=', 'internal'))
    
    # Records user has explicit access to
    domain.append('|')
    domain.append(('allowed_user_ids', 'in', self.env.user.id))
    
    # Records owned by user
    domain.append(('owner_id', '=', self.env.user.id))
    
    return domain
```

### Custom Search Methods
```python
class CustomSearch(models.Model):
    _name = 'custom.search'
    _inherit = ['tk.ownable.mixin', 'tk.assignable.mixin']
    
    @api.model
    def search_my_work(self):
        """Find all records related to current user"""
        domain = [
            '|', '|', '|',
            ('owner_id', '=', self.env.user.id),
            ('co_owner_ids', 'in', self.env.user.id),
            ('assigned_user_ids', 'in', self.env.user.id),
            ('responsible_user_ids', 'in', self.env.user.id)
        ]
        return self.search(domain)
```

## 🧪 Testing

### Unit Test Examples
```python
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, ValidationError

class TestToolkitMixins(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.user1 = self.env['res.users'].create({
            'name': 'Test User 1',
            'login': 'testuser1'
        })
        self.user2 = self.env['res.users'].create({
            'name': 'Test User 2', 
            'login': 'testuser2'
        })
        
    def test_ownership_transfer(self):
        """Test ownership transfer functionality"""
        record = self.env['your.model'].create({
            'name': 'Test Record',
            'owner_id': self.user1.id
        })
        
        # Test transfer
        record.with_user(self.user1).transfer_ownership(
            self.user2.id, 
            reason="Test transfer"
        )
        
        self.assertEqual(record.owner_id, self.user2)
        self.assertEqual(record.previous_owner_id, self.user1)
        
    def test_assignment_permissions(self):
        """Test assignment permission logic"""
        record = self.env['your.model'].create({
            'name': 'Test Record',
            'owner_id': self.user1.id
        })
        
        # Owner should be able to assign
        self.assertTrue(record.with_user(self.user1).can_assign)
        
        # Non-owner should not
        self.assertFalse(record.with_user(self.user2).can_assign)
```

## 🔧 Performance Optimization

### Efficient Queries
```python
# Good: Use computed stored fields
@api.depends('assigned_user_ids')
def _compute_assigned_user_count(self):
    for record in self:
        record.assigned_user_count = len(record.assigned_user_ids)

# Good: Batch operations
records = self.env['your.model'].search([])
records.assign_to_users([user.id], reason="Batch assignment")

# Avoid: N+1 queries in loops
for record in records:
    record.assign_to_users([user.id])  # Bad - creates many queries
```

### Indexing for Performance
```python
# Add custom indexes in your model
class CustomModel(models.Model):
    _name = 'custom.model'
    _inherit = ['tk.ownable.mixin']
    
    def init(self):
        # Add database indexes for better performance
        tools.create_index(self._cr, 'custom_model_owner_state_idx', 
                          self._table, ['owner_id', 'state'])
```

## 🚀 Deployment Considerations

### Migration Scripts
```python
def migrate(cr, version):
    """Migration script for existing data"""
    if not version:
        return
        
    # Migrate existing ownership data
    cr.execute("""
        UPDATE your_table 
        SET owner_id = old_owner_field 
        WHERE old_owner_field IS NOT NULL
    """)
    
    # Set default access levels
    cr.execute("""
        UPDATE your_table 
        SET access_level = 'internal' 
        WHERE access_level IS NULL
    """)
```

### Configuration Management
```python
# config/settings.py
class ComprehensiveToolkitSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    default_access_level = fields.Selection([...], 
                                          string="Default Access Level")
    auto_assign_ownership = fields.Boolean("Auto-assign Ownership")
    
    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('toolkit.default_access_level', self.default_access_level)
        params.set_param('toolkit.auto_assign_ownership', self.auto_assign_ownership)
```

## 📚 Best Practices

### Code Organization
- Keep mixin-specific logic in separate methods
- Use descriptive method names with toolkit prefixes
- Document custom overrides clearly
- Follow Odoo coding standards

### Performance Guidelines
- Use stored computed fields for frequently accessed data
- Implement efficient search domains
- Batch operations when possible
- Add appropriate database indexes

### Security Considerations
- Always validate user permissions in custom methods
- Use sudo() carefully and document security implications
- Implement proper access controls for sensitive operations
- Regular security audits of access permissions

---

**Next**: Check out the [API Reference](api-reference.md) for complete method documentation and the [Examples](examples.md) for more practical implementation patterns.
