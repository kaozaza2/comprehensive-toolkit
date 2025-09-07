# Examples

Practical examples and implementation patterns for the Comprehensive Toolkit mixins.

## 🚀 Quick Start Examples

### Basic Project Task Model

```python
from odoo import models, fields, api, _
from datetime import timedelta

class ProjectTask(models.Model):
    _name = 'example.project.task'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin', 
        'tk.accessible.mixin',
        'tk.responsible.mixin'
    ]
    _description = 'Project Task with Full Toolkit'
    
    name = fields.Char('Task Name', required=True)
    description = fields.Text('Description')
    project_id = fields.Many2one('project.project', 'Project')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='normal')
    
    @api.model
    def create(self, vals):
        """Auto-assign ownership and set access level on creation"""
        task = super().create(vals)
        
        # Auto-assign ownership to creator
        if not task.owner_id:
            task.owner_id = self.env.user
        
        # Set access level based on priority
        if task.priority == 'critical':
            task.access_level = 'restricted'
        else:
            task.access_level = 'internal'
            
        return task
    
    def action_start_work(self):
        """Start working on the task"""
        # Assign to current user if not already assigned
        if self.env.user not in self.assigned_user_ids:
            self.add_assignee(self.env.user.id, reason="Starting work")
        
        # Change assignment status
        self.start_assignment(reason="Work begun")
        self.state = 'in_progress'
    
    def action_submit_for_review(self):
        """Submit task for review"""
        # Find reviewers group
        reviewers = self.env.ref('project.group_project_manager', raise_if_not_found=False)
        if reviewers:
            # Grant access to reviewers
            self.grant_group_access(reviewers.id, reason="Review required")
            
            # Assign for review
            self.assign_to_users(
                reviewers.users.ids,
                deadline=fields.Datetime.now() + timedelta(days=2),
                description="Review and approve task completion",
                priority='normal',
                reason="Task submitted for review"
            )
        
        self.state = 'review'
```

### Document Management System

```python
class Document(models.Model):
    _name = 'example.document'
    _inherit = ['tk.ownable.mixin', 'tk.accessible.mixin']
    _description = 'Document with Access Control'
    
    name = fields.Char('Document Name', required=True)
    content = fields.Html('Content')
    document_type = fields.Selection([
        ('public', 'Public Document'),
        ('internal', 'Internal Document'),
        ('confidential', 'Confidential'),
        ('classified', 'Classified')
    ], required=True)
    
    department_id = fields.Many2one('hr.department', 'Department')
    
    @api.model
    def create(self, vals):
        """Set access level based on document type"""
        doc = super().create(vals)
        
        # Auto-set access level
        access_mapping = {
            'public': 'public',
            'internal': 'internal', 
            'confidential': 'restricted',
            'classified': 'private'
        }
        doc.access_level = access_mapping.get(doc.document_type, 'internal')
        
        # Grant department access for internal documents
        if doc.document_type == 'internal' and doc.department_id:
            dept_users = doc.department_id.member_ids
            if dept_users:
                doc.grant_access(dept_users.ids, reason="Department access")
        
        return doc
    
    def action_share_with_team(self):
        """Share document with team members"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to share this document."))
        
        # Create custom access group for team
        team_group = self.env['tk.accessible.group'].create({
            'name': f'Team Access - {self.name}',
            'description': f'Team access for document: {self.name}',
            'user_ids': [(6, 0, self._get_team_members().ids)]
        })
        
        # Apply the group
        self.custom_access_group_ids = [(4, team_group.id)]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Document shared with team successfully'),
                'type': 'success'
            }
        }
    
    def _get_team_members(self):
        """Get team members - override in subclasses"""
        return self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('base.group_user').id)
        ])
```

### Customer Account Management

