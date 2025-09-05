from odoo import models, fields, api, _


class ProjectTask(models.Model):
    _name = 'tk.project.task'
    _description = 'Project Task with Comprehensive Toolkit'
    _inherit = [
        'tk.ownable.mixin',
        'tk.assignable.mixin',
        'tk.accessible.mixin',
        'tk.accessible.group.mixin',
        'tk.responsible.mixin'
    ]
    _order = 'priority desc, create_date desc'

    # Basic fields
    name = fields.Char(string='Task Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    # Project specific fields
    project_id = fields.Many2one('tk.project', string='Project')
    milestone_id = fields.Many2one('tk.project.milestone', string='Milestone')
    task_type = fields.Selection([
        ('feature', 'Feature'),
        ('bug', 'Bug Fix'),
        ('improvement', 'Improvement'),
        ('documentation', 'Documentation'),
        ('testing', 'Testing')
    ], string='Task Type', default='feature')

    # Progress tracking
    progress = fields.Float(string='Progress (%)', default=0.0, help="Task completion percentage")
    estimated_hours = fields.Float(string='Estimated Hours')
    actual_hours = fields.Float(string='Actual Hours')

    # Dependencies
    depends_on_task_ids = fields.Many2many(
        'tk.project.task',
        'task_dependency_rel',
        'task_id',
        'depends_on_id',
        string='Depends On'
    )
    blocking_task_ids = fields.Many2many(
        'tk.project.task',
        'task_dependency_rel',
        'depends_on_id',
        'task_id',
        string='Blocking Tasks'
    )

    # Computed fields
    is_blocked = fields.Boolean(
        string='Is Blocked',
        compute='_compute_is_blocked',
        help="Whether this task is blocked by other tasks"
    )
    can_start = fields.Boolean(
        string='Can Start',
        compute='_compute_can_start',
        help="Whether this task can be started"
    )

    @api.depends('depends_on_task_ids.state')
    def _compute_is_blocked(self):
        for task in self:
            task.is_blocked = any(dep.state not in ['done', 'cancelled'] for dep in task.depends_on_task_ids)

    @api.depends('is_blocked', 'state')
    def _compute_can_start(self):
        for task in self:
            task.can_start = not task.is_blocked and task.state == 'draft'

    def action_start_task(self):
        """Start the task"""
        if not self.can_start:
            if self.is_blocked:
                raise ValidationError(_("Cannot start task - it is blocked by other tasks."))
            if self.state != 'draft':
                raise ValidationError(_("Task must be in draft state to start."))

        self.state = 'in_progress'
        if hasattr(self, 'start_assignment'):
            self.start_assignment(reason="Task started")

    def action_complete_task(self):
        """Complete the task"""
        if self.state != 'in_progress':
            raise ValidationError(_("Task must be in progress to complete."))

        self.write({
            'state': 'done',
            'progress': 100.0
        })
        if hasattr(self, 'complete_assignment'):
            self.complete_assignment(reason="Task completed")

    def action_review_task(self):
        """Send task for review"""
        if self.state != 'in_progress':
            raise ValidationError(_("Task must be in progress to send for review."))

        self.state = 'review'


class Project(models.Model):
    _name = 'tk.project'
    _description = 'Project with Comprehensive Toolkit'
    _inherit = [
        'tk.ownable.mixin',
        'tk.accessible.mixin',
        'tk.accessible.group.mixin',
        'tk.responsible.mixin'
    ]
    _order = 'create_date desc'

    # Basic fields
    name = fields.Char(string='Project Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='planning', tracking=True)

    # Project details
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    budget = fields.Monetary(string='Budget', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Related records
    task_ids = fields.One2many('tk.project.task', 'project_id', string='Tasks')
    milestone_ids = fields.One2many('tk.project.milestone', 'project_id', string='Milestones')

    # Computed fields
    task_count = fields.Integer(string='Task Count', compute='_compute_task_statistics')
    completed_task_count = fields.Integer(string='Completed Tasks', compute='_compute_task_statistics')
    progress = fields.Float(string='Progress (%)', compute='_compute_task_statistics')

    @api.depends('task_ids.state')
    def _compute_task_statistics(self):
        for project in self:
            total_tasks = len(project.task_ids)
            completed_tasks = len(project.task_ids.filtered(lambda t: t.state == 'done'))

            project.task_count = total_tasks
            project.completed_task_count = completed_tasks
            project.progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0


class ProjectMilestone(models.Model):
    _name = 'tk.project.milestone'
    _description = 'Project Milestone'
    _inherit = ['tk.accessible.mixin', 'tk.responsible.mixin']
    _order = 'deadline_date'

    name = fields.Char(string='Milestone Name', required=True)
    description = fields.Text(string='Description')
    project_id = fields.Many2one('tk.project', string='Project', required=True)
    deadline_date = fields.Date(string='Deadline Date')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('achieved', 'Achieved'),
        ('missed', 'Missed')
    ], string='Status', default='pending')


class Document(models.Model):
    _name = 'tk.document'
    _description = 'Document with Comprehensive Toolkit'
    _inherit = [
        'tk.ownable.mixin',
        'tk.accessible.mixin',
        'tk.accessible.group.mixin'
    ]
    _order = 'create_date desc'

    # Basic fields
    name = fields.Char(string='Document Name', required=True, tracking=True)
    content = fields.Html(string='Content')
    document_type = fields.Selection([
        ('policy', 'Policy'),
        ('procedure', 'Procedure'),
        ('manual', 'Manual'),
        ('report', 'Report'),
        ('specification', 'Specification'),
        ('other', 'Other')
    ], string='Document Type', default='other')

    # Document management
    version = fields.Char(string='Version', default='1.0')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True)

    # File attachment
    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                   domain=[('res_model', '=', 'tk.document')],
                                   string='Attachments')

    def action_submit_for_review(self):
        """Submit document for review"""
        if self.status != 'draft':
            raise ValidationError(_("Only draft documents can be submitted for review."))
        self.status = 'review'

    def action_approve(self):
        """Approve the document"""
        if self.status != 'review':
            raise ValidationError(_("Only documents under review can be approved."))
        self.status = 'approved'
