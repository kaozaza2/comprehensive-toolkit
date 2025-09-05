from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class AssignableMixin(models.AbstractModel):
    _name = 'tk.assignable.mixin'
    _description = 'Assignable Mixin - Provides assignment functionality'

    assigned_user_ids = fields.Many2many(
        'res.users',
        'record_assigned_users_rel',
        'record_id',
        'user_id',
        string='Assigned To',
        tracking=True,
        help="Users this record is assigned to"
    )
    assigner_id = fields.Many2one(
        'res.users',
        string='Assigned By',
        readonly=True,
        help="User who made the assignment"
    )
    assignment_date = fields.Datetime(
        string='Assignment Date',
        readonly=True,
        help="Date when the assignment was made"
    )
    assignment_deadline = fields.Datetime(
        string='Assignment Deadline',
        help="Deadline for completing the assignment"
    )
    is_assigned = fields.Boolean(
        string='Is Assigned',
        compute='_compute_is_assigned',
        store=True,
        help="Whether this record is assigned to someone"
    )
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        help="Whether the assignment is overdue"
    )
    can_assign = fields.Boolean(
        string='Can Assign',
        compute='_compute_can_assign',
        help="Whether current user can assign this record"
    )
    assignment_status = fields.Selection([
        ('unassigned', 'Unassigned'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Assignment Status', default='unassigned', tracking=True)
    assignment_description = fields.Text(
        string='Assignment Description',
        help="Description of what needs to be done"
    )
    assignment_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Assignment Priority', default='normal', tracking=True)
    assigned_user_count = fields.Integer(
        string='Number of Assigned Users',
        compute='_compute_assigned_user_count',
        help="Total number of users assigned to this record"
    )
    is_assigned_to_me = fields.Boolean(
        string='Assigned to Me',
        compute='_compute_is_assigned_to_me',
        search='_search_is_assigned_to_me',
        help="Whether current user is assigned to this record"
    )

    @api.depends('assigned_user_ids')
    def _compute_is_assigned(self):
        for record in self:
            record.is_assigned = bool(record.assigned_user_ids)

    @api.depends('assignment_deadline')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_overdue = (
                record.assignment_deadline and
                record.assignment_deadline < now and
                record.assignment_status in ['assigned', 'in_progress']
            )

    @api.depends('assigned_user_ids')
    def _compute_assigned_user_count(self):
        for record in self:
            record.assigned_user_count = len(record.assigned_user_ids)

    @api.depends('assigned_user_ids')
    def _compute_is_assigned_to_me(self):
        for record in self:
            record.is_assigned_to_me = self.env.user in record.assigned_user_ids

    def _compute_can_assign(self):
        for record in self:
            # Basic permission check
            has_basic_permission = (
                self.env.user.has_group('base.group_user') or
                self.env.user.has_group('base.group_system')
            )

            # Check if user is currently assigned
            is_assigned = self.env.user in record.assigned_user_ids

            # Check ownership if record has ownable mixin (including co-owners)
            has_ownership = False
            if hasattr(record, 'owner_id'):
                has_ownership = (
                    record.owner_id == self.env.user or
                    (hasattr(record, 'co_owner_ids') and self.env.user in record.co_owner_ids) or
                    not record.owner_id  # Unowned records can be assigned
                )

            # Check access permissions if record has accessible mixin
            has_access = True  # Default to True if no access control
            if hasattr(record, 'access_level'):
                if record.access_level == 'private' and hasattr(record, 'owner_id'):
                    has_access = (
                        record.owner_id == self.env.user or
                        (hasattr(record, 'co_owner_ids') and self.env.user in record.co_owner_ids)
                    )
                elif record.access_level == 'restricted':
                    has_access = (
                        self.env.user in record.allowed_user_ids or
                        any(group in self.env.user.groups_id for group in record.allowed_group_ids) or
                        (hasattr(record, 'owner_id') and record.owner_id == self.env.user) or
                        (hasattr(record, 'co_owner_ids') and self.env.user in record.co_owner_ids)
                    )
                    
                    # Check custom access groups if available
                    if not has_access and hasattr(record, 'custom_access_group_ids'):
                        for custom_group in record.custom_access_group_ids:
                            if custom_group.active and self.env.user in custom_group.user_ids:
                                has_access = True
                                break
                                
                elif record.access_level in ['internal', 'public']:
                    has_access = True

            # User can assign if they have basic permission AND (is assigned OR ownership OR access)
            record.can_assign = (
                has_basic_permission and
                (is_assigned or has_ownership or has_access or self.env.user.has_group('base.group_system'))
            )

    def assign_to_users(self, user_ids, deadline=None, description=None,
                       priority='normal', reason=None):
        """Assign record to multiple users"""
        if not self.can_assign and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("You don't have permission to assign this record."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified for assignment."))

        # Ensure user_ids is a list
        if not isinstance(user_ids, list):
            user_ids = [user_ids] if user_ids else []

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified for assignment."))

        old_assigned = self.assigned_user_ids

        # Assign to users
        vals = {
            'assigned_user_ids': [(6, 0, user_ids)],
            'assigner_id': self.env.user.id,
            'assignment_date': fields.Datetime.now(),
            'assignment_status': 'assigned',
            'assignment_priority': priority
        }
        if deadline:
            vals['assignment_deadline'] = deadline
        if description:
            vals['assignment_description'] = description

        self.write(vals)

        # Log the assignment
        self._log_assignment_change('assign_multiple', old_assigned, users, reason)

        return True

    def add_assignee(self, user_id, reason=None):
        """Add an assignee to the record"""
        if not self.can_assign:
            raise AccessError(_("You don't have permission to add assignees."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user not in self.assigned_user_ids:
            self.assigned_user_ids = [(4, user_id)]

            # If this is the first assignee, set metadata
            if len(self.assigned_user_ids) == 1:
                self.write({
                    'assignment_date': fields.Datetime.now(),
                    'assigner_id': self.env.user.id,
                    'assignment_status': 'assigned'
                })

            # Log the addition
            self._log_assignment_change('add_assignee', None, user, reason)

        return True

    def remove_assignee(self, user_id, reason=None):
        """Remove an assignee from the record"""
        if not self.can_assign:
            raise AccessError(_("You don't have permission to remove assignees."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user in self.assigned_user_ids:
            self.assigned_user_ids = [(3, user_id)]

            # If no more assignees, mark as unassigned
            if not self.assigned_user_ids:
                self.assignment_status = 'unassigned'

            # Log the removal
            self._log_assignment_change('remove_assignee', user, None, reason)

        return True

    def reassign_to_users(self, user_ids, reason=None):
        """Reassign record to different users"""
        if not self.can_assign:
            raise AccessError(_("You don't have permission to reassign this record."))

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified for reassignment."))

        old_assigned = self.assigned_user_ids

        # Reassign
        vals = {
            'assigned_user_ids': [(6, 0, user_ids)],
            'assigner_id': self.env.user.id,
            'assignment_date': fields.Datetime.now(),
            'assignment_status': 'assigned'
        }

        self.write(vals)

        # Log the reassignment
        self._log_assignment_change('reassign_multiple', old_assigned, users, reason)

        return True

    def unassign_all(self, reason=None):
        """Unassign all users from the record"""
        if not self.can_assign:
            raise AccessError(_("You don't have permission to unassign this record."))

        old_assigned = self.assigned_user_ids

        # Unassign all
        self.write({
            'assigned_user_ids': [(5, 0, 0)],
            'assignment_status': 'unassigned'
        })

        # Log the unassignment
        self._log_assignment_change('unassign_all', old_assigned, None, reason)

        return True

    def start_assignment(self, reason=None):
        """Mark assignment as in progress"""
        if self.env.user not in self.assigned_user_ids and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("You are not assigned to this record."))

        self.assignment_status = 'in_progress'

        # Log the start
        self._log_assignment_change('start', None, self.env.user, reason)

        return True

    def complete_assignment(self, reason=None):
        """Mark assignment as completed"""
        if self.env.user not in self.assigned_user_ids and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("You are not assigned to this record."))

        self.assignment_status = 'completed'

        # Log the completion
        self._log_assignment_change('complete', None, self.env.user, reason)

        return True

    def cancel_assignment(self, reason=None):
        """Cancel the assignment"""
        if not self.can_assign:
            raise AccessError(_("You don't have permission to cancel this assignment."))

        old_assigned = self.assigned_user_ids

        self.write({
            'assignment_status': 'cancelled',
            'assigned_user_ids': [(5, 0, 0)]
        })

        # Log the cancellation
        self._log_assignment_change('cancel', old_assigned, None, reason)

        return True

    def _log_assignment_change(self, action, old_users, new_users, reason):
        """Log assignment changes"""
        old_user_names = []
        new_user_names = []

        if old_users:
            if hasattr(old_users, '__iter__'):
                old_user_names = [user.name for user in old_users]
            else:
                old_user_names = [old_users.name]

        if new_users:
            if hasattr(new_users, '__iter__'):
                new_user_names = [user.name for user in new_users]
            else:
                new_user_names = [new_users.name]

        extra_info = ""
        if old_user_names:
            extra_info += f"Previous: {', '.join(old_user_names)}"
        if new_user_names:
            if extra_info:
                extra_info += " | "
            extra_info += f"New: {', '.join(new_user_names)}"

        self.env['tk.assignment.log'].create({
            'model_name': self._name,
            'res_id': self.id,
            'action': action,
            'old_assigned_user_id': old_users[0].id if old_users and len(old_users) > 0 else False,
            'new_assigned_user_id': new_users[0].id if new_users and len(new_users) > 0 else False,
            'reason': reason or '',
            'extra_info': extra_info,
            'user_id': self.env.user.id,
            'date': fields.Datetime.now()
        })

    def _search_is_assigned_to_me(self, operator, value):
        """Search method for is_assigned_to_me field"""
        if operator == '=' and value or operator == '!=' and not value:
            # Current user is assigned
            return [('assigned_user_ids', 'in', [self.env.user.id])]
        elif operator == '=' and not value or operator == '!=' and value:
            # Current user is NOT assigned
            return [('assigned_user_ids', 'not in', [self.env.user.id])]
        return []

    def _search_can_assign(self, operator, value):
        """Search method for can_assign field"""
        # This is a complex computed field, return basic domain
        if operator == '=' and value:
            # Records where user has some level of access
            domain = []
            if self.env.user.has_group('base.group_system'):
                domain = [('id', '!=', False)]  # System admin can assign any record
            else:
                # Basic users can assign records they're assigned to or own
                domain = ['|',
                         ('assigned_user_ids', 'in', [self.env.user.id]),
                         '|', ('owner_id', '=', self.env.user.id),
                         ('co_owner_ids', 'in', [self.env.user.id])]
            return domain
        elif operator == '=' and not value:
            # Records where user cannot assign (complex logic, return restrictive domain)
            return [('id', '=', False)]  # No records by default
        return []
