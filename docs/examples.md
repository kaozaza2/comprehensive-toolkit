# Examples and Use Cases

## Introduction

This guide provides practical examples of implementing and using the Comprehensive Toolkit mixins in real-world scenarios. Each example includes complete code samples and explanations.

## Example 1: Project Task Management

### Model Implementation

```python
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _name = 'project.task.enhanced'
    _description = 'Enhanced Project Task'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.accessible.mixin',
        'tk.responsible.mixin'
    ]
    _order = 'priority desc, create_date desc'

    # Basic task fields
    name = fields.Char('Task Name', required=True, tracking=True)
    description = fields.Html('Description')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    
    # Task-specific fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], default='1', tracking=True)
    
    # Progress tracking
    progress = fields.Float('Progress (%)', default=0.0)
    estimated_hours = fields.Float('Estimated Hours')
    spent_hours = fields.Float('Spent Hours')
    
    # Dependencies
    depends_on_ids = fields.Many2many(
        'project.task.enhanced',
        'task_dependency_rel',
        'task_id', 'depends_on_id',
        string='Depends On'
    )
    
    # Custom business logic
    can_start = fields.Boolean('Can Start', compute='_compute_can_start')
    is_blocked = fields.Boolean('Is Blocked', compute='_compute_is_blocked')
    
    @api.depends('depends_on_ids.state')
    def _compute_is_blocked(self):
        for task in self:
            task.is_blocked = any(
                dep.state not in ['done', 'cancelled'] 
                for dep in task.depends_on_ids
            )
    
    @api.depends('is_blocked', 'state', 'is_assigned')
    def _compute_can_start(self):
        for task in self:
            task.can_start = (
                not task.is_blocked and 
                task.state == 'draft' and 
                task.is_assigned
            )
    
    def action_start(self):
        """Start working on the task"""
        if not self.can_start:
            raise ValidationError(_("Task cannot be started"))
        
        self.write({
            'state': 'in_progress',
            'progress': 5.0
        })
        
        # Start assignment tracking
        self.start_assignment(reason="Task started")
        
        return True
    
    def action_submit_for_review(self):
        """Submit task for review"""
        if self.state != 'in_progress':
            raise ValidationError(_("Only in-progress tasks can be submitted for review"))
        
        self.write({
            'state': 'review',
            'progress': 90.0
        })
        
        # Assign to project manager for review
        if self.project_id.user_id:
            self.assign_to_users(
                [self.project_id.user_id.id],
                reason="Task submitted for review"
            )
    
    def action_approve(self):
        """Approve and complete the task"""
        if self.state != 'review':
            raise ValidationError(_("Only tasks under review can be approved"))
        
        self.write({
            'state': 'done',
            'progress': 100.0
        })
        
        self.complete_assignment(reason="Task approved and completed")
```

### View Implementation

