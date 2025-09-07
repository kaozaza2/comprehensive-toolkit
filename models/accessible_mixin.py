from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class AccessibleMixin(models.AbstractModel):
    _name = 'tk.accessible.mixin'
    _description = 'Accessible Mixin - Provides access control functionality'

    access_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('private', 'Private')
    ], string='Access Level', default='internal', tracking=True,
       help="Access level for this record")

    allowed_user_ids = fields.Many2many(
        'res.users',
        string='Allowed Users',
        help="Users who have explicit access to this record"
    )
    allowed_group_ids = fields.Many2many(
        'res.groups',
        string='Allowed Groups',
        help="Groups that have access to this record"
    )
    allowed_group_users_ids = fields.Many2many(
        'res.users',
        'record_group_users_rel',
        'record_id',
        'user_id',
        string='Users from Allowed Groups',
        compute='_compute_allowed_group_users_ids',
        store=True,
        help="All users who have access through allowed groups"
    )
    # Custom access groups
    custom_access_group_ids = fields.Many2many(
        'tk.accessible.group',
        'record_custom_groups_rel',
        'record_id',
        'group_id',
        string='Custom Access Groups',
        help="Custom access groups that have access to this record"
    )
    custom_group_users_ids = fields.Many2many(
        'res.users',
        'record_custom_group_users_rel',
        'record_id',
        'user_id',
        string='Users from Custom Groups',
        compute='_compute_custom_group_users_ids',
        store=True,
        help="All users who have access through custom groups"
    )
    all_allowed_users_ids = fields.Many2many(
        'res.users',
        'record_all_allowed_users_rel',
        'record_id',
        'user_id',
        string='All Allowed Users',
        compute='_compute_all_allowed_users_ids',
        store=True,
        help="All users who have access (direct + groups + custom groups)"
    )
    access_start_date = fields.Datetime(
        string='Access Start Date',
        help="Date from which access is granted"
    )
    access_end_date = fields.Datetime(
        string='Access End Date',
        help="Date until which access is granted"
    )
    is_access_expired = fields.Boolean(
        string='Access Expired',
        compute='_compute_is_access_expired',
        help="Whether access has expired"
    )
    can_grant_access = fields.Boolean(
        string='Can Grant Access',
        compute='_compute_can_grant_access',
        help="Whether current user can grant access to this record"
    )
    has_access = fields.Boolean(
        string='Has Access',
        compute='_compute_has_access',
        help="Whether current user has access to this record"
    )

    @api.depends('access_end_date')
    def _compute_is_access_expired(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_access_expired = (
                record.access_end_date and record.access_end_date < now
            )

    @api.depends('allowed_group_ids')
    def _compute_allowed_group_users_ids(self):
        for record in self:
            # Get all users from the allowed groups
            group_users = self.env['res.users']
            for group in record.allowed_group_ids:
                group_users |= group.users
            record.allowed_group_users_ids = group_users

    @api.depends('custom_access_group_ids')
    def _compute_custom_group_users_ids(self):
        for record in self:
            # Get all users from the custom access groups
            custom_users = self.env['res.users']
            for group in record.custom_access_group_ids:
                if group.active:  # Only include active groups
                    custom_users |= group.user_ids
            record.custom_group_users_ids = custom_users

    @api.depends('allowed_user_ids', 'allowed_group_users_ids', 'custom_group_users_ids')
    def _compute_all_allowed_users_ids(self):
        for record in self:
            # Combine all users with access
            all_users = record.allowed_user_ids | record.allowed_group_users_ids | record.custom_group_users_ids
            record.all_allowed_users_ids = all_users

    def _compute_can_grant_access(self):
        for record in self:
            # Check if user has access management rights
            record.can_grant_access = (
                self.env.user.has_group('base.group_system') or
                (hasattr(record, 'owner_id') and record.owner_id == self.env.user) or
                self.env.user in record.allowed_user_ids
            )

    @api.depends('access_level', 'allowed_user_ids', 'allowed_group_ids', 'custom_access_group_ids',
                 'access_start_date', 'access_end_date', 'is_access_expired')
    def _compute_has_access(self):
        for record in self:
            record.has_access = record._check_user_access(self.env.user)

    def _check_user_access(self, user):
        """Check if a user has access to this record"""
        # Check if access is expired
        if self.is_access_expired:
            return False

        # Check access start date
        now = fields.Datetime.now()
        if self.access_start_date and self.access_start_date > now:
            return False

        # System admin always has access
        if user.has_group('base.group_system'):
            return True

        # Owner has access (if record has ownership)
        if hasattr(self, 'owner_id') and self.owner_id == user:
            return True

        # Co-owner has access (if record has co-ownership)
        if hasattr(self, 'co_owner_ids') and user in self.co_owner_ids:
            return True

        # Check access level
        if self.access_level == 'public':
            return True
        elif self.access_level == 'internal':
            return user.has_group('base.group_user')
        elif self.access_level == 'restricted':
            # Check explicit user access
            if user in self.allowed_user_ids:
                return True
            # Check system group access
            user_groups = user.groups_id
            if bool(user_groups & self.allowed_group_ids):
                return True
            # Check custom group access
            for custom_group in self.custom_access_group_ids:
                if custom_group.active and user in custom_group.user_ids:
                    return True
            return False
        elif self.access_level == 'private':
            # Check explicit user access
            if user in self.allowed_user_ids:
                return True
            # Check custom group access for private records
            for custom_group in self.custom_access_group_ids:
                if custom_group.active and user in custom_group.user_ids:
                    return True
            return False

        return False

    def grant_access_to_user(self, user_id, start_date=None, end_date=None, reason=None):
        """Grant access to a specific user"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to grant access to this record."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user not in self.allowed_user_ids:
            self.allowed_user_ids = [(4, user_id)]

        # Update access dates if provided
        if start_date:
            self.access_start_date = start_date
        if end_date:
            self.access_end_date = end_date

        # Log the access grant
        self._log_access_change('grant_user', user, reason)

        return True

    def revoke_access_from_user(self, user_id, reason=None):
        """Revoke access from a specific user"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to revoke access to this record."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user in self.allowed_user_ids:
            self.allowed_user_ids = [(3, user_id)]

        # Log the access revocation
        self._log_access_change('revoke_user', user, reason)

        return True

    def grant_access_to_group(self, group_id, start_date=None, end_date=None, reason=None):
        """Grant access to a specific group"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to grant access to this record."))

        group = self.env['res.groups'].browse(group_id)
        if not group.exists():
            raise ValidationError(_("Invalid group specified."))

        if group not in self.allowed_group_ids:
            self.allowed_group_ids = [(4, group_id)]

        # Update access dates if provided
        if start_date:
            self.access_start_date = start_date
        if end_date:
            self.access_end_date = end_date

        # Log the access grant
        self._log_access_change('grant_group', group, reason)

        return True

    def revoke_access_from_group(self, group_id, reason=None):
        """Revoke access from a specific group"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to revoke access to this record."))

        group = self.env['res.groups'].browse(group_id)
        if not group.exists():
            raise ValidationError(_("Invalid group specified."))

        if group in self.allowed_group_ids:
            self.allowed_group_ids = [(3, group_id)]

        # Log the access revocation
        self._log_access_change('revoke_group', group, reason)

        return True

    def grant_access_to_custom_group(self, custom_group_id, start_date=None, end_date=None, reason=None):
        """Grant access to a custom access group"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to grant access to this record."))

        custom_group = self.env['tk.accessible.group'].browse(custom_group_id)
        if not custom_group.exists():
            raise ValidationError(_("Invalid custom group specified."))

        if not custom_group.active:
            raise ValidationError(_("Cannot grant access to inactive group."))

        if custom_group not in self.custom_access_group_ids:
            self.custom_access_group_ids = [(4, custom_group_id)]

        # Update access dates if provided
        if start_date:
            self.access_start_date = start_date
        if end_date:
            self.access_end_date = end_date

        # Log the access grant
        self._log_access_change('grant_custom_group', custom_group, reason)

        return True

    def revoke_access_from_custom_group(self, custom_group_id, reason=None):
        """Revoke access from a custom access group"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to revoke access to this record."))

        custom_group = self.env['tk.accessible.group'].browse(custom_group_id)
        if not custom_group.exists():
            raise ValidationError(_("Invalid custom group specified."))

        if custom_group in self.custom_access_group_ids:
            self.custom_access_group_ids = [(3, custom_group_id)]

        # Log the access revocation
        self._log_access_change('revoke_custom_group', custom_group, reason)

        return True

    def create_and_assign_custom_group(self, group_name, user_ids, group_type='custom', reason=None):
        """Create a new custom group and assign it to this record"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to create access groups for this record."))

        # Create the custom group
        custom_group = self.env['tk.accessible.group'].create({
            'name': group_name,
            'description': f"Access group created for {self._description} record",
            'group_type': group_type,
            'user_ids': [(6, 0, user_ids)] if user_ids else [],
        })

        # Assign the group to this record
        self.custom_access_group_ids = [(4, custom_group.id)]

        # Log the creation and assignment
        self._log_access_change('create_assign_custom_group', custom_group, reason,
                              extra_info=f"Created group: {group_name}")

        return custom_group

    def set_access_level(self, level, reason=None):
        """Set the access level for this record"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to change access level of this record."))

        if level not in dict(self._fields['access_level'].selection):
            raise ValidationError(_("Invalid access level specified."))

        old_level = self.access_level
        self.access_level = level

        # Log the access level change
        self._log_access_change('change_level', None, reason,
                              extra_info=f"From {old_level} to {level}")

        return True

    def set_access_duration(self, start_date=None, end_date=None, reason=None):
        """Set the access duration for this record"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to change access duration of this record."))

        if start_date:
            self.access_start_date = start_date
        if end_date:
            self.access_end_date = end_date

        # Log the access duration change
        self._log_access_change('change_duration', None, reason,
                              extra_info=f"Start: {start_date}, End: {end_date}")

        return True

    def get_all_accessible_users(self):
        """Get all users who have access to this record"""
        return self.all_allowed_users_ids

    def check_user_has_access(self, user_id):
        """Check if a specific user has access to this record"""
        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            return False

        return self._check_user_access(user)

    def bulk_grant_access_to_users(self, user_ids, start_date=None, end_date=None, reason=None):
        """Grant access to multiple users at once"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to grant access to this record."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified."))

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified."))

        # Add users that aren't already in allowed_user_ids
        new_users = users.filtered(lambda u: u not in self.allowed_user_ids)
        if new_users:
            self.allowed_user_ids = [(4, user_id) for user_id in new_users.ids]
            user_names = ', '.join(new_users.mapped('name'))
            self._log_access_change('bulk_grant_users', None, reason,
                                  extra_info=f"Granted access to: {user_names}")

        if start_date:
            self.access_start_date = start_date

        if end_date:
            self.access_end_date = end_date

        return True

    def bulk_revoke_access_from_users(self, user_ids, reason=None):
        """Revoke access from multiple users at once"""
        if not self.can_grant_access:
            raise AccessError(_("You don't have permission to revoke access to this record."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified."))

        users = self.env['res.users'].browse(user_ids)
        existing_users = users.filtered(lambda u: u in self.allowed_user_ids)

        if existing_users:
            self.allowed_user_ids = [(3, user_id) for user_id in existing_users.ids]
            user_names = ', '.join(existing_users.mapped('name'))
            self._log_access_change('bulk_revoke_users', None, reason,
                                  extra_info=f"Revoked access from: {user_names}")

        return True

    def _log_access_change(self, action, target, reason, extra_info=None):
        """Log access changes"""
        target_user_id = False
        target_group_id = False
        target_custom_group_id = False

        if target:
            if hasattr(target, '_name'):
                if target._name == 'res.users':
                    target_user_id = target.id
                elif target._name == 'res.groups':
                    target_group_id = target.id
                elif target._name == 'tk.accessible.group':
                    target_custom_group_id = target.id

        self.env['tk.access.log'].create({
            'model_name': self._name,
            'res_id': self.id,
            'action': action,
            'target_user_id': target_user_id,
            'target_group_id': target_group_id,
            'target_custom_group_id': target_custom_group_id,
            'reason': reason or '',
            'extra_info': extra_info or '',
            'user_id': self.env.user.id,
            'date': fields.Datetime.now()
        })
