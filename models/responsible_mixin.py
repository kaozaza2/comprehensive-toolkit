from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class ResponsibleMixin(models.AbstractModel):
    _name = 'tk.responsible.mixin'
    _description = 'Responsible Mixin - Provides responsibility management functionality'

    responsible_user_ids = fields.Many2many(
        'res.users',
        'record_responsible_users_rel',
        'record_id',
        'user_id',
        string='Responsible Users',
        tracking=True,
        help="Users responsible for this record"
    )
    secondary_responsible_ids = fields.Many2many(
        'res.users',
        'record_secondary_responsible_rel',
        'record_id',
        'user_id',
        string='Secondary Responsible',
        tracking=True,
        help="Users with secondary responsibility for this record"
    )
    responsibility_start_date = fields.Datetime(
        string='Responsibility Start Date',
        default=fields.Datetime.now,
        help="Date when responsibility was assigned"
    )
    responsibility_end_date = fields.Datetime(
        string='Responsibility End Date',
        help="Date when responsibility ends (for temporary responsibilities)"
    )
    responsibility_delegated_by = fields.Many2one(
        'res.users',
        string='Delegated By',
        readonly=True,
        help="User who delegated this responsibility"
    )
    responsibility_description = fields.Text(
        string='Responsibility Description',
        help="Description of what this responsibility entails"
    )
    is_responsibility_active = fields.Boolean(
        string='Responsibility Active',
        compute='_compute_is_responsibility_active',
        store=True,
        help="Whether the responsibility is currently active"
    )
    is_responsibility_expired = fields.Boolean(
        string='Responsibility Expired',
        compute='_compute_is_responsibility_expired',
        help="Whether the responsibility has expired"
    )
    can_delegate = fields.Boolean(
        string='Can Delegate',
        compute='_compute_can_delegate',
        search='_search_can_delegate',
        help="Whether current user can delegate responsibility"
    )
    responsibility_count = fields.Integer(
        string='Number of Responsible Users',
        compute='_compute_responsibility_count',
        help="Total number of responsible users"
    )
    secondary_responsibility_count = fields.Integer(
        string='Number of Secondary Responsible',
        compute='_compute_secondary_responsibility_count',
        help="Total number of secondary responsible users"
    )

    @api.depends('responsible_user_ids', 'responsibility_end_date')
    def _compute_is_responsibility_active(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_responsibility_active = (
                bool(record.responsible_user_ids) and
                (not record.responsibility_end_date or record.responsibility_end_date > now)
            )

    @api.depends('responsibility_end_date')
    def _compute_is_responsibility_expired(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_responsibility_expired = (
                record.responsibility_end_date and
                record.responsibility_end_date < now
            )

    @api.depends('responsible_user_ids')
    def _compute_responsibility_count(self):
        for record in self:
            record.responsibility_count = len(record.responsible_user_ids)

    @api.depends('secondary_responsible_ids')
    def _compute_secondary_responsibility_count(self):
        for record in self:
            record.secondary_responsibility_count = len(record.secondary_responsible_ids)

    def _compute_can_delegate(self):
        for record in self:
            # Basic permission check
            has_basic_permission = (
                self.env.user.has_group('base.group_user') or
                self.env.user.has_group('base.group_system')
            )

            # Check if user is currently responsible (primary OR secondary)
            is_responsible = (
                self.env.user in record.responsible_user_ids or
                self.env.user in record.secondary_responsible_ids
            )

            # Check ownership if record has ownable mixin (including co-owners)
            has_ownership = False
            if hasattr(record, 'owner_id'):
                has_ownership = (
                    record.owner_id == self.env.user or
                    (hasattr(record, 'co_owner_ids') and self.env.user in record.co_owner_ids) or
                    not record.owner_id  # Unowned records can be delegated
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

            # User can delegate if they have basic permission AND (is responsible OR ownership OR access)
            record.can_delegate = (
                has_basic_permission and
                (is_responsible or has_ownership or has_access or self.env.user.has_group('base.group_system'))
            )

    def assign_responsibility(self, user_ids, end_date=None, description=None, reason=None):
        """Assign responsibility to users"""
        if not self.can_delegate and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("You don't have permission to assign responsibility for this record."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified for responsibility assignment."))

        # Ensure user_ids is a list
        if not isinstance(user_ids, list):
            user_ids = [user_ids] if user_ids else []

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified for responsibility assignment."))

        old_responsible = self.responsible_user_ids

        # Assign responsibility
        vals = {
            'responsible_user_ids': [(6, 0, user_ids)],
            'responsibility_start_date': fields.Datetime.now(),
            'responsibility_delegated_by': self.env.user.id
        }
        if end_date:
            vals['responsibility_end_date'] = end_date
        if description:
            vals['responsibility_description'] = description

        self.write(vals)

        # Log the assignment
        self._log_responsibility_change('assign_multiple', old_responsible, users, reason)

        return True

    def assign_secondary_responsibility(self, user_ids, reason=None):
        """Assign secondary responsibility to users"""
        if not self.can_delegate and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("You don't have permission to assign secondary responsibility for this record."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified for secondary responsibility assignment."))

        # Ensure user_ids is a list
        if not isinstance(user_ids, list):
            user_ids = [user_ids] if user_ids else []

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified for secondary responsibility assignment."))

        old_secondary = self.secondary_responsible_ids

        # Assign secondary responsibility
        vals = {
            'secondary_responsible_ids': [(6, 0, user_ids)],
        }

        self.write(vals)

        # Log the assignment
        self._log_responsibility_change('assign_secondary_multiple', old_secondary, users, reason)

        return True

    def delegate_responsibility(self, user_ids, reason=None):
        """Delegate responsibility to other users"""
        return self._change_responsibility(user_ids, 'delegate_multiple', reason)

    def transfer_responsibility(self, user_ids, reason=None):
        """Transfer responsibility to other users (alias for delegate_responsibility)"""
        return self._change_responsibility(user_ids, 'transfer_multiple', reason)

    def delegate_secondary_responsibility(self, user_ids, reason=None):
        """Delegate secondary responsibility to other users"""
        return self._change_secondary_responsibility(user_ids, 'delegate_secondary_multiple', reason)

    def transfer_secondary_responsibility(self, user_ids, reason=None):
        """Transfer secondary responsibility to other users (alias for delegate_secondary_responsibility)"""
        return self._change_secondary_responsibility(user_ids, 'transfer_secondary_multiple', reason)

    def _change_responsibility(self, user_ids, action_type, reason=None):
        """Internal method to handle responsibility changes"""
        if not self.can_delegate:
            raise AccessError(_("You don't have permission to change responsibility."))

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified for responsibility change."))

        old_responsible = self.responsible_user_ids

        # Change responsibility
        vals = {
            'responsible_user_ids': [(6, 0, user_ids)],
            'responsibility_delegated_by': self.env.user.id,
            'responsibility_start_date': fields.Datetime.now()
        }

        self.write(vals)

        # Log the change
        self._log_responsibility_change(action_type, old_responsible, users, reason)

        return True

    def _change_secondary_responsibility(self, user_ids, action_type, reason=None):
        """Internal method to handle secondary responsibility changes"""
        if not self.can_delegate:
            raise AccessError(_("You don't have permission to change secondary responsibility."))

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified for secondary responsibility change."))

        old_secondary = self.secondary_responsible_ids

        # Change secondary responsibility
        vals = {
            'secondary_responsible_ids': [(6, 0, user_ids)],
        }

        self.write(vals)

        # Log the change
        self._log_responsibility_change(action_type, old_secondary, users, reason)

        return True

    def add_responsible_user(self, user_id, is_secondary=False, reason=None):
        """Add a responsible user"""
        if not self.can_delegate:
            raise AccessError(_("You don't have permission to add responsible users."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if is_secondary:
            if user not in self.secondary_responsible_ids:
                self.secondary_responsible_ids = [(4, user_id)]
                self._log_responsibility_change('add_secondary', None, user, reason)
        else:
            if user not in self.responsible_user_ids:
                self.responsible_user_ids = [(4, user_id)]
                self._log_responsibility_change('add_responsible', None, user, reason)

        return True

    def remove_responsible_user(self, user_id, is_secondary=False, reason=None):
        """Remove a responsible user"""
        if not self.can_delegate:
            raise AccessError(_("You don't have permission to remove responsible users."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if is_secondary:
            if user in self.secondary_responsible_ids:
                self.secondary_responsible_ids = [(3, user_id)]
                self._log_responsibility_change('remove_secondary', user, None, reason)
        else:
            if user in self.responsible_user_ids:
                self.responsible_user_ids = [(3, user_id)]
                self._log_responsibility_change('remove_responsible', user, None, reason)

        return True

    def revoke_all_responsibility(self, reason=None):
        """Revoke all responsibility"""
        if not self.can_delegate:
            raise AccessError(_("You don't have permission to revoke responsibility."))

        old_responsible = self.responsible_user_ids
        old_secondary = self.secondary_responsible_ids

        # Revoke all responsibility
        self.write({
            'responsible_user_ids': [(5, 0, 0)],
            'secondary_responsible_ids': [(5, 0, 0)]
        })

        # Log the revocation
        if old_responsible or old_secondary:
            self._log_responsibility_change('revoke_all', old_responsible | old_secondary, None, reason)

        return True

    def escalate_responsibility(self, escalation_user_id, reason=None):
        """Escalate responsibility to a higher authority"""
        if not self.can_delegate:
            raise AccessError(_("You don't have permission to escalate responsibility."))

        escalation_user = self.env['res.users'].browse(escalation_user_id)
        if not escalation_user.exists():
            raise ValidationError(_("Invalid escalation user specified."))

        old_responsible = self.responsible_user_ids
        old_secondary = self.secondary_responsible_ids

        # Escalate responsibility - clear both primary and secondary responsibility
        vals = {
            'responsible_user_ids': [(6, 0, [escalation_user_id])],
            'secondary_responsible_ids': [(5, 0, 0)],  # Clear secondary responsibility
            'responsibility_delegated_by': self.env.user.id,
            'responsibility_start_date': fields.Datetime.now(),
        }

        self.write(vals)

        # Log the escalation (include both primary and secondary in the log)
        all_old_users = old_responsible | old_secondary
        self._log_responsibility_change('escalate', all_old_users, escalation_user, reason)

        return True

    def _log_responsibility_change(self, action, old_users, new_users, reason):
        """Log responsibility changes"""
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

        self.env['tk.responsibility.log'].create({
            'model_name': self._name,
            'res_id': self.id,
            'action': action,
            'old_responsible_user_id': old_users[0].id if old_users and len(old_users) > 0 else False,
            'new_responsible_user_id': new_users[0].id if new_users and len(new_users) > 0 else False,
            'reason': reason or '',
            'extra_info': extra_info,
            'user_id': self.env.user.id,
            'date': fields.Datetime.now()
        })

    def _search_can_delegate(self, operator, value):
        """Search method for can_delegate field"""
        # This is a complex computed field, return basic domain
        if operator == '=' and value:
            # Records where user has some level of access
            if self.env.user.has_group('base.group_system'):
                domain = [('id', '!=', False)]  # System admin can delegate any record
            else:
                fields = ['responsible_user_ids', 'secondary_responsible_ids']
                if hasattr(self, 'owner_id'):
                    fields += ['owner_id', 'co_owner_ids']

                domain = ['|'] * (len(fields) - 1)  # Create OR conditions
                user_id = self.env.user.id
                for field in fields:
                    domain.append((field, '=', user_id))

            return domain
        elif operator == '=' and not value:
            # Records where user cannot delegate (complex logic, return restrictive domain)
            return [('id', '=', False)]  # No records by default
        return []