```xml
<!-- Form View -->
<record id="view_project_task_enhanced_form" model="ir.ui.view">
    <field name="name">project.task.enhanced.form</field>
    <field name="model">project.task.enhanced</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <!-- Workflow buttons -->
                <button name="action_start" string="Start Task" type="object" 
                        class="btn-primary" invisible="not can_start"/>
                <button name="action_submit_for_review" string="Submit for Review" 
                        type="object" class="btn-info" invisible="state != 'in_progress'"/>
                <button name="action_approve" string="Approve" type="object" 
                        class="btn-success" invisible="state != 'review'"/>
                
                <!-- Mixin actions -->
                <button name="%(comprehensive_toolkit.action_transfer_ownership_wizard)d" 
                        string="Transfer Ownership" type="action" 
                        invisible="not can_transfer"/>
                <button name="%(comprehensive_toolkit.action_bulk_assign_wizard)d" 
                        string="Assign Users" type="action" 
                        invisible="not can_assign"/>
                <button name="%(comprehensive_toolkit.action_delegate_responsibility_wizard)d" 
                        string="Delegate" type="action" 
                        invisible="not can_delegate"/>
                
                <field name="state" widget="statusbar" 
                       statusbar_visible="draft,in_progress,review,done"/>
            </header>
            <sheet>
                <div class="oe_button_box" name="button_box">
                    <button name="action_view_dependencies" type="object" 
                            class="oe_stat_button" icon="fa-link">
                        <field name="depends_on_ids" string="Dependencies" widget="statinfo"/>
                    </button>
                </div>
                
                <group>
                    <group>
                        <field name="name"/>
                        <field name="project_id"/>
                        <field name="priority"/>
                        <field name="progress" widget="progressbar"/>
                    </group>
                    <group>
                        <field name="estimated_hours"/>
                        <field name="spent_hours"/>
                        <field name="can_start"/>
                        <field name="is_blocked"/>
                    </group>
                </group>
                
                <field name="description"/>
                
                <notebook>
                    <!-- Task Details -->
                    <page string="Dependencies">
                        <field name="depends_on_ids"/>
                    </page>
                    
                    <!-- Ownership Management -->
                    <page string="Ownership">
                        <group>
                            <field name="owner_id"/>
                            <field name="co_owner_ids" widget="many2many_tags"/>
                            <field name="ownership_date"/>
                        </group>
                    </page>
                    
                    <!-- Assignment Details -->
                    <page string="Assignment">
                        <group>
                            <field name="assigned_user_ids" widget="many2many_tags"/>
                            <field name="assignment_deadline"/>
                            <field name="assignment_status"/>
                            <field name="assignment_priority"/>
                        </group>
                        <field name="assignment_description"/>
                    </page>
                    
                    <!-- Access Control -->
                    <page string="Access">
                        <group>
                            <field name="access_level"/>
                            <field name="allowed_user_ids" widget="many2many_tags"/>
                            <field name="custom_access_group_ids" widget="many2many_tags"/>
                        </group>
                    </page>
                    
                    <!-- Responsibility -->
                    <page string="Responsibility">
                        <group>
                            <field name="responsible_user_ids" widget="many2many_tags"/>
                            <field name="secondary_responsible_ids" widget="many2many_tags"/>
                            <field name="responsibility_type"/>
                        </group>
                    </page>
                </notebook>
            </sheet>
            <div class="oe_chatter">
                <field name="message_follower_ids"/>
                <field name="activity_ids"/>
                <field name="message_ids"/>
            </div>
        </form>
    </field>
</record>
```

### Usage Scenarios

**Scenario 1: Project Manager assigns tasks**
```python
# Create task
task = env['project.task.enhanced'].create({
    'name': 'Implement user authentication',
    'project_id': project.id,
    'description': 'Add OAuth2 authentication system',
    'estimated_hours': 40,
    'priority': '2'
})

# Assign to developers
task.assign_to_users(
    user_ids=[dev1.id, dev2.id],
    deadline=fields.Datetime.now() + timedelta(days=14),
    description="Please implement OAuth2 authentication",
    priority='high',
    reason="Critical feature for release"
)

# Set responsibility
task.assign_responsibility(
    user_ids=[tech_lead.id],
    responsibility_type='primary',
    description="Technical oversight and code review"
)
```

**Scenario 2: Developer workflow**
```python
# Developer starts task
task.action_start()

# Work in progress...
task.progress = 50

# Submit for review
task.action_submit_for_review()

# Tech lead reviews and approves
task.action_approve()
```

## Example 2: Document Management System

### Model Implementation

```python
class Document(models.Model):
    _name = 'document.management'
    _description = 'Document Management'
    _inherit = [
        'tk.ownable.mixin',
        'tk.accessible.mixin',
        'tk.accessible.group.mixin'
    ]
    
    name = fields.Char('Document Title', required=True)
    content = fields.Html('Content')
    document_type = fields.Selection([
        ('policy', 'Policy'),
        ('procedure', 'Procedure'),
        ('manual', 'Manual'),
        ('specification', 'Specification')
    ], required=True)
    
    version = fields.Char('Version', default='1.0')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived')
    ], default='draft')
    
    # Review workflow
    reviewer_ids = fields.Many2many('res.users', string='Reviewers')
    approver_id = fields.Many2one('res.users', string='Final Approver')
    review_deadline = fields.Date('Review Deadline')
    
    # File attachments
    attachment_ids = fields.One2many('ir.attachment', 'res_id', 
                                   domain=[('res_model', '=', 'document.management')])
    
    def action_submit_for_review(self):
        """Submit document for review"""
        if not self.reviewer_ids:
            raise ValidationError(_("Please assign reviewers before submitting"))
        
        # Assign reviewers
        self.assign_to_users(
            user_ids=self.reviewer_ids.ids,
            deadline=self.review_deadline,
            description="Please review this document",
            reason="Document submitted for review"
        )
        
        # Grant temporary access to reviewers
        for reviewer in self.reviewer_ids:
            self.grant_access_to_user(
                reviewer.id,
                start_date=fields.Datetime.now(),
                end_date=self.review_deadline,
                reason="Review access"
            )
        
        self.status = 'review'
    
    def action_approve(self):
        """Approve document"""
        if self.env.user != self.approver_id:
            raise ValidationError(_("Only the designated approver can approve this document"))
        
        self.write({
            'status': 'approved',
            'access_level': 'internal'  # Make approved docs generally accessible
        })
        
        # Complete review assignments
        self.complete_assignment(reason="Document approved")
```