```python
class CustomerAccount(models.Model):
    _name = 'example.customer.account'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.responsible.mixin'
    ]
    _description = 'Customer Account with Assignment and Responsibility'
    
    name = fields.Char('Account Name', required=True)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    account_manager_id = fields.Many2one('res.users', 'Account Manager')
    revenue = fields.Monetary('Annual Revenue')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Account status
    status = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('at_risk', 'At Risk'),
        ('churned', 'Churned')
    ], default='prospect', tracking=True)
    
    @api.model
    def create(self, vals):
        """Auto-assign ownership and responsibility"""
        account = super().create(vals)
        
        # Set owner as account manager if specified
        if account.account_manager_id:
            account.owner_id = account.account_manager_id
            
            # Assign primary responsibility
            account.assign_responsibility(
                [account.account_manager_id.id],
                responsibility_type='primary',
                description="Primary account management and customer relationship"
            )
        
        return account
    
    def action_escalate_to_manager(self):
        """Escalate account to manager"""
        # Find sales manager
        sales_manager = self.env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
        if not sales_manager or not sales_manager.users:
            raise ValidationError(_("No sales manager found for escalation."))
        
        manager = sales_manager.users[0]
        
        # Transfer ownership
        self.transfer_ownership(manager.id, reason="Account escalated due to issues")
        
        # Assign urgent task
        self.assign_to_users(
            [manager.id],
            deadline=fields.Datetime.now() + timedelta(hours=24),
            description="Urgent: Account requires immediate attention",
            priority='urgent',
            reason="Account escalation"
        )
        
        # Add original owner as co-owner for continuity
        if self.owner_id != manager:
            self.add_co_owner(self.owner_id.id, reason="Continuity during escalation")
    
    def action_assign_support_team(self):
        """Assign account to support team"""
        support_group = self.env.ref('helpdesk.group_helpdesk_user', raise_if_not_found=False)
        if support_group:
            self.assign_to_users(
                support_group.users.ids,
                description="Provide ongoing customer support",
                priority='normal',
                reason="Support team assignment"
            )
            
            # Add secondary responsibility
            self.add_secondary_responsible(
                support_group.users.ids,
                reason="Support team backup responsibility"
            )
```

## 🏗️ Advanced Integration Examples

### Workflow Integration

```python
class WorkflowDocument(models.Model):
    _name = 'example.workflow.document'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.accessible.mixin'
    ]
    _description = 'Document with Workflow Integration'
    
    name = fields.Char('Document Name', required=True)
    content = fields.Text('Content')
    workflow_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published')
    ], default='draft', tracking=True)
    
    def action_submit(self):
        """Submit document for approval workflow"""
        # Set restricted access during review
        self.set_access_level('restricted', reason="Under review process")
        
        # Find approvers
        approver_group = self.env.ref('example.group_document_approvers')
        
        # Assign to approvers
        self.assign_to_users(
            approver_group.users.ids,
            deadline=fields.Datetime.now() + timedelta(days=5),
            description="Review and approve document for publication",
            priority='normal',
            reason="Document submitted for approval"
        )
        
        # Grant access to approvers
        self.grant_group_access(approver_group.id, reason="Review access")
        
        self.workflow_state = 'submitted'
    
    def action_approve(self):
        """Approve document"""
        if not self._can_approve():
            raise AccessError(_("You don't have permission to approve this document."))
        
        # Complete assignment
        self.complete_assignment(reason="Document approved")
        
        # Set public access for approved documents
        self.set_access_level('public', reason="Document approved for publication")
        
        self.workflow_state = 'approved'
    
    def action_reject(self):
        """Reject document"""
        if not self._can_approve():
            raise AccessError(_("You don't have permission to reject this document."))
        
        # Cancel assignment
        self.cancel_assignment(reason="Document rejected")
        
        # Transfer back to original owner
        if self.previous_owner_id:
            self.transfer_ownership(
                self.previous_owner_id.id, 
                reason="Returned to author for revision"
            )
        
        self.workflow_state = 'rejected'
    
    def _can_approve(self):
        """Check if current user can approve"""
        approver_group = self.env.ref('example.group_document_approvers', raise_if_not_found=False)
        return (
            approver_group and self.env.user in approver_group.users or
            self.env.user.has_group('base.group_system')
        )
```

### Multi-level Responsibility System

