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

## 🎯 Responsible Mixin Implementation

### Core Fields Added
```python
# Automatically added to your model
responsible_user_ids = fields.Many2many('res.users', 'Responsible Users')
secondary_responsible_ids = fields.Many2many('res.users', 'Secondary Responsible')
responsibility_start_date = fields.Datetime('Responsibility Start Date')
responsibility_end_date = fields.Datetime('Responsibility End Date')
responsibility_delegated_by = fields.Many2one('res.users', 'Delegated By')
responsibility_description = fields.Text('Responsibility Description')

# Computed fields
is_responsibility_active = fields.Boolean('Responsibility Active')
is_responsibility_expired = fields.Boolean('Responsibility Expired')
can_delegate = fields.Boolean('Can Delegate')
responsibility_count = fields.Integer('Number of Responsible Users')
secondary_responsibility_count = fields.Integer('Number of Secondary Responsible')
```

### Available Methods
```python
# Assign responsibility
record.assign_responsibility(
    user_ids=[user1.id, user2.id],
    end_date=fields.Datetime.now() + timedelta(days=30),
    description="Review and approve document",
    reason="Project milestone"
)

# Assign secondary responsibility
record.assign_secondary_responsibility(
    user_ids=[user3.id, user4.id],
    reason="Backup responsibility"
)

# Transfer/delegate responsibility
record.delegate_responsibility([new_user.id], reason="Delegation")
record.transfer_responsibility([new_user.id], reason="Transfer")

# Secondary responsibility management
record.delegate_secondary_responsibility([user.id], reason="Secondary delegation")
record.transfer_secondary_responsibility([user.id], reason="Secondary transfer")

# Individual user management
record.add_responsible_user(user.id, is_secondary=False, reason="Adding user")
record.remove_responsible_user(user.id, is_secondary=False, reason="Removing user")

# Escalation and revocation
record.escalate_responsibility(manager.id, reason="Escalation needed")
record.revoke_all_responsibility(reason="Task completed")
```

### Custom Responsibility Logic
```python
class CustomModel(models.Model):
    _name = 'custom.model'
    _inherit = ['tk.responsible.mixin']
    
    @api.depends('responsible_user_ids', 'state')
    def _compute_can_delegate(self):
        """Override delegation permissions with custom logic"""
        super()._compute_can_delegate()
        for record in self:
            # Add custom business rules
            if record.state == 'locked':
                record.can_delegate = False
            elif record.priority == 'urgent':
                # Only managers can delegate urgent items
                record.can_delegate = self.env.user.has_group('base.group_system')
    
    def custom_responsibility_workflow(self):
        """Custom workflow integration"""
        if self.state == 'ready_for_review':
            # Auto-assign to quality team
            quality_users = self.env.ref('my_module.group_quality').users
            self.assign_responsibility(
                user_ids=quality_users.ids,
                description="Quality review required",
                reason="Workflow automation"
            )
```

## 📋 Assignable Mixin Implementation

### Core Fields Added
```python
assigned_user_ids = fields.Many2many('res.users', 'Assigned Users')
assignment_date = fields.Datetime('Assignment Date')
assignment_deadline = fields.Datetime('Assignment Deadline')
assignment_description = fields.Text('Assignment Description')
assignment_priority = fields.Selection([...], 'Priority')
assignment_status = fields.Selection([...], 'Status')
```

### Available Methods
```python
# Basic assignment
record.assign_to_users(
    user_ids=[user1.id, user2.id],
    deadline=fields.Datetime.now() + timedelta(days=7),
    description="Complete the task",
    priority='high',
    reason="Urgent project"
)

# Assignment management
record.unassign_from_users([user1.id], reason="Role change")
record.reassign_to_users([new_user.id], reason="Reassignment")
record.update_assignment_status('in_progress')
```

## 🔒 Accessible Mixin Implementation

