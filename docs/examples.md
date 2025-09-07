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
            # Grant access to project managers
            managers = self.env.ref('project.group_project_manager').users
            task.grant_access(user_ids=managers.ids, reason="Critical task access")
        else:
            task.access_level = 'internal'
        
        # Assign responsibility to task creator
        task.assign_responsibility(
            user_ids=[self.env.user.id],
            description="Overall task completion and coordination",
            reason="Task creation"
        )
        
        return task
    
    def action_start_task(self):
        """Start task workflow with automatic assignments"""
        self.state = 'in_progress'
        
        # Assign to project team members
        if self.project_id and self.project_id.member_ids:
            self.assign_to_users(
                user_ids=self.project_id.member_ids.ids,
                deadline=fields.Datetime.now() + timedelta(days=7),
                priority='normal',
                description="Work on assigned task",
                reason="Task started"
            )
        
        # Add project manager as co-owner
        if self.project_id.user_id:
            self.add_co_owner(
                user_id=self.project_id.user_id.id,
                reason="Project manager oversight"
            )
    
    def action_submit_for_review(self):
        """Submit task for review with responsibility transfer"""
        self.state = 'review'
        
        # Transfer responsibility to project manager
        if self.project_id.user_id:
            self.transfer_responsibility(
                user_ids=[self.project_id.user_id.id],
                reason="Task submitted for review"
            )
        
        # Assign secondary responsibility to quality team
        quality_team = self.env.ref('project.group_project_quality', raise_if_not_found=False)
        if quality_team:
            self.assign_secondary_responsibility(
                user_ids=quality_team.users.ids,
                reason="Quality review backup"
            )