```python
class Project(models.Model):
    _name = 'example.project'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.responsible.mixin'
    ]
    _description = 'Project with Multi-level Responsibility'
    
    name = fields.Char('Project Name', required=True)
    description = fields.Text('Description')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    
    # Project hierarchy
    parent_project_id = fields.Many2one('example.project', 'Parent Project')
    child_project_ids = fields.One2many('example.project', 'parent_project_id', 'Sub-projects')
    
    # Project roles
    project_manager_id = fields.Many2one('res.users', 'Project Manager')
    tech_lead_id = fields.Many2one('res.users', 'Technical Lead')
    stakeholder_ids = fields.Many2many('res.users', 'project_stakeholder_rel', 'Stakeholders')
    
    @api.model
    def create(self, vals):
        """Set up project hierarchy and responsibilities"""
        project = super().create(vals)
        project._setup_project_roles()
        return project
    
    def _setup_project_roles(self):
        """Set up default project roles and responsibilities"""
        responsibilities = []
        
        # Project Manager - Primary responsibility
        if self.project_manager_id:
            responsibilities.append({
                'user_id': self.project_manager_id.id,
                'type': 'primary',
                'description': 'Overall project management and delivery'
            })
            
            # Set as owner
            self.owner_id = self.project_manager_id
        
        # Technical Lead - Secondary responsibility
        if self.tech_lead_id:
            responsibilities.append({
                'user_id': self.tech_lead_id.id,
                'type': 'secondary', 
                'description': 'Technical architecture and development oversight'
            })
            
            # Add as co-owner
            self.add_co_owner(self.tech_lead_id.id, reason="Technical lead role")
        
        # Set up responsibilities
        for resp in responsibilities:
            self.assign_responsibility(
                [resp['user_id']],
                responsibility_type=resp['type'],
                description=resp['description']
            )
        
        # Assign stakeholders for visibility
        if self.stakeholder_ids:
            self.assign_to_users(
                self.stakeholder_ids.ids,
                description="Project oversight and stakeholder review",
                priority='low',
                reason="Stakeholder visibility"
            )
    
    def action_delegate_management(self, new_manager_id, duration_days=None):
        """Temporarily delegate project management"""
        if not self.can_delegate:
            raise AccessError(_("You cannot delegate this project."))
        
        end_date = None
        if duration_days:
            end_date = fields.Datetime.now() + timedelta(days=duration_days)
        
        # Delegate responsibility
        self.delegate_responsibility(
            new_manager_id,
            end_date=end_date,
            reason=f"Temporary delegation for {duration_days} days" if duration_days else "Temporary delegation"
        )
        
        # Add as co-owner during delegation
        self.add_co_owner(new_manager_id, reason="Temporary management delegation")
        
        return True
    
    def action_escalate_to_portfolio(self):
        """Escalate project issues to portfolio level"""
        # Find portfolio managers
        portfolio_group = self.env.ref('project.group_portfolio_manager', raise_if_not_found=False)
        if not portfolio_group:
            raise ValidationError(_("No portfolio management group found."))
        
        # Assign to portfolio managers
        self.assign_to_users(
            portfolio_group.users.ids,
            deadline=fields.Datetime.now() + timedelta(days=1),
            description="Project requires portfolio-level intervention",
            priority='urgent',
            reason="Project escalation"
        )
        
        # Grant access to portfolio level
        self.grant_group_access(portfolio_group.id, reason="Portfolio escalation")
```

### Custom Dashboard Integration

```python
class ProjectDashboard(models.TransientModel):
    _inherit = 'tk.comprehensive.dashboard'
    
    # Project-specific statistics
    my_managed_projects = fields.Integer(
        'Projects I Manage',
        compute='_compute_project_statistics'
    )
    overdue_project_tasks = fields.Integer(
        'Overdue Project Tasks',
        compute='_compute_project_statistics'
    )
    projects_requiring_attention = fields.Integer(
        'Projects Requiring Attention',
        compute='_compute_project_statistics'
    )
    
    def _compute_project_statistics(self):
        for dashboard in self:
            # Projects I manage (own)
            dashboard.my_managed_projects = self.env['example.project'].search_count([
                ('owner_id', '=', self.env.user.id)
            ])
            
            # Overdue tasks assigned to me
            dashboard.overdue_project_tasks = self.env['example.project.task'].search_count([
                ('assigned_user_ids', 'in', self.env.user.id),
                ('is_overdue', '=', True),
                ('assignment_status', 'in', ['assigned', 'in_progress'])
            ])
            
            # Projects where I'm responsible and have urgent assignments
            dashboard.projects_requiring_attention = self.env['example.project'].search_count([
                ('responsible_user_ids', 'in', self.env.user.id),
                ('assigned_user_ids', 'in', self.env.user.id),
                ('assignment_priority', '=', 'urgent')
            ])
    
    def action_view_my_projects(self):
        """Open view of projects I manage"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Projects',
            'res_model': 'example.project',
            'view_mode': 'tree,form',
            'domain': [('owner_id', '=', self.env.user.id)],
            'context': {'create': False}
        }
    
    def action_view_overdue_tasks(self):
        """Open view of my overdue tasks"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Overdue Tasks',
            'res_model': 'example.project.task',
            'view_mode': 'tree,form',
            'domain': [
                ('assigned_user_ids', 'in', self.env.user.id),
                ('is_overdue', '=', True),
                ('assignment_status', 'in', ['assigned', 'in_progress'])
            ]
        }
```