### Core Fields Added
```python
# Access control fields
access_level = fields.Selection([
    ('public', 'Public'),
    ('internal', 'Internal'),
    ('restricted', 'Restricted'),
    ('private', 'Private')
], default='internal', tracking=True)

allowed_user_ids = fields.Many2many('res.users', 'Allowed Users')
allowed_group_ids = fields.Many2many('res.groups', 'Allowed Groups')
custom_access_group_ids = fields.Many2many('tk.accessible.group', 'Custom Access Groups')

access_start_date = fields.Datetime('Access Start Date')
access_end_date = fields.Datetime('Access End Date')

# Computed fields
allowed_group_users_ids = fields.Many2many('res.users', compute='_compute_allowed_group_users_ids', store=True)
custom_group_users_ids = fields.Many2many('res.users', compute='_compute_custom_group_users_ids', store=True)
all_allowed_users_ids = fields.Many2many('res.users', compute='_compute_all_allowed_users_ids', store=True)
is_access_expired = fields.Boolean(compute='_compute_is_access_expired')
can_grant_access = fields.Boolean(compute='_compute_can_grant_access')
has_access = fields.Boolean(compute='_compute_has_access')
```

### Available Methods
```python
# User access management
record.grant_access_to_user(
    user_id=user.id,
    start_date=fields.Datetime.now(),
    end_date=fields.Datetime.now() + timedelta(days=30),
    reason="Project collaboration"
)

record.revoke_access_from_user(user.id, reason="Project ended")

# Bulk user operations
record.bulk_grant_access_to_users(
    user_ids=[user1.id, user2.id],
    end_date=fields.Datetime.now() + timedelta(days=30),
    reason="Team access"
)

# Group access management
record.grant_access_to_group(group.id, reason="Department access")
record.grant_access_to_custom_group(custom_group.id, reason="Project team access")

# Access level and duration
record.set_access_level('restricted', reason="Confidential information")
record.set_access_duration(
    start_date=fields.Datetime.now(),
    end_date=fields.Datetime.now() + timedelta(days=60),
    reason="Temporary project access"
)

# Custom group creation
team_group = record.create_and_assign_custom_group(
    group_name="Project Alpha Team",
    user_ids=[user1.id, user2.id, user3.id],
    group_type='project',
    reason="Project team setup"
)
```

### Custom Access Control Logic
```python
class CustomModel(models.Model):
    _name = 'custom.model'
    _inherit = ['tk.accessible.mixin']
    
    def _compute_can_grant_access(self):
        """Override access granting permissions with custom logic"""
        super()._compute_can_grant_access()
        for record in self:
            # Add custom business rules
            if record.state == 'locked':
                record.can_grant_access = False
            elif record.confidentiality_level == 'top_secret':
                # Only security officers can grant access
                record.can_grant_access = self.env.user.has_group('security.group_security_officer')
    
    def custom_access_workflow(self):
        """Custom workflow integration with access control"""
        if self.state == 'draft':
            # Set internal access for drafts
            self.set_access_level('internal', reason="Draft document")
        elif self.state == 'review':
            # Create review team group
            reviewers = self.env['res.users'].search([('is_reviewer', '=', True)])
            self.create_and_assign_custom_group(
                group_name=f"Review Team - {self.name}",
                user_ids=reviewers.ids,
                group_type='temporary',
                reason="Document review process"
            )
            self.set_access_level('restricted', reason="Under review")
        elif self.state == 'approved':
            # Set public access for approved documents
            self.set_access_level('public', reason="Document approved")
```

## 🔒 Accessible Group Mixin Implementation

### Enhanced Group Management Fields
```python
# Group management fields
allowed_group_users_ids = fields.Many2many('res.users', compute='_compute_allowed_group_users_ids', store=True)
custom_access_group_ids = fields.Many2many('tk.accessible.group', 'Custom Access Groups')
can_manage_groups = fields.Boolean(compute='_compute_can_manage_groups')
total_group_users_count = fields.Integer(compute='_compute_group_statistics')
active_custom_groups_count = fields.Integer(compute='_compute_group_statistics')
has_group_access = fields.Boolean(compute='_compute_has_group_access')
```

