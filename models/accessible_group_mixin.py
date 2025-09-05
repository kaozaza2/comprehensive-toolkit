from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class AccessibleGroupMixin(models.AbstractModel):
    _name = 'tk.accessible.group.mixin'
    _description = 'Accessible Group Mixin - Enhanced group management for accessible records'

    # Enhanced group access control
    allowed_group_users_ids = fields.Many2many(
        'res.users',
        'record_allowed_group_users_rel',
        'record_id',
        'user_id',
        string='Allowed Group Users',
        compute='_compute_allowed_group_users_ids',
        store=True,
        help="All users who have access through system groups and custom groups"
    )

    # Custom access groups with enhanced functionality
    custom_access_group_ids = fields.Many2many(
        'tk.accessible.group',
        'record_custom_access_groups_rel',
        'record_id',
        'group_id',
        string='Custom Access Groups',
        help="Custom access groups that have access to this record"
    )

    # Group management permissions
    can_manage_groups = fields.Boolean(
        string='Can Manage Groups',
        compute='_compute_can_manage_groups',
        help="Whether current user can manage access groups for this record"
    )

    # Group statistics
    total_group_users_count = fields.Integer(
        string='Total Group Users',
        compute='_compute_group_statistics',
        help="Total number of users with access through all groups"
    )

    active_custom_groups_count = fields.Integer(
        string='Active Custom Groups',
        compute='_compute_group_statistics',
        help="Number of active custom access groups"
    )

    # Group access validation
    has_group_access = fields.Boolean(
        string='Has Group Access',
        compute='_compute_has_group_access',
        help="Whether current user has access through any group"
    )

    @api.depends('allowed_group_ids', 'custom_access_group_ids')
    def _compute_allowed_group_users_ids(self):
        """Compute all users who have access through system and custom groups"""
        for record in self:
            all_users = self.env['res.users']

            # Add users from system groups
            if hasattr(record, 'allowed_group_ids'):
                for group in record.allowed_group_ids:
                    all_users |= group.users

            # Add users from custom groups
            for custom_group in record.custom_access_group_ids:
                if custom_group.active:
                    all_users |= custom_group.user_ids

            record.allowed_group_users_ids = all_users

    def _compute_can_manage_groups(self):
        """Compute whether current user can manage access groups"""
        for record in self:
            record.can_manage_groups = (
                self.env.user.has_group('base.group_system') or
                (hasattr(record, 'owner_id') and record.owner_id == self.env.user) or
                (hasattr(record, 'co_owner_ids') and self.env.user in record.co_owner_ids) or
                (hasattr(record, 'allowed_user_ids') and self.env.user in record.allowed_user_ids)
            )

    @api.depends('custom_access_group_ids', 'allowed_group_users_ids')
    def _compute_group_statistics(self):
        """Compute group-related statistics"""
        for record in self:
            record.total_group_users_count = len(record.allowed_group_users_ids)
            record.active_custom_groups_count = len(record.custom_access_group_ids.filtered('active'))

    @api.depends('allowed_group_users_ids')
    def _compute_has_group_access(self):
        """Compute whether current user has access through groups"""
        for record in self:
            record.has_group_access = self.env.user in record.allowed_group_users_ids

    def add_custom_access_group(self, group_id, reason=None):
        """Add a custom access group to the record"""
        if not self.can_manage_groups:
            raise AccessError(_("You don't have permission to manage access groups for this record."))

        group = self.env['tk.accessible.group'].browse(group_id)
        if not group.exists():
            raise ValidationError(_("Invalid access group specified."))

        if not group.active:
            raise ValidationError(_("Cannot add inactive access group."))

        if group not in self.custom_access_group_ids:
            self.custom_access_group_ids = [(4, group_id)]

            # Log the addition if record has access logging
            if hasattr(self, '_log_access_change'):
                self._log_access_change('add_custom_group', None, group.user_ids,
                                       f"Added custom group: {group.name}" + (f" - {reason}" if reason else ""))

        return True

    def remove_custom_access_group(self, group_id, reason=None):
        """Remove a custom access group from the record"""
        if not self.can_manage_groups:
            raise AccessError(_("You don't have permission to manage access groups for this record."))

        group = self.env['tk.accessible.group'].browse(group_id)
        if not group.exists():
            raise ValidationError(_("Invalid access group specified."))

        if group in self.custom_access_group_ids:
            old_users = group.user_ids
            self.custom_access_group_ids = [(3, group_id)]

            # Log the removal if record has access logging
            if hasattr(self, '_log_access_change'):
                self._log_access_change('remove_custom_group', old_users, None,
                                       f"Removed custom group: {group.name}" + (f" - {reason}" if reason else ""))

        return True

    def replace_custom_access_groups(self, group_ids, reason=None):
        """Replace all custom access groups with new ones"""
        if not self.can_manage_groups:
            raise AccessError(_("You don't have permission to manage access groups for this record."))

        if not isinstance(group_ids, list):
            group_ids = [group_ids] if group_ids else []

        groups = self.env['tk.accessible.group'].browse(group_ids)
        if not all(group.exists() for group in groups):
            raise ValidationError(_("One or more invalid access groups specified."))

        inactive_groups = groups.filtered(lambda g: not g.active)
        if inactive_groups:
            raise ValidationError(_("Cannot add inactive access groups: %s") %
                                ', '.join(inactive_groups.mapped('name')))

        old_groups = self.custom_access_group_ids
        self.custom_access_group_ids = [(6, 0, group_ids)]

        # Log the replacement if record has access logging
        if hasattr(self, '_log_access_change'):
            old_names = ', '.join(old_groups.mapped('name'))
            new_names = ', '.join(groups.mapped('name'))
            extra_reason = f"Replaced groups: {old_names} → {new_names}"
            if reason:
                extra_reason += f" - {reason}"
            self._log_access_change('replace_custom_groups', old_groups.mapped('user_ids'),
                                   groups.mapped('user_ids'), extra_reason)

        return True

    def clear_all_custom_groups(self, reason=None):
        """Remove all custom access groups"""
        if not self.can_manage_groups:
            raise AccessError(_("You don't have permission to manage access groups for this record."))

        if self.custom_access_group_ids:
            old_groups = self.custom_access_group_ids
            old_users = old_groups.mapped('user_ids')
            self.custom_access_group_ids = [(5, 0, 0)]

            # Log the clearing if record has access logging
            if hasattr(self, '_log_access_change'):
                group_names = ', '.join(old_groups.mapped('name'))
                extra_reason = f"Cleared all custom groups: {group_names}"
                if reason:
                    extra_reason += f" - {reason}"
                self._log_access_change('clear_custom_groups', old_users, None, extra_reason)

        return True

    def get_users_from_group(self, group_id):
        """Get all users from a specific access group"""
        group = self.env['tk.accessible.group'].browse(group_id)
        if not group.exists():
            raise ValidationError(_("Invalid access group specified."))

        return group.user_ids

    def get_all_group_users(self, include_inactive=False):
        """Get all users who have access through any group"""
        all_users = self.env['res.users']

        # Users from system groups
        if hasattr(self, 'allowed_group_ids'):
            for group in self.allowed_group_ids:
                all_users |= group.users

        # Users from custom groups
        custom_groups = self.custom_access_group_ids
        if not include_inactive:
            custom_groups = custom_groups.filtered('active')

        for group in custom_groups:
            all_users |= group.user_ids

        return all_users

    def check_user_group_access(self, user=None):
        """Check if a user has access through any group"""
        if user is None:
            user = self.env.user

        # Check system groups
        if hasattr(self, 'allowed_group_ids'):
            user_groups = user.groups_id
            if bool(user_groups & self.allowed_group_ids):
                return True

        # Check custom groups
        for custom_group in self.custom_access_group_ids:
            if custom_group.active and user in custom_group.user_ids:
                return True

        return False

    def get_group_access_summary(self):
        """Get a summary of group access for this record"""
        summary = {
            'system_groups': [],
            'custom_groups': [],
            'total_users': len(self.allowed_group_users_ids),
            'active_custom_groups': self.active_custom_groups_count
        }

        # System groups info
        if hasattr(self, 'allowed_group_ids'):
            for group in self.allowed_group_ids:
                summary['system_groups'].append({
                    'name': group.name,
                    'user_count': len(group.users)
                })

        # Custom groups info
        for group in self.custom_access_group_ids:
            summary['custom_groups'].append({
                'name': group.name,
                'active': group.active,
                'user_count': len(group.user_ids),
                'group_type': group.group_type
            })

        return summary

    def action_manage_custom_groups(self):
        """Open wizard to manage custom access groups"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Manage Custom Access Groups'),
            'res_model': 'tk.accessible.group.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_active_model': self._name,
                'default_active_id': self.id,
                'default_current_groups': self.custom_access_group_ids.ids,
            }
        }

    def action_view_group_users(self):
        """Open view of all users with group access"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Users with Group Access'),
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.allowed_group_users_ids.ids)],
            'context': {
                'default_record_ref': f"{self._name},{self.id}",
            }
        }