### Usage Example

```python
# Create confidential document
doc = env['document.management'].create({
    'name': 'Employee Handbook 2024',
    'document_type': 'manual',
    'content': '<p>Company policies and procedures...</p>',
    'access_level': 'restricted',  # Start restricted
    'reviewer_ids': [(6, 0, [hr_manager.id, legal_counsel.id])],
    'approver_id': ceo.id
})

# Create HR team access group
hr_group = env['tk.accessible.group'].create({
    'name': 'HR Team',
    'description': 'Human Resources team members',
    'group_type': 'department',
    'user_ids': [(6, 0, hr_team_users.ids)]
})

# Grant access to HR team
doc.add_custom_access_group(hr_group.id, reason="HR document access")

# Submit for review
doc.action_submit_for_review()
```

## Example 3: Customer Support Ticket System

### Model Implementation

```python
class SupportTicket(models.Model):
    _name = 'support.ticket'
    _description = 'Support Ticket'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.responsible.mixin'
    ]
    
    name = fields.Char('Ticket Number', default=lambda self: self.env['ir.sequence'].next_by_code('support.ticket'))
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    subject = fields.Char('Subject', required=True)
    description = fields.Text('Description', required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='normal')
    
    status = fields.Selection([
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('waiting_customer', 'Waiting for Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], default='new')
    
    category_id = fields.Many2one('support.category', 'Category')
    team_id = fields.Many2one('support.team', 'Support Team')
    
    # SLA tracking
    response_deadline = fields.Datetime('Response Due')
    resolution_deadline = fields.Datetime('Resolution Due')
    first_response_date = fields.Datetime('First Response')
    resolution_date = fields.Datetime('Resolution Date')
    
    # Escalation
    escalation_level = fields.Integer('Escalation Level', default=0)
    escalated_to_ids = fields.Many2many('res.users', string='Escalated To')
    
    @api.model
    def create(self, vals):
        """Auto-assign based on category and set SLA deadlines"""
        ticket = super().create(vals)
        
        # Set SLA deadlines based on priority
        sla_hours = {
            'low': 24,
            'normal': 8,
            'high': 4,
            'critical': 1
        }
        
        hours = sla_hours.get(ticket.priority, 8)
        ticket.response_deadline = fields.Datetime.now() + timedelta(hours=hours)
        ticket.resolution_deadline = fields.Datetime.now() + timedelta(hours=hours*3)
        
        # Auto-assign to team
        if ticket.category_id and ticket.category_id.default_team_id:
            ticket.team_id = ticket.category_id.default_team_id
            ticket.assign_to_team()
        
        return ticket
    
    def assign_to_team(self):
        """Assign ticket to team members"""
        if not self.team_id:
            return
        
        # Assign to all team members
        self.assign_to_users(
            user_ids=self.team_id.member_ids.ids,
            deadline=self.response_deadline,
            description=f"New {self.priority} priority ticket: {self.subject}",
            priority=self.priority,
            reason="Auto-assignment to support team"
        )
        
        # Set team lead as responsible
        if self.team_id.leader_id:
            self.assign_responsibility(
                user_ids=[self.team_id.leader_id.id],
                responsibility_type='primary',
                description="Team lead responsibility for ticket resolution"
            )
        
        self.status = 'assigned'
    
    def action_take_ownership(self):
        """Support agent takes ownership of ticket"""
        self.transfer_ownership(
            self.env.user.id, 
            reason="Support agent taking ownership"
        )
        
        # Assign to self
        self.assign_to_users(
            [self.env.user.id],
            reason="Taking ownership of ticket"
        )
        
        self.status = 'in_progress'
        
        if not self.first_response_date:
            self.first_response_date = fields.Datetime.now()
    
    def action_escalate(self):
        """Escalate ticket to next level"""
        self.escalation_level += 1
        
        # Find escalation target based on level
        if self.escalation_level == 1:
            # Escalate to team leader
            target = self.team_id.leader_id
        elif self.escalation_level == 2:
            # Escalate to department manager
            target = self.team_id.department_id.manager_id
        else:
            # Escalate to support director
            target = self.env.ref('support.support_director')
        
        if target:
            # Delegate responsibility to escalation target
            self.delegate_responsibility(
                [target.id],
                reason=f"Escalation level {self.escalation_level}"
            )
            
            self.escalated_to_ids = [(4, target.id)]
    
    def action_resolve(self):
        """Mark ticket as resolved"""
        self.write({
            'status': 'resolved',
            'resolution_date': fields.Datetime.now()
        })
        
        self.complete_assignment(reason="Ticket resolved")
```