## 🔍 Search and Filter Examples

### Smart Search Methods

```python
class SmartSearch(models.Model):
    _name = 'example.smart.search'
    _description = 'Smart Search Examples'
    
    @api.model
    def search_my_work(self):
        """Find all records I'm involved with"""
        domain = [
            '|', '|', '|', '|',
            ('owner_id', '=', self.env.user.id),
            ('co_owner_ids', 'in', self.env.user.id),
            ('assigned_user_ids', 'in', self.env.user.id),
            ('responsible_user_ids', 'in', self.env.user.id),
            ('secondary_responsible_ids', 'in', self.env.user.id)
        ]
        return self.search(domain)
    
    @api.model
    def search_urgent_items(self):
        """Find items requiring urgent attention"""
        domain = [
            '|', '|',
            ('assignment_priority', '=', 'urgent'),
            ('is_overdue', '=', True),
            ('responsibility_type', '=', 'primary'),
            # User is involved
            '|', '|', '|',
            ('owner_id', '=', self.env.user.id),
            ('assigned_user_ids', 'in', self.env.user.id),
            ('responsible_user_ids', 'in', self.env.user.id)
        ]
        return self.search(domain)
    
    @api.model
    def search_accessible_records(self, access_level=None):
        """Find records user can access"""
        domain = []
        
        # Public records
        domain.append('|')
        domain.append(('access_level', '=', 'public'))
        
        # Internal records (if internal user)
        if not self.env.user.share:
            domain.append('|')
            domain.append(('access_level', '=', 'internal'))
        
        # Records with explicit access
        domain.append('|')
        domain.append(('allowed_user_ids', 'in', self.env.user.id))
        
        # Records through group access
        user_groups = self.env.user.groups_id
        if user_groups:
            domain.append('|')
            domain.append(('allowed_group_ids', 'in', user_groups.ids))
        
        # Records owned by user
        domain.append('|')
        domain.append(('owner_id', '=', self.env.user.id))
        
        # Records co-owned by user
        domain.append(('co_owner_ids', 'in', self.env.user.id))
        
        if access_level:
            domain.append(('access_level', '=', access_level))
        
        return self.search(domain)
```

### Custom Filters

```python
# In your model's view, add custom filters
class CustomFilters(models.Model):
    _name = 'example.custom.filters'
    _inherit = ['tk.ownable.mixin', 'tk.assignable.mixin']
    
    # Add search methods for common filter patterns
    def _search_is_owned_by_me(self, operator, value):
        """Search for records owned by current user"""
        if operator == '=' and value:
            return [
                '|',
                ('owner_id', '=', self.env.user.id),
                ('co_owner_ids', 'in', self.env.user.id)
            ]
        return []
    
    def _search_needs_attention(self, operator, value):
        """Search for records needing attention"""
        if operator == '=' and value:
            return [
                '|', '|',
                ('is_overdue', '=', True),
                ('assignment_priority', '=', 'urgent'),
                ('assignment_status', '=', 'assigned')
            ]
        return []
    
    # Add computed fields for the filters
    needs_attention = fields.Boolean(
        'Needs Attention',
        search='_search_needs_attention',
        help="Records requiring immediate attention"
    )
```

## 🧪 Testing Examples

### Comprehensive Test Suite

