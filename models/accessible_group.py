from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccessibleGroup(models.Model):
    _name = 'tk.accessible.group'
    _description = 'Custom Access Group'
    _order = 'name'

    name = fields.Char('Group Name', required=True)
    description = fields.Text('Description')

    group_type = fields.Selection([
        ('project', 'Project Team'),
        ('department', 'Department'),
        ('temporary', 'Temporary Access'),
        ('custom', 'Custom Group')
    ], string='Group Type', default='custom', required=True)

    user_ids = fields.Many2many(
        'res.users',
        'accessible_group_user_rel',
        'group_id',
        'user_id',
        string='Users',
        help="Users in this access group"
    )

    active = fields.Boolean('Active', default=True)

    # Metadata
    create_date = fields.Datetime('Created On', readonly=True)
    create_uid = fields.Many2one('res.users', 'Created By', readonly=True)
    write_date = fields.Datetime('Last Modified On', readonly=True)
    write_uid = fields.Many2one('res.users', 'Last Modified By', readonly=True)

    # Computed fields
    user_count = fields.Integer('User Count', compute='_compute_user_count', store=True)

    @api.depends('user_ids')
    def _compute_user_count(self):
        for group in self:
            group.user_count = len(group.user_ids)

    @api.constrains('user_ids')
    def _check_user_ids(self):
        for group in self:
            if group.active and not group.user_ids:
                raise ValidationError(_("Active access groups must have at least one user."))

    def name_get(self):
        result = []
        for group in self:
            name = f"{group.name} ({group.user_count} users)"
            result.append((group.id, name))
        return result

    def add_users(self, user_ids, reason=None):
        """Add users to the access group"""
        if not user_ids:
            return False

        users = self.env['res.users'].browse(user_ids)
        existing_users = users.filtered(lambda u: u in self.user_ids)
        new_users = users - existing_users

        if new_users:
            self.user_ids = [(4, user_id) for user_id in new_users.ids]
            # Log the addition if needed
            self._log_group_change('add_users', new_users, reason)

        return True

    def remove_users(self, user_ids, reason=None):
        """Remove users from the access group"""
        if not user_ids:
            return False

        users = self.env['res.users'].browse(user_ids)
        existing_users = users.filtered(lambda u: u in self.user_ids)

        if existing_users:
            self.user_ids = [(3, user_id) for user_id in existing_users.ids]
            # Log the removal if needed
            self._log_group_change('remove_users', existing_users, reason)

        return True

    def _log_group_change(self, action, users, reason):
        """Log changes to the access group"""
        # This would integrate with the access logging system
        # For now, we'll keep it simple
        pass

    def toggle_active(self):
        """Toggle the active state of the group"""
        for group in self:
            group.active = not group.active

    @api.model
    def create_project_team_group(self, project_name, user_ids):
        """Create a project team access group"""
        return self.create({
            'name': f"Project Team - {project_name}",
            'description': f"Access group for {project_name} project team members",
            'group_type': 'project',
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        })

    @api.model
    def create_department_group(self, department_name, user_ids):
        """Create a department access group"""
        return self.create({
            'name': f"Department - {department_name}",
            'description': f"Access group for {department_name} department",
            'group_type': 'department',
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        })
