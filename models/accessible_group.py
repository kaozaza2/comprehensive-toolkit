from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class AccessibleGroupMixin(models.Model):
    _name = 'tk.accessible.group'
    _description = 'Custom Access Group for Records'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Group Name',
        required=True,
        help="Name of the access group"
    )
    description = fields.Text(
        string='Description',
        help="Description of what this group is for"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this group is active"
    )
    user_ids = fields.Many2many(
        'res.users',
        'tk_accessible_group_users_rel',
        'group_id',
        'user_id',
        string='Users',
        help="Users in this access group"
    )
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
        help="User who created this group"
    )
    created_date = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now,
        readonly=True,
        help="Date when this group was created"
    )
    group_type = fields.Selection([
        ('general', 'General Access'),
        ('project', 'Project Team'),
        ('department', 'Department'),
        ('temporary', 'Temporary Access'),
        ('external', 'External Users'),
        ('custom', 'Custom')
    ], string='Group Type', default='general', help="Type of access group")

    # Computed fields
    user_count = fields.Integer(
        string='Number of Users',
        compute='_compute_user_count',
        help="Total number of users in this group"
    )
    is_manager = fields.Boolean(
        string='Is Manager',
        compute='_compute_is_manager',
        search='_search_is_manager',
        help="Whether current user can manage this group"
    )

    # Access control fields
    manager_ids = fields.Many2many(
        'res.users',
        'tk_accessible_group_managers_rel',
        'group_id',
        'user_id',
        string='Group Managers',
        help="Users who can manage this group"
    )
    access_level = fields.Selection([
        ('public', 'Public - Anyone can see'),
        ('internal', 'Internal - Internal users can see'),
        ('restricted', 'Restricted - Only managers can see'),
        ('private', 'Private - Only creator can see')
    ], string='Visibility', default='internal', help="Who can see this group")

    # Temporary group fields
    is_temporary = fields.Boolean(
        string='Temporary Group',
        help="This group will expire after a certain date"
    )
    expiry_date = fields.Datetime(
        string='Expiry Date',
        help="Date when this group should be automatically archived"
    )

    @api.depends('user_ids')
    def _compute_user_count(self):
        for record in self:
            record.user_count = len(record.user_ids)

    @api.depends('created_by', 'manager_ids')
    def _compute_is_manager(self):
        for record in self:
            record.is_manager = (
                self.env.user.has_group('base.group_system') or
                record.created_by == self.env.user or
                self.env.user in record.manager_ids
            )

    def _search_is_manager(self, operator, value):
        """Search method for is_manager field"""
        if operator == '=' and value:
            # Return groups where current user is manager
            return [
                '|', '|',
                ('created_by', '=', self.env.user.id),
                ('manager_ids', 'in', [self.env.user.id]),
                ('created_by', '=', self.env.user.id)
            ]
        return []

    def add_user(self, user_id, reason=None):
        """Add a user to this group"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to add users to this group."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user not in self.user_ids:
            self.user_ids = [(4, user_id)]
            self._log_group_change('add_user', user, reason)

        return True

    def remove_user(self, user_id, reason=None):
        """Remove a user from this group"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to remove users from this group."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user in self.user_ids:
            self.user_ids = [(3, user_id)]
            self._log_group_change('remove_user', user, reason)

        return True

    def add_multiple_users(self, user_ids, reason=None):
        """Add multiple users to this group"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to add users to this group."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified."))

        # Ensure user_ids is a list
        if not isinstance(user_ids, list):
            user_ids = [user_ids] if user_ids else []

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified."))

        # Add users that aren't already in the group
        new_users = users.filtered(lambda u: u not in self.user_ids)
        if new_users:
            self.user_ids = [(4, user_id) for user_id in new_users.ids]
            user_names = ', '.join(new_users.mapped('name'))
            self._log_group_change('add_multiple_users', None, reason,
                                 extra_info=f"Added users: {user_names}")

        return True

    def remove_all_users(self, reason=None):
        """Remove all users from this group"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to remove users from this group."))

        if self.user_ids:
            user_names = ', '.join(self.user_ids.mapped('name'))
            self.user_ids = [(5, 0, 0)]
            self._log_group_change('remove_all_users', None, reason,
                                 extra_info=f"Removed all users: {user_names}")

        return True

    def add_manager(self, user_id, reason=None):
        """Add a group manager"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to add managers to this group."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user not in self.manager_ids:
            self.manager_ids = [(4, user_id)]
            self._log_group_change('add_manager', user, reason)

        return True

    def remove_manager(self, user_id, reason=None):
        """Remove a group manager"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to remove managers from this group."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        # Don't allow removing the creator unless there are other managers
        if user == self.created_by and len(self.manager_ids) <= 1:
            raise ValidationError(_("Cannot remove the creator unless there are other managers."))

        if user in self.manager_ids:
            self.manager_ids = [(3, user_id)]
            self._log_group_change('remove_manager', user, reason)

        return True

    def duplicate_group(self, name=None, include_users=True):
        """Duplicate this group"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to duplicate this group."))

        new_name = name or f"{self.name} (Copy)"
        vals = {
            'name': new_name,
            'description': f"Copy of {self.name}\n{self.description or ''}",
            'group_type': self.group_type,
            'access_level': self.access_level,
        }

        if include_users:
            vals['user_ids'] = [(6, 0, self.user_ids.ids)]

        new_group = self.create(vals)
        self._log_group_change('duplicate', None, f"Created duplicate: {new_name}")

        return new_group

    def archive_group(self, reason=None):
        """Archive this group"""
        if not self.is_manager:
            raise AccessError(_("You don't have permission to archive this group."))

        self.active = False
        self._log_group_change('archive', None, reason)

        return True

    def _log_group_change(self, action, target_user, reason, extra_info=None):
        """Log group changes"""
        # Create a simple log entry (you could enhance this with a dedicated log model)
        log_message = f"Group '{self.name}' - Action: {action}"
        if target_user:
            log_message += f" - User: {target_user.name}"
        if reason:
            log_message += f" - Reason: {reason}"
        if extra_info:
            log_message += f" - {extra_info}"

        # You could log this to a dedicated model or just use the mail thread
        self.message_post(body=log_message, message_type='notification')

    @api.model
    def create_project_group(self, project_name, user_ids, manager_ids=None):
        """Helper method to create a project access group"""
        vals = {
            'name': f"Project: {project_name}",
            'description': f"Access group for {project_name} project",
            'group_type': 'project',
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        }

        if manager_ids:
            vals['manager_ids'] = [(6, 0, manager_ids)]

        return self.create(vals)

    @api.model
    def create_department_group(self, department_name, user_ids, manager_ids=None):
        """Helper method to create a department access group"""
        vals = {
            'name': f"Department: {department_name}",
            'description': f"Access group for {department_name} department",
            'group_type': 'department',
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        }

        if manager_ids:
            vals['manager_ids'] = [(6, 0, manager_ids)]

        return self.create(vals)

    @api.model
    def create_temporary_group(self, purpose, user_ids, end_date=None):
        """Helper method to create a temporary access group"""
        description = f"Temporary access group for: {purpose}"
        if end_date:
            description += f"\nExpires: {end_date}"

        vals = {
            'name': f"Temp: {purpose}",
            'description': description,
            'group_type': 'temporary',
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        }
        return self.create(vals)