```

### Document Management System

```python
class DocumentManagement(models.Model):
    _name = 'example.document'
    _inherit = ['tk.ownable.mixin', 'tk.accessible.mixin', 'tk.responsible.mixin']
    _description = 'Document with Access Control'
    
    name = fields.Char('Document Name', required=True)
    content = fields.Html('Content')
    document_type = fields.Selection([
        ('public', 'Public Document'),
        ('internal', 'Internal Document'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret')
    ], required=True, default='internal')
    
    department_id = fields.Many2one('hr.department', 'Department')
    approval_required = fields.Boolean('Requires Approval', default=False)
    approved_by = fields.Many2one('res.users', 'Approved By', readonly=True)
    approval_date = fields.Datetime('Approval Date', readonly=True)
    
    @api.model
    def create(self, vals):
        """Setup document permissions based on type"""
        doc = super().create(vals)
        doc._setup_document_permissions()
        return doc
    
    def _setup_document_permissions(self):
        """Configure access and responsibility based on document type"""
        if self.document_type == 'public':
            self.access_level = 'public'
        elif self.document_type == 'internal':
            self.access_level = 'internal'
        elif self.document_type == 'confidential':
            self.access_level = 'restricted'
            # Only department members can access
            if self.department_id:
                self.grant_access(
                    user_ids=self.department_id.member_ids.ids,
                    reason="Department confidential document"
                )
        elif self.document_type == 'secret':
            self.access_level = 'private'
            # Only owner and managers
            managers = self.env.ref('base.group_system').users
            self.grant_access(user_ids=managers.ids, reason="Secret document access")
        
        # Assign responsibility for document maintenance
        self.assign_responsibility(
            user_ids=[self.owner_id.id],
            description="Document maintenance and updates",
            reason="Document ownership responsibility"
        )
        
        # If approval required, assign secondary responsibility to department manager
        if self.approval_required and self.department_id.manager_id:
            self.assign_secondary_responsibility(
                user_ids=[self.department_id.manager_id.id],
                reason="Approval responsibility"
            )
    
    def action_request_approval(self):
        """Request document approval"""
        if not self.department_id.manager_id:
            raise ValidationError(_("No department manager found for approval."))
        
        # Escalate responsibility to manager for approval
        self.escalate_responsibility(
            escalation_user_id=self.department_id.manager_id.id,
            reason="Document approval requested"
        )
        
        # Send notification (implement your notification logic)
        self._send_approval_notification()
    
    def action_approve(self):
        """Approve document"""
        if self.env.user not in self.responsible_user_ids:
            raise AccessError(_("Only responsible users can approve this document."))
        
        self.approved_by = self.env.user
        self.approval_date = fields.Datetime.now()
        
        # Transfer responsibility back to original owner
        self.transfer_responsibility(
            user_ids=[self.owner_id.id],
            reason="Document approved, responsibility returned to owner"
        )
```

### Customer Support Ticket System

```python
class SupportTicket(models.Model):
    _name = 'example.support.ticket'
    _inherit = ['tk.assignable.mixin', 'tk.responsible.mixin', 'tk.accessible.mixin']
    _description = 'Support Ticket with Escalation'
    
    name = fields.Char('Ticket Number', required=True, default='New')
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    subject = fields.Char('Subject', required=True)
    description = fields.Text('Description', required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal', required=True)
    
    state = fields.Selection([
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], default='new', tracking=True)
    
    category = fields.Selection([
        ('technical', 'Technical Issue'),
        ('billing', 'Billing Question'),
        ('feature', 'Feature Request'),
        ('complaint', 'Complaint')
    ], required=True)
    
    @api.model
    def create(self, vals):
        """Auto-assignment based on category and priority"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('support.ticket') or 'TKT-000'
        
        ticket = super().create(vals)
        ticket._auto_assign_ticket()
        return ticket
    
    def _auto_assign_ticket(self):
        """Automatically assign ticket based on category and priority"""
        # Set access level based on priority
        if self.priority == 'urgent':
            self.access_level = 'restricted'
            # Grant access to all support staff
            support_group = self.env.ref('support.group_support_team', raise_if_not_found=False)
            if support_group:
                self.grant_access(user_ids=support_group.users.ids, reason="Urgent ticket access")
        else:
            self.access_level = 'internal'
        
        # Auto-assign based on category
        if self.category == 'technical':
            tech_team = self.env.ref('support.group_technical_support', raise_if_not_found=False)
            if tech_team and tech_team.users:
                # Round-robin assignment to technical team
                available_users = tech_team.users.filtered(lambda u: u.active)
                if available_users:
                    assigned_user = available_users[len(self.search([])) % len(available_users)]
                    self.assign_to_users(
                        user_ids=[assigned_user.id],
                        deadline=self._get_sla_deadline(),
                        priority=self.priority,
                        description=f"Handle {self.category} support ticket",
                        reason="Auto-assignment based on category"
                    )
                    
                    # Assign responsibility
                    self.assign_responsibility(
                        user_ids=[assigned_user.id],
                        description="Primary responsibility for ticket resolution",
                        reason="Auto-assignment"
                    )
                    
                    self.state = 'assigned'
        
        elif self.category == 'billing':
            billing_team = self.env.ref('support.group_billing_support', raise_if_not_found=False)
            if billing_team and billing_team.users:
                self.assign_to_users(
                    user_ids=billing_team.users.ids,
                    deadline=self._get_sla_deadline(),
                    priority=self.priority,
                    reason="Billing category assignment"
                )
                
                # Assign responsibility to billing team lead
                team_lead = billing_team.users.filtered(lambda u: u.has_group('support.group_billing_lead'))
                if team_lead:
                    self.assign_responsibility(
                        user_ids=[team_lead[0].id],
                        description="Billing inquiry resolution",
                        reason="Team lead responsibility"
                    )
                
                self.state = 'assigned'
    
    def _get_sla_deadline(self):
        """Calculate SLA deadline based on priority"""
        now = fields.Datetime.now()
        if self.priority == 'urgent':
            return now + timedelta(hours=4)
        elif self.priority == 'high':
            return now + timedelta(hours=8)
        elif self.priority == 'normal':
            return now + timedelta(days=1)
        else:  # low
            return now + timedelta(days=3)
    
    def action_escalate(self):
        """Escalate ticket to supervisor"""
        if self.state != 'assigned':
            raise ValidationError(_("Only assigned tickets can be escalated."))
        
        # Find supervisor
        current_responsible = self.responsible_user_ids
        if current_responsible:
            # Find manager of current responsible user
            manager = current_responsible[0].parent_id
            if manager:
                self.escalate_responsibility(
                    escalation_user_id=manager.id,
                    reason="Ticket escalation to supervisor"
                )
                
                # Update priority and deadline
                if self.priority == 'normal':
                    self.priority = 'high'
                elif self.priority == 'high':
                    self.priority = 'urgent'
                
                # Update assignment deadline
                self.assignment_deadline = self._get_sla_deadline()
                self.state = 'escalated'
            else:
                raise ValidationError(_("No supervisor found for escalation."))
    
    def action_resolve(self):
        """Mark ticket as resolved"""
        if self.env.user not in self.responsible_user_ids:
            raise AccessError(_("Only responsible users can resolve tickets."))
        
        self.state = 'resolved'
        
        # Transfer responsibility to customer success for follow-up
        cs_team = self.env.ref('support.group_customer_success', raise_if_not_found=False)
        if cs_team and cs_team.users:
            self.transfer_responsibility(
                user_ids=[cs_team.users[0].id],
                reason="Ticket resolved, transferred for follow-up"
            )
```

## 🎯 Workflow Integration Examples

### Approval Workflow with Responsibility Chain

```python
class ApprovalRequest(models.Model):
    _name = 'example.approval.request'
    _inherit = ['tk.ownable.mixin', 'tk.responsible.mixin']
    _description = 'Multi-level Approval Request'
    
    name = fields.Char('Request Title', required=True)
    amount = fields.Float('Amount')
    description = fields.Text('Description')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('level1', 'Level 1 Approval'),
        ('level2', 'Level 2 Approval'),
        ('level3', 'Level 3 Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft', tracking=True)
    
    def action_submit(self):
        """Submit for approval with automatic responsibility assignment"""
        self.state = 'submitted'
        
        # Determine approval levels based on amount
        approval_chain = self._get_approval_chain()
        
        if approval_chain:
            # Assign responsibility to first approver
            first_approver = approval_chain[0]
            self.assign_responsibility(
                user_ids=[first_approver.id],
                description=f"Level 1 approval for {self.name}",
                end_date=fields.Datetime.now() + timedelta(days=3),
                reason="Approval workflow"
            )
            self.state = 'level1'
    
    def _get_approval_chain(self):
        """Get approval chain based on amount"""
        approvers = []
        
        # Level 1: Direct manager (up to $1000)
        if self.owner_id.parent_id:
            approvers.append(self.owner_id.parent_id)
        
        # Level 2: Department head (up to $10000)
        if self.amount > 1000:
            dept_head = self.env['hr.department'].search([
                ('member_ids', 'in', self.owner_id.id)
            ], limit=1).manager_id
            if dept_head and dept_head not in approvers:
                approvers.append(dept_head)
        
        # Level 3: Finance director (over $10000)
        if self.amount > 10000:
            finance_director = self.env.ref('hr.group_finance_director', raise_if_not_found=False)
            if finance_director and finance_director.users:
                approvers.append(finance_director.users[0])
        
        return approvers
    
    def action_approve(self):
        """Approve and move to next level or complete"""
        if self.env.user not in self.responsible_user_ids:
            raise AccessError(_("You are not authorized to approve this request."))
        
        approval_chain = self._get_approval_chain()
        current_level = len([s for s in ['level1', 'level2', 'level3'] if self.state.startswith(s)])
        
        if current_level < len(approval_chain):
            # Move to next approval level
            next_approver = approval_chain[current_level]
            next_level = f'level{current_level + 1}'
            
            self.transfer_responsibility(
                user_ids=[next_approver.id],
                reason=f"Approved at level {current_level}, moving to {next_level}"
            )
            self.state = next_level
        else:
            # Final approval
            self.state = 'approved'
            self.revoke_all_responsibility(reason="Request fully approved")
```

## 🔄 Batch Operations Examples

### Bulk Record Management

```python
def bulk_responsibility_operations():
    """Examples of bulk operations"""
    
    # Bulk assign responsibility to project tasks
    tasks = env['example.project.task'].search([('state', '=', 'draft')])
    
    # Group by project and assign to project managers
    projects = tasks.mapped('project_id')
    for project in projects:
        project_tasks = tasks.filtered(lambda t: t.project_id == project)
        if project.user_id:
            for task in project_tasks:
                task.assign_responsibility(
                    user_ids=[project.user_id.id],
                    description="Project management responsibility",
                    reason="Bulk assignment to project manager"
                )
    
    # Bulk transfer ownership for completed tasks
    completed_tasks = env['example.project.task'].search([('state', '=', 'done')])
    archive_user = env.ref('base.user_admin')
    
    for task in completed_tasks:
        task.transfer_ownership(
            new_owner_id=archive_user.id,
            reason="Task completed - archived"
        )
    
    # Bulk escalation for overdue items
    overdue_tickets = env['example.support.ticket'].search([
        ('assignment_deadline', '<', fields.Datetime.now()),
        ('state', 'in', ['assigned', 'in_progress'])
    ])
    
    for ticket in overdue_tickets:
        if ticket.responsible_user_ids:
            manager = ticket.responsible_user_ids[0].parent_id
            if manager:
                ticket.escalate_responsibility(
                    escalation_user_id=manager.id,
                    reason="Overdue ticket escalation"
                )
```

## 🎛️ Dashboard Integration Examples

```python
class CustomDashboardMetrics(models.Model):
    _inherit = 'tk.dashboard'
    
    def get_custom_metrics(self):
        """Add custom business metrics"""
        metrics = super().get_custom_metrics()
        
        # Support ticket metrics
        tickets = self.env['example.support.ticket'].search([])
        metrics.update({
            'support_tickets_total': len(tickets),
            'support_tickets_urgent': len(tickets.filtered(lambda t: t.priority == 'urgent')),
            'support_tickets_overdue': len(tickets.filtered(
                lambda t: t.assignment_deadline and t.assignment_deadline < fields.Datetime.now()
            )),
            'support_tickets_my_responsibility': len(tickets.filtered(
                lambda t: self.env.user in t.responsible_user_ids
            )),
        })
        
        # Project task metrics
        tasks = self.env['example.project.task'].search([])
        metrics.update({
            'project_tasks_total': len(tasks),
            'project_tasks_in_progress': len(tasks.filtered(lambda t: t.state == 'in_progress')),
            'project_tasks_my_ownership': len(tasks.filtered('is_owned_by_me')),
            'project_tasks_my_responsibility': len(tasks.filtered(
                lambda t: self.env.user in t.responsible_user_ids
            )),
        })
        
        # Document metrics
        documents = self.env['example.document'].search([])
        metrics.update({
            'documents_total': len(documents),
            'documents_pending_approval': len(documents.filtered(
                lambda d: d.approval_required and not d.approved_by
            )),
            'documents_confidential': len(documents.filtered(
                lambda d: d.document_type in ['confidential', 'secret']
            )),
        })
        
        return metrics
```

## 🧪 Testing Examples

```python
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, ValidationError
from datetime import timedelta

class TestToolkitIntegration(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.user1 = self.env['res.users'].create({
            'name': 'Test User 1',
            'login': 'user1@test.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        self.user2 = self.env['res.users'].create({
            'name': 'Test User 2', 
            'login': 'user2@test.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        self.manager = self.env['res.users'].create({
            'name': 'Manager',
            'login': 'manager@test.com', 
            'groups_id': [(6, 0, [self.env.ref('base.group_system').id])]
        })
    
    def test_task_workflow(self):
        """Test complete task workflow"""
        # Create task
        task = self.env['example.project.task'].with_user(self.user1).create({
            'name': 'Test Task',
            'description': 'Test task description',
            'priority': 'normal'
        })
        
        # Verify auto-ownership
        self.assertEqual(task.owner_id, self.user1)
        self.assertIn(self.user1, task.responsible_user_ids)
        
        # Start task
        task.action_start_task()
        self.assertEqual(task.state, 'in_progress')
        
        # Submit for review
        task.action_submit_for_review()
        self.assertEqual(task.state, 'review')
    
    def test_responsibility_escalation(self):
        """Test responsibility escalation workflow"""
        ticket = self.env['example.support.ticket'].create({
            'customer_id': self.env['res.partner'].create({'name': 'Test Customer'}).id,
            'subject': 'Test Issue',
            'description': 'Test description',
            'category': 'technical',
            'priority': 'normal'
        })
        
        # Assign responsibility
        ticket.assign_responsibility(
            user_ids=[self.user1.id],
            reason="Initial assignment"
        )
        
        # Escalate to manager
        ticket.with_user(self.user1).escalate_responsibility(
            escalation_user_id=self.manager.id,
            reason="Need manager attention"
        )
        
        self.assertEqual(ticket.responsible_user_ids, self.manager)
        self.assertFalse(ticket.secondary_responsible_ids)
    
    def test_access_control_integration(self):
        """Test access control with other mixins"""
        doc = self.env['example.document'].with_user(self.user1).create({
            'name': 'Confidential Document',
            'content': '<p>Secret content</p>',
            'document_type': 'confidential'
        })
        
        # Verify restricted access
        self.assertEqual(doc.access_level, 'restricted')
        
        # Test access denial
        with self.assertRaises(AccessError):
            doc.with_user(self.user2).read(['content'])
        
        # Grant access
        doc.grant_access(user_ids=[self.user2.id], reason="Project collaboration")
        
        # Verify access granted
        content = doc.with_user(self.user2).read(['content'])
        self.assertTrue(content)
```

These examples demonstrate practical implementations of the Comprehensive Toolkit mixins in real-world scenarios, showing how to combine multiple mixins for complex business requirements.

## 🔒 Advanced Access Control Examples

### Document Management with Classification-Based Access

```python
class ConfidentialDocument(models.Model):
    _name = 'confidential.document'
    _inherit = ['tk.ownable.mixin', 'tk.accessible.mixin', 'tk.accessible.group.mixin']
    _description = 'Document with Advanced Access Control'
    
    name = fields.Char('Document Title', required=True)
    content = fields.Html('Content')
    classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use Only'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret')
    ], required=True, default='internal')
    
    department_id = fields.Many2one('hr.department', 'Department')
    security_clearance_required = fields.Selection([
        ('none', 'None'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret')
    ], compute='_compute_security_clearance_required', store=True)
    
    @api.depends('classification')
    def _compute_security_clearance_required(self):
        mapping = {
            'public': 'none',
            'internal': 'none',
            'confidential': 'confidential',
            'secret': 'secret',
            'top_secret': 'top_secret'
        }
        for doc in self:
            doc.security_clearance_required = mapping.get(doc.classification, 'none')
    
    @api.model
    def create(self, vals):
        """Auto-setup access control based on classification"""
        doc = super().create(vals)
        doc._setup_classification_access()
        return doc
    
    def _setup_classification_access(self):
        """Configure access based on document classification"""
        if self.classification == 'public':
            self.set_access_level('public', reason="Public document")
            
        elif self.classification == 'internal':
            self.set_access_level('internal', reason="Internal document")
            
        elif self.classification == 'confidential':
            self.set_access_level('restricted', reason="Confidential document")
            
            # Create department access group if applicable
            if self.department_id:
                dept_group = self._get_or_create_department_group()
                self.grant_access_to_custom_group(dept_group.id, reason="Department confidential access")
            
            # Grant access to users with confidential clearance
            cleared_users = self.env['res.users'].search([
                ('security_clearance', 'in', ['confidential', 'secret', 'top_secret'])
            ])
            if cleared_users:
                self.bulk_grant_access_to_users(cleared_users.ids, reason="Security clearance")
                
        elif self.classification in ['secret', 'top_secret']:
            self.set_access_level('private', reason=f"{self.classification.title()} document")
            
            # Only users with appropriate clearance
            required_clearances = ['secret', 'top_secret'] if self.classification == 'secret' else ['top_secret']
            cleared_users = self.env['res.users'].search([
                ('security_clearance', 'in', required_clearances)
            ])
            if cleared_users:
                self.bulk_grant_access_to_users(cleared_users.ids, reason="Security clearance required")
                
            # Create secure access group
            secure_group = self.env['tk.accessible.group'].create({
                'name': f'{self.classification.title()} Access - {self.name}',
                'group_type': 'custom',
                'description': f'Secure access group for {self.classification} document',
                'user_ids': [(6, 0, cleared_users.ids)]
            })
            self.grant_access_to_custom_group(secure_group.id, reason="Secure document access")
    
    def _get_or_create_department_group(self):
        """Get or create department access group"""
        group_name = f"Department Access - {self.department_id.name}"
        existing_group = self.env['tk.accessible.group'].search([
            ('name', '=', group_name),
            ('group_type', '=', 'department')
        ], limit=1)
        
        if existing_group:
            return existing_group
        
        return self.env['tk.accessible.group'].create_department_group(
            self.department_id.name,
            self.department_id.member_ids.ids
        )
    
    def action_declassify(self):
        """Declassify document and update access"""
        if self.classification not in ['secret', 'top_secret']:
            raise ValidationError(_("Only secret/top secret documents can be declassified"))
        
        # Clear existing access
        self.clear_all_custom_groups(reason="Document declassification")
        
        # Set to internal access
        self.classification = 'internal'
        self.set_access_level('internal', reason="Document declassified")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Document has been declassified and is now available to all internal users'),
                'type': 'success'
            }
        }
```

### Project-Based Access Management System

```python
class ProjectWorkspace(models.Model):
    _name = 'project.workspace'
    _inherit = ['tk.ownable.mixin', 'tk.accessible.mixin', 'tk.accessible.group.mixin', 'tk.responsible.mixin']
    _description = 'Project Workspace with Dynamic Access Control'
    
    name = fields.Char('Project Name', required=True)
    description = fields.Text('Description')
    project_type = fields.Selection([
        ('internal', 'Internal Project'),
        ('client', 'Client Project'),
        ('confidential', 'Confidential Project'),
        ('partnership', 'Partnership Project')
    ], required=True, default='internal')
    
    # Team structure
    project_manager_id = fields.Many2one('res.users', 'Project Manager', required=True)
    team_lead_ids = fields.Many2many('res.users', 'project_team_leads_rel', string='Team Leads')
    team_member_ids = fields.Many2many('res.users', 'project_team_members_rel', string='Team Members')
    stakeholder_ids = fields.Many2many('res.users', 'project_stakeholders_rel', string='Stakeholders')
    client_contact_ids = fields.Many2many('res.users', 'project_client_contacts_rel', string='Client Contacts')
    
    # Access groups (computed)
    core_team_group_id = fields.Many2one('tk.accessible.group', 'Core Team Group', readonly=True)
    extended_team_group_id = fields.Many2one('tk.accessible.group', 'Extended Team Group', readonly=True)
    stakeholder_group_id = fields.Many2one('tk.accessible.group', 'Stakeholder Group', readonly=True)
    client_group_id = fields.Many2one('tk.accessible.group', 'Client Group', readonly=True)
    
    @api.model
    def create(self, vals):
        """Setup project access structure on creation"""
        project = super().create(vals)
        project._setup_project_access_structure()
        return project
    
    def write(self, vals):
        """Update access groups when team changes"""
        result = super().write(vals)
        
        # Check if team composition changed
        team_fields = ['project_manager_id', 'team_lead_ids', 'team_member_ids', 
                      'stakeholder_ids', 'client_contact_ids']
        if any(field in vals for field in team_fields):
            self._update_project_access_groups()
        
        return result
    
    def _setup_project_access_structure(self):
        """Create and configure all project access groups"""
        # Set ownership
        self.owner_id = self.project_manager_id
        self.assign_responsibility([self.project_manager_id.id], 
                                 description="Project management and oversight",
                                 reason="Project manager responsibility")
        
        # Create core team group (PM + Team Leads)
        core_team_users = self.project_manager_id | self.team_lead_ids
        self.core_team_group_id = self.env['tk.accessible.group'].create({
            'name': f'Core Team - {self.name}',
            'group_type': 'project',
            'description': f'Core team for project {self.name}',
            'user_ids': [(6, 0, core_team_users.ids)]
        })
        
        # Create extended team group (Core + Members)
        extended_team_users = core_team_users | self.team_member_ids
        self.extended_team_group_id = self.env['tk.accessible.group'].create({
            'name': f'Extended Team - {self.name}',
            'group_type': 'project',
            'description': f'Extended team for project {self.name}',
            'user_ids': [(6, 0, extended_team_users.ids)]
        })
        
        # Create stakeholder group
        if self.stakeholder_ids:
            self.stakeholder_group_id = self.env['tk.accessible.group'].create({
                'name': f'Stakeholders - {self.name}',
                'group_type': 'custom',
                'description': f'Stakeholders for project {self.name}',
                'user_ids': [(6, 0, self.stakeholder_ids.ids)]
            })
        
        # Create client group for client projects
        if self.project_type == 'client' and self.client_contact_ids:
            self.client_group_id = self.env['tk.accessible.group'].create({
                'name': f'Client Access - {self.name}',
                'group_type': 'external',
                'description': f'Client access for project {self.name}',
                'user_ids': [(6, 0, self.client_contact_ids.ids)]
            })
        
        # Configure access based on project type
        self._configure_project_access_levels()
    
    def _configure_project_access_levels(self):
        """Configure access levels based on project type"""
        if self.project_type == 'internal':
            self.set_access_level('internal', reason="Internal project")
            
        elif self.project_type == 'client':
            self.set_access_level('restricted', reason="Client project - controlled access")
            
            # Grant access to extended team
            self.grant_access_to_custom_group(self.extended_team_group_id.id, 
                                           reason="Project team access")
            
            # Grant limited access to stakeholders
            if self.stakeholder_group_id:
                self.grant_access_to_custom_group(self.stakeholder_group_id.id,
                                               reason="Stakeholder visibility")
            
            # Grant access to client contacts
            if self.client_group_id:
                self.grant_access_to_custom_group(self.client_group_id.id,
                                               reason="Client collaboration")
                
        elif self.project_type == 'confidential':
            self.set_access_level('private', reason="Confidential project")
            
            # Only core team has access
            self.grant_access_to_custom_group(self.core_team_group_id.id,
                                           reason="Confidential project - core team only")
            
        elif self.project_type == 'partnership':
            self.set_access_level('restricted', reason="Partnership project")
            
            # Extended team + stakeholders
            self.grant_access_to_custom_group(self.extended_team_group_id.id,
                                           reason="Partnership team access")
            if self.stakeholder_group_id:
                self.grant_access_to_custom_group(self.stakeholder_group_id.id,
                                               reason="Partnership stakeholder access")
    
    def _update_project_access_groups(self):
        """Update access groups when team composition changes"""
        # Update core team group
        if self.core_team_group_id:
            core_team_users = self.project_manager_id | self.team_lead_ids
            self.core_team_group_id.user_ids = [(6, 0, core_team_users.ids)]
        
        # Update extended team group
        if self.extended_team_group_id:
            extended_team_users = self.project_manager_id | self.team_lead_ids | self.team_member_ids
            self.extended_team_group_id.user_ids = [(6, 0, extended_team_users.ids)]
        
        # Update stakeholder group
        if self.stakeholder_group_id and self.stakeholder_ids:
            self.stakeholder_group_id.user_ids = [(6, 0, self.stakeholder_ids.ids)]
        elif not self.stakeholder_ids and self.stakeholder_group_id:
            # Archive group if no stakeholders
            self.stakeholder_group_id.active = False
        
        # Update client group
        if self.client_group_id and self.client_contact_ids:
            self.client_group_id.user_ids = [(6, 0, self.client_contact_ids.ids)]
        elif not self.client_contact_ids and self.client_group_id:
            self.client_group_id.active = False
    
    def action_promote_to_core_team(self):
        """Wizard to promote team members to core team"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Promote to Core Team'),
            'res_model': 'project.team.promotion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_available_users': self.team_member_ids.ids
            }
        }
    
    def action_grant_temporary_access(self):
        """Grant temporary access to external users"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Grant Temporary Access'),
            'res_model': 'tk.accessible.group.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_type': 'temporary',
                'default_is_temporary': True,
                'default_name': f'Temporary Access - {self.name}',
                'default_active_model': self._name,
                'default_active_id': self.id
            }
        }
```

### Healthcare Patient Records with Privacy Controls

```python
class PatientRecord(models.Model):
    _name = 'healthcare.patient.record'
    _inherit = ['tk.accessible.mixin', 'tk.accessible.group.mixin']
    _description = 'Patient Record with HIPAA Compliance'
    
    patient_id = fields.Many2one('res.partner', 'Patient', required=True)
    record_type = fields.Selection([
        ('general', 'General Medical'),
        ('mental_health', 'Mental Health'),
        ('substance_abuse', 'Substance Abuse'),
        ('genetic', 'Genetic Information'),
        ('research', 'Research Data')
    ], required=True)
    
    # Medical team
    primary_physician_id = fields.Many2one('res.users', 'Primary Physician', required=True)
    attending_physician_ids = fields.Many2many('res.users', 'patient_attending_rel', string='Attending Physicians')
    nurse_ids = fields.Many2many('res.users', 'patient_nurse_rel', string='Assigned Nurses')
    specialist_ids = fields.Many2many('res.users', 'patient_specialist_rel', string='Consulting Specialists')
    
    # Privacy settings
    patient_consent_level = fields.Selection([
        ('minimal', 'Minimal Sharing'),
        ('treatment_team', 'Treatment Team Only'),
        ('department', 'Department Wide'),
        ('research_approved', 'Research Approved')
    ], default='treatment_team', required=True)
    
    emergency_access_enabled = fields.Boolean('Emergency Access Enabled', default=True)
    research_participation = fields.Boolean('Research Participation Consent', default=False)
    
    @api.model
    def create(self, vals):
        """Setup HIPAA-compliant access on creation"""
        record = super().create(vals)
        record._setup_hipaa_access()
        return record
    
    def _setup_hipaa_access(self):
        """Configure access based on HIPAA requirements and patient consent"""
        # Always private by default for healthcare records
        self.set_access_level('private', reason="HIPAA compliance - patient privacy")
        
        # Create primary care team group
        care_team_users = self.primary_physician_id | self.attending_physician_ids | self.nurse_ids
        if care_team_users:
            care_team_group = self.env['tk.accessible.group'].create({
                'name': f'Care Team - {self.patient_id.name}',
                'group_type': 'custom',
                'description': f'Primary care team for patient {self.patient_id.name}',
                'user_ids': [(6, 0, care_team_users.ids)]
            })
            self.grant_access_to_custom_group(care_team_group.id, reason="Primary care team access")
        
        # Handle consent-based access
        if self.patient_consent_level == 'minimal':
            # Only primary physician
            if self.primary_physician_id:
                self.grant_access_to_user(self.primary_physician_id.id, reason="Primary physician - minimal consent")
                
        elif self.patient_consent_level == 'treatment_team':
            # Primary care team already granted above
            pass
            
        elif self.patient_consent_level == 'department':
            # Add department-wide access
            department = self.primary_physician_id.department_id
            if department:
                dept_group = self._get_or_create_medical_department_group(department)
                self.grant_access_to_custom_group(dept_group.id, reason="Department consent level")
                
        elif self.patient_consent_level == 'research_approved':
            # Add research team access if participating
            if self.research_participation:
                research_group = self.env.ref('healthcare.group_research_team', raise_if_not_found=False)
                if research_group:
                    self.grant_access_to_group(research_group.id, reason="Research participation consent")
        
        # Handle specialist access
        if self.specialist_ids:
            specialist_group = self.env['tk.accessible.group'].create({
                'name': f'Specialists - {self.patient_id.name}',
                'group_type': 'temporary',
                'description': f'Consulting specialists for patient {self.patient_id.name}',
                'user_ids': [(6, 0, self.specialist_ids.ids)]
            })
            self.grant_access_to_custom_group(specialist_group.id, reason="Specialist consultation")
        
        # Configure record type specific access
        self._setup_record_type_access()
    
    def _setup_record_type_access(self):
        """Setup access based on record type sensitivity"""
        if self.record_type == 'mental_health':
            # More restrictive access for mental health records
            mental_health_group = self.env.ref('healthcare.group_mental_health', raise_if_not_found=False)
            if mental_health_group:
                # Clear existing access and grant only to mental health professionals
                self.revoke_access_from_custom_group()
                self.grant_access_to_group(mental_health_group.id, reason="Mental health record - specialized access")
                
        elif self.record_type == 'substance_abuse':
            # Federal regulations require special handling
            substance_abuse_group = self.env.ref('healthcare.group_substance_abuse', raise_if_not_found=False)
            if substance_abuse_group:
                self.grant_access_to_group(substance_abuse_group.id, reason="Substance abuse treatment - federal compliance")
                
        elif self.record_type == 'genetic':
            # Genetic counselors and authorized physicians only
            genetic_group = self.env.ref('healthcare.group_genetic_counseling', raise_if_not_found=False)
            if genetic_group:
                self.grant_access_to_group(genetic_group.id, reason="Genetic information - specialized access")
    
    def action_emergency_access(self):
        """Grant emergency access to record"""
        if not self.emergency_access_enabled:
            raise ValidationError(_("Emergency access is not enabled for this patient"))
        
        # Grant access to emergency team
        emergency_group = self.env.ref('healthcare.group_emergency_team', raise_if_not_found=False)
        if emergency_group:
            # Grant time-limited access (24 hours)
            end_time = fields.Datetime.now() + timedelta(hours=24)
            self.grant_access_to_group(emergency_group.id, 
                                     start_date=fields.Datetime.now(),
                                     end_date=end_time,
                                     reason="Emergency access granted")
            
            # Log emergency access
            self.env['healthcare.emergency.access.log'].create({
                'patient_record_id': self.id,
                'granted_by': self.env.user.id,
                'access_reason': 'Emergency medical situation',
                'granted_date': fields.Datetime.now(),
                'expiry_date': end_time
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Emergency access granted for 24 hours'),
                'type': 'warning',
                'sticky': True
            }
        }
    
    def action_patient_consent_update(self):
        """Update patient consent and adjust access accordingly"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Update Patient Consent'),
            'res_model': 'healthcare.patient.consent.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_record_id': self.id,
                'default_current_consent_level': self.patient_consent_level,
                'default_research_participation': self.research_participation
            }
        }
```

These examples demonstrate advanced access control scenarios with real-world complexity including security clearances, project team management, and HIPAA compliance.