### Workflow Example

```python
# Customer creates ticket (via portal or API)
ticket = env['support.ticket'].create({
    'customer_id': customer.id,
    'subject': 'Login issues',
    'description': 'Cannot log into the system',
    'priority': 'high',
    'category_id': tech_support_category.id
})

# Ticket auto-assigned to tech support team
# Agent takes ownership
ticket.action_take_ownership()

# If issue is complex, escalate
if ticket.priority == 'critical' and ticket.escalation_level == 0:
    ticket.action_escalate()

# Resolve ticket
ticket.action_resolve()
```

## Example 4: Inventory Management

### Model Implementation

```python
class InventoryItem(models.Model):
    _name = 'inventory.item'
    _description = 'Inventory Item'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.accessible.mixin'
    ]
    
    name = fields.Char('Item Name', required=True)
    sku = fields.Char('SKU', required=True)
    category_id = fields.Many2one('product.category', 'Category')
    location_id = fields.Many2one('stock.location', 'Location')
    
    # Inventory details
    quantity_on_hand = fields.Float('Quantity on Hand')
    reserved_quantity = fields.Float('Reserved Quantity')
    available_quantity = fields.Float('Available', compute='_compute_available')
    
    # Ownership for tracking responsibility
    warehouse_manager_id = fields.Many2one('res.users', 'Warehouse Manager')
    
    # Assignment for tasks (counting, restocking, etc.)
    last_count_date = fields.Date('Last Count Date')
    next_count_date = fields.Date('Next Count Date')
    reorder_level = fields.Float('Reorder Level')
    
    needs_recount = fields.Boolean('Needs Recount', compute='_compute_needs_recount')
    needs_restock = fields.Boolean('Needs Restock', compute='_compute_needs_restock')
    
    @api.depends('quantity_on_hand', 'reserved_quantity')
    def _compute_available(self):
        for item in self:
            item.available_quantity = item.quantity_on_hand - item.reserved_quantity
    
    @api.depends('last_count_date')
    def _compute_needs_recount(self):
        today = fields.Date.today()
        for item in self:
            if not item.last_count_date:
                item.needs_recount = True
            else:
                days_since_count = (today - item.last_count_date).days
                item.needs_recount = days_since_count > 90  # Quarterly counts
    
    @api.depends('available_quantity', 'reorder_level')
    def _compute_needs_restock(self):
        for item in self:
            item.needs_restock = item.available_quantity <= item.reorder_level
    
    def action_schedule_count(self, count_date=None):
        """Schedule inventory count"""
        if not count_date:
            count_date = fields.Date.today() + timedelta(days=7)
        
        # Assign to warehouse staff
        warehouse_users = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('stock.group_stock_user').id])
        ])
        
        self.assign_to_users(
            user_ids=warehouse_users.ids,
            deadline=count_date,
            description=f"Physical count required for {self.name}",
            priority='normal',
            reason="Scheduled inventory count"
        )
        
        self.next_count_date = count_date
    
    def action_schedule_restock(self):
        """Schedule restocking"""
        if not self.needs_restock:
            return
        
        # Assign to purchasing team
        purchasing_users = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('purchase.group_purchase_user').id])
        ])
        
        self.assign_to_users(
            user_ids=purchasing_users.ids,
            deadline=fields.Date.today() + timedelta(days=3),
            description=f"Restock {self.name} - Current: {self.available_quantity}, Reorder: {self.reorder_level}",
            priority='high' if self.available_quantity <= 0 else 'normal',
            reason="Low stock level detected"
        )
```