```python
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, ValidationError
from datetime import timedelta

class TestComprehensiveToolkit(TransactionCase):
    
    def setUp(self):
        super().setUp()
        
        # Create test users
        self.user1 = self.env['res.users'].create({
            'name': 'Test User 1',
            'login': 'testuser1',
            'email': 'test1@example.com'
        })
        
        self.user2 = self.env['res.users'].create({
            'name': 'Test User 2', 
            'login': 'testuser2',
            'email': 'test2@example.com'
        })
        
        self.manager = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'manager',
            'email': 'manager@example.com',
            'groups_id': [(4, self.env.ref('base.group_system').id)]
        })
        
        # Create test model record
        self.test_record = self.env['example.project.task'].create({
            'name': 'Test Task',
            'description': 'Test task for toolkit testing'
        })
    
    def test_ownership_workflow(self):
        """Test complete ownership workflow"""
        # Initial state - created by admin, so should have owner
        self.assertTrue(self.test_record.owner_id)
        
        # Transfer ownership
        self.test_record.transfer_ownership(
            self.user1.id, 
            reason="Test transfer"
        )
        self.assertEqual(self.test_record.owner_id, self.user1)
        
        # Add co-owner
        self.test_record.with_user(self.user1).add_co_owner(
            self.user2.id,
            reason="Collaboration needed"
        )
        self.assertIn(self.user2, self.test_record.co_owner_ids)
        
        # Release ownership
        self.test_record.with_user(self.user1).release_ownership(
            reason="No longer needed"
        )
        self.assertFalse(self.test_record.owner_id)
        
        # Claim ownership
        self.test_record.with_user(self.user2).claim_ownership(
            reason="Taking over"
        )
        self.assertEqual(self.test_record.owner_id, self.user2)
    
    def test_assignment_permissions(self):
        """Test assignment permission logic"""
        # Owner should be able to assign
        self.test_record.owner_id = self.user1
        self.assertTrue(
            self.test_record.with_user(self.user1).can_assign
        )
        
        # Non-owner should not be able to assign
        self.assertFalse(
            self.test_record.with_user(self.user2).can_assign
        )
        
        # But if user2 is assigned, they should be able to assign others
        self.test_record.with_user(self.user1).assign_to_users(
            [self.user2.id],
            reason="Initial assignment"
        )
        self.assertTrue(
            self.test_record.with_user(self.user2).can_assign
        )
    
    def test_access_control(self):
        """Test access control functionality"""
        # Set restricted access
        self.test_record.access_level = 'restricted'
        self.test_record.owner_id = self.user1
        
        # Owner should have access
        self.assertTrue(
            self.test_record.with_user(self.user1).has_access
        )
        
        # Non-owner should not have access
        self.assertFalse(
            self.test_record.with_user(self.user2).has_access
        )
        
        # Grant access
        self.test_record.with_user(self.user1).grant_access(
            [self.user2.id],
            reason="Need review access"
        )
        self.assertTrue(
            self.test_record.with_user(self.user2).has_access
        )
    
    def test_responsibility_delegation(self):
        """Test responsibility delegation"""
        # Assign initial responsibility
        self.test_record.assign_responsibility(
            [self.user1.id],
            responsibility_type='primary',
            description="Primary responsibility"
        )
        
        # Delegate responsibility
        end_date = fields.Datetime.now() + timedelta(days=7)
        self.test_record.with_user(self.user1).delegate_responsibility(
            self.user2.id,
            end_date=end_date,
            reason="Vacation coverage"
        )
        
        # Check delegation
        self.assertEqual(
            self.test_record.responsibility_delegated_by,
            self.user1
        )
        self.assertIn(self.user2, self.test_record.responsible_user_ids)
    
    def test_logging(self):
        """Test that actions are properly logged"""
        initial_log_count = self.env['tk.ownership.log'].search_count([])
        
        # Perform ownership transfer
        self.test_record.transfer_ownership(
            self.user1.id,
            reason="Test logging"
        )
        
        # Check log was created
        new_log_count = self.env['tk.ownership.log'].search_count([])
        self.assertEqual(new_log_count, initial_log_count + 1)
        
        # Check log details
        log = self.env['tk.ownership.log'].search([], limit=1, order='id desc')
        self.assertEqual(log.action, 'transfer')
        self.assertEqual(log.new_owner_id, self.user1)
        self.assertEqual(log.reason, "Test logging")
```

These examples demonstrate practical implementation patterns and real-world usage scenarios for the Comprehensive Toolkit mixins. Each example shows how to combine the mixins effectively and leverage their features in different business contexts.