### Available Methods
```python
# Custom group management
record.add_custom_access_group(group.id, reason="Project collaboration")
record.remove_custom_access_group(group.id, reason="Project ended")
record.replace_custom_access_groups([group1.id, group2.id], reason="Team restructure")
record.clear_all_custom_groups(reason="Project completion")

# Group information
users = record.get_users_from_group(group.id)
all_users = record.get_all_group_users(include_inactive=False)
has_access = record.check_user_group_access(user)
summary = record.get_group_access_summary()

# Actions
record.action_manage_custom_groups()  # Opens wizard
record.action_view_group_users()      # Shows user list
```

## 📊 Custom Access Group Model

### Implementation
```python
class CustomAccessGroup(models.Model):
    _name = 'tk.accessible.group'
    _description = 'Custom Access Group'
    
    name = fields.Char('Group Name', required=True)
    description = fields.Text('Description')
    group_type = fields.Selection([
        ('project', 'Project Team'),
        ('department', 'Department'),
        ('temporary', 'Temporary Access'),
        ('custom', 'Custom Group')
    ], default='custom', required=True)
    
    user_ids = fields.Many2many('res.users', string='Users')
    active = fields.Boolean('Active', default=True)
    user_count = fields.Integer(compute='_compute_user_count', store=True)
    
    def add_users(self, user_ids, reason=None):
        """Add users to the group"""
        users = self.env['res.users'].browse(user_ids)
        new_users = users.filtered(lambda u: u not in self.user_ids)
        if new_users:
            self.user_ids = [(4, user_id) for user_id in new_users.ids]
            self._log_group_change('add_users', new_users, reason)
        return True
    
    @api.model
    def create_project_team_group(self, project_name, user_ids):
        """Create a project team access group"""
        return self.create({
            'name': f"Project Team - {project_name}",
            'description': f"Access group for {project_name} project team members",
            'group_type': 'project',
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        })
```

## 🔗 Advanced Integration Patterns

### Multi-Level Access Control
```python
class ProjectDocument(models.Model):
    _name = 'project.document'
    _inherit = ['tk.ownable.mixin', 'tk.accessible.mixin', 'tk.accessible.group.mixin']
    
    classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret')
    ])
    
    @api.model
    def create(self, vals):
        """Auto-setup access based on classification"""
        record = super().create(vals)
        record._setup_classification_access()
        return record
    
    def _setup_classification_access(self):
        """Setup access control based on document classification"""
        if self.classification == 'public':
            self.set_access_level('public', reason="Public document")
        elif self.classification == 'internal':
            self.set_access_level('internal', reason="Internal document")
        elif self.classification == 'confidential':
            self.set_access_level('restricted', reason="Confidential document")
            # Create confidential access group
            if hasattr(self, 'department_id') and self.department_id:
                dept_group = self.env['tk.accessible.group'].create_department_group(
                    self.department_id.name,
                    self.department_id.member_ids.ids
                )
                self.grant_access_to_custom_group(dept_group.id, reason="Department confidential access")
        elif self.classification == 'secret':
            self.set_access_level('private', reason="Secret document")
            # Only security cleared personnel
            security_users = self.env['res.users'].search([('security_clearance', '=', 'secret')])
            self.bulk_grant_access_to_users(security_users.ids, reason="Security clearance required")
```

### Dynamic Access Groups
```python
class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = ['tk.ownable.mixin', 'tk.accessible.mixin', 'tk.responsible.mixin']
    
    def action_start_task(self):
        """Create dynamic access group when task starts"""
        super().action_start_task()
        
        # Create task team group
        team_users = self.responsible_user_ids | self.assigned_user_ids
        if team_users:
            task_group = self.create_and_assign_custom_group(
                group_name=f"Task Team - {self.name}",
                user_ids=team_users.ids,
                group_type='project',
                reason="Task team collaboration"
            )
            
            # Set restricted access
            self.set_access_level('restricted', reason="Active task - team only")
            
    def action_complete_task(self):
        """Update access when task is completed"""
        super().action_complete_task()
        
        # Archive task groups and set internal access
        for group in self.custom_access_group_ids:
            if 'Task Team' in group.name:
                group.active = False
        
        self.set_access_level('internal', reason="Task completed")
```