### Automated Workflows

```python
# Cron job to check for low stock and schedule tasks
@api.model
def _cron_check_inventory_levels(self):
    # Find items needing restock
    low_stock_items = self.search([('needs_restock', '=', True)])
    for item in low_stock_items:
        item.action_schedule_restock()
    
    # Find items needing count
    recount_items = self.search([('needs_recount', '=', True)])
    for item in recount_items:
        item.action_schedule_count()
```

## Example 5: Contract Management

### Complete Implementation

```python
class Contract(models.Model):
    _name = 'contract.management'
    _description = 'Contract Management'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.accessible.mixin',
        'tk.responsible.mixin'
    ]
    
    name = fields.Char('Contract Name', required=True)
    partner_id = fields.Many2one('res.partner', 'Counterparty', required=True)
    contract_type = fields.Selection([
        ('service', 'Service Agreement'),
        ('supply', 'Supply Contract'),
        ('employment', 'Employment Contract'),
        ('nda', 'Non-Disclosure Agreement')
    ], required=True)
    
    # Contract lifecycle
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated')
    ], default='draft')
    
    # Important dates
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    signature_date = fields.Date('Signature Date')
    
    # Financial
    value = fields.Monetary('Contract Value')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Review and approval workflow
    legal_reviewer_id = fields.Many2one('res.users', 'Legal Reviewer')
    business_approver_id = fields.Many2one('res.users', 'Business Approver')
    final_approver_id = fields.Many2one('res.users', 'Final Approver')
    
    def action_submit_for_legal_review(self):
        """Submit contract for legal review"""
        if not self.legal_reviewer_id:
            raise ValidationError(_("Please assign a legal reviewer"))
        
        # Assign to legal reviewer
        self.assign_to_users(
            [self.legal_reviewer_id.id],
            deadline=fields.Date.today() + timedelta(days=5),
            description="Legal review required",
            priority='normal',
            reason="Contract submitted for legal review"
        )
        
        # Set legal team as responsible
        self.assign_responsibility(
            [self.legal_reviewer_id.id],
            responsibility_type='primary',
            description="Legal review and compliance check"
        )
        
        self.state = 'review'
    
    def action_approve_legal(self):
        """Legal approval"""
        if self.env.user != self.legal_reviewer_id:
            raise ValidationError(_("Only assigned legal reviewer can approve"))
        
        # Complete legal review assignment
        self.complete_assignment(reason="Legal review completed")
        
        # Assign to business approver
        if self.business_approver_id:
            self.assign_to_users(
                [self.business_approver_id.id],
                description="Business approval required",
                reason="Legal review completed, business approval needed"
            )
    
    def action_final_approval(self):
        """Final approval for contract"""
        self.state = 'approved'
        self.complete_assignment(reason="Contract approved")
        
        # Restrict access to authorized personnel only
        self.write({
            'access_level': 'restricted',
            'allowed_user_ids': [(6, 0, [
                self.owner_id.id,
                self.legal_reviewer_id.id,
                self.business_approver_id.id,
                self.final_approver_id.id
            ])]
        })
```

## Best Practices Summary

### 1. Model Design
- Always inherit mixins in logical order
- Add business-specific computed fields
- Implement proper workflow methods
- Use appropriate tracking on important fields

### 2. Security
- Start with restrictive access and open up as needed
- Use custom access groups for team-based access
- Implement proper record rules
- Log all important changes with reasons

### 3. User Experience
- Provide clear button labels and help text
- Use appropriate visibility conditions
- Include all mixin tabs in form views
- Add useful filters in search views

### 4. Performance
- Index frequently searched fields
- Optimize computed field calculations
- Use batch operations for bulk changes
- Consider database impact of many2many fields

### 5. Workflow Integration
- Combine mixin functionality with business logic
- Use assignments for task delegation
- Implement proper approval chains
- Provide escalation mechanisms

---

*These examples demonstrate the flexibility and power of the Comprehensive Toolkit mixins. Adapt them to your specific business requirements and extend as needed.*