### Wizard Integration
```python
class CustomAccessWizard(models.TransientModel):
    _name = 'custom.access.wizard'
    _description = 'Custom Access Management'
    
    def action_setup_project_access(self):
        """Setup comprehensive project access"""
        active_ids = self.env.context.get('active_ids', [])
        records = self.env[self.env.context.get('active_model')].browse(active_ids)
        
        for record in records:
            # Create project team group
            team_group = self.env['tk.accessible.group'].create({
                'name': f"Project Team - {record.name}",
                'group_type': 'project',
                'user_ids': [(6, 0, self.team_member_ids.ids)]
            })
            
            # Create stakeholder group
            stakeholder_group = self.env['tk.accessible.group'].create({
                'name': f"Project Stakeholders - {record.name}",
                'group_type': 'custom',
                'user_ids': [(6, 0, self.stakeholder_ids.ids)]
            })
            
            # Setup access
            record.set_access_level('restricted', reason="Project access setup")
            record.grant_access_to_custom_group(team_group.id, reason="Team collaboration")
            record.grant_access_to_custom_group(stakeholder_group.id, reason="Stakeholder visibility")
            
            # Set access duration
            if self.project_end_date:
                record.set_access_duration(
                    end_date=self.project_end_date,
                    reason="Project timeline"
                )
```

## 🧪 Testing Patterns

### Access Control Testing
```python
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, ValidationError

class TestAccessControl(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.test_model = self.env['test.model'].create({'name': 'Test Record'})
        self.user1 = self.env.ref('base.user_demo')
        self.user2 = self.env.ref('base.user_admin')
        self.group = self.env.ref('base.group_user')
    
    def test_access_level_public(self):
        """Test public access level"""
        self.test_model.set_access_level('public')
        self.assertTrue(self.test_model._check_user_access(self.user1))
        self.assertTrue(self.test_model._check_user_access(self.user2))
    
    def test_access_level_restricted(self):
        """Test restricted access level"""
        self.test_model.set_access_level('restricted')
        
        # No access by default
        self.assertFalse(self.test_model._check_user_access(self.user1))
        
        # Grant access to user
        self.test_model.grant_access_to_user(self.user1.id)
        self.assertTrue(self.test_model._check_user_access(self.user1))
        
        # Still no access for other user
        self.assertFalse(self.test_model._check_user_access(self.user2))
    
    def test_custom_group_access(self):
        """Test custom group access"""
        # Create custom group
        custom_group = self.env['tk.accessible.group'].create({
            'name': 'Test Group',
            'group_type': 'custom',
            'user_ids': [(6, 0, [self.user1.id])]
        })
        
        # Set restricted access and grant to group
        self.test_model.set_access_level('restricted')
        self.test_model.grant_access_to_custom_group(custom_group.id)
        
        # User in group should have access
        self.assertTrue(self.test_model._check_user_access(self.user1))
        # User not in group should not have access
        self.assertFalse(self.test_model._check_user_access(self.user2))
    
    def test_access_expiry(self):
        """Test access expiry functionality"""
        from datetime import timedelta
        
        # Set access with past end date
        past_date = fields.Datetime.now() - timedelta(days=1)
        self.test_model.grant_access_to_user(
            self.user1.id,
            end_date=past_date
        )
        
        # Access should be expired
        self.assertTrue(self.test_model.is_access_expired)
        self.assertFalse(self.test_model._check_user_access(self.user1))
    
    def test_bulk_operations(self):
        """Test bulk access operations"""
        # Create multiple records
        records = self.env['test.model'].create([
            {'name': 'Record 1'},
            {'name': 'Record 2'},
            {'name': 'Record 3'}
        ])
        
        # Bulk grant access
        user_ids = [self.user1.id, self.user2.id]
        for record in records:
            record.set_access_level('restricted')
            record.bulk_grant_access_to_users(user_ids, reason="Bulk test")
        
        # Verify all records have access for both users
        for record in records:
            self.assertTrue(record._check_user_access(self.user1))
            self.assertTrue(record._check_user_access(self.user2))
```

This completes the comprehensive developer guide with detailed implementation patterns, code examples, and testing strategies for the accessible functionality.
