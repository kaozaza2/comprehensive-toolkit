from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class OwnableMixin(models.AbstractModel):
    _name = 'tk.ownable.mixin'
    _description = 'Ownable Mixin - Provides ownership functionality'

    owner_id = fields.Many2one(
        'res.users',
        string='Owner',
        default=lambda self: self.env.user,
        tracking=True,
        help="Current owner of this record"
    )
    co_owner_ids = fields.Many2many(
        'res.users',
        'record_co_owners_rel',
        'record_id',
        'user_id',
        string='Co-owners',
        tracking=True,
        help="Users who share ownership of this record"
    )
    previous_owner_id = fields.Many2one(
        'res.users',
        string='Previous Owner',
        readonly=True,
        help="Previous owner before the last transfer"
    )
    ownership_date = fields.Datetime(
        string='Ownership Date',
        default=fields.Datetime.now,
        readonly=True,
        help="Date when current ownership was established"
    )
    is_owned = fields.Boolean(
        string='Is Owned',
        compute='_compute_is_owned',
        search='_search_is_owned',
        store=True,
        help="Whether this record has an owner"
    )
    can_transfer = fields.Boolean(
        string='Can Transfer',
        compute='_compute_can_transfer',
        search='_search_can_transfer',
        help="Whether current user can transfer ownership"
    )
    can_release = fields.Boolean(
        string='Can Release',
        compute='_compute_can_release',
        search='_search_can_release',
        help="Whether current user can release ownership"
    )
    can_manage_co_owners = fields.Boolean(
        string='Can Manage Co-owners',
        compute='_compute_can_manage_co_owners',
        search='_search_can_manage_co_owners',
        help="Whether current user can add/remove co-owners"
    )
    co_owner_count = fields.Integer(
        string='Number of Co-owners',
        compute='_compute_co_owner_count',
        help="Total number of co-owners for this record"
    )
    is_owned_by_me = fields.Boolean(
        string='Owned by Me',
        compute='_compute_is_owned_by_me',
        search='_search_is_owned_by_me',
        help="Whether current user owns or co-owns this record"
    )

    @api.depends('owner_id', 'co_owner_ids')
    def _compute_is_owned(self):
        for record in self:
            # Record is owned if it has an owner OR co-owners
            record.is_owned = bool(record.owner_id) or bool(record.co_owner_ids)

    @api.depends('owner_id', 'co_owner_ids')
    def _compute_can_manage_co_owners(self):
        for record in self:
            record.can_manage_co_owners = (
                record.owner_id == self.env.user or
                self.env.user in record.co_owner_ids or  # Co-owners can also manage co-owners
                self.env.user.has_group('base.group_system')
            )

    @api.depends('owner_id')
    def _compute_can_transfer(self):
        for record in self:
            record.can_transfer = (
                record.owner_id == self.env.user or
                self.env.user.has_group('base.group_system')
            )

    @api.depends('owner_id')
    def _compute_can_release(self):
        for record in self:
            record.can_release = (
                record.owner_id == self.env.user or
                self.env.user.has_group('base.group_system')
            )

    @api.depends('co_owner_ids')
    def _compute_co_owner_count(self):
        for record in self:
            record.co_owner_count = len(record.co_owner_ids)

    @api.depends('owner_id', 'co_owner_ids')
    def _compute_is_owned_by_me(self):
        for record in self:
            record.is_owned_by_me = (
                record.owner_id == self.env.user or
                self.env.user in record.co_owner_ids
            )

    def transfer_ownership(self, new_owner_id, reason=None):
        """Transfer ownership to a new user"""
        if not self.can_transfer:
            raise AccessError(_("You don't have permission to transfer ownership of this record."))

        new_owner = self.env['res.users'].browse(new_owner_id)
        if not new_owner.exists():
            raise ValidationError(_("Invalid new owner specified."))

        old_owner = self.owner_id

        # Update ownership
        self.write({
            'previous_owner_id': old_owner.id if old_owner else False,
            'owner_id': new_owner_id,
            'ownership_date': fields.Datetime.now()
        })

        # Log the transfer
        self._log_ownership_change('transfer', old_owner, new_owner, reason)

        return True

    def release_ownership(self, reason=None):
        """Release current ownership"""
        if not self.can_release:
            raise AccessError(_("You don't have permission to release ownership of this record."))

        old_owner = self.owner_id

        # Release ownership
        self.write({
            'previous_owner_id': old_owner.id if old_owner else False,
            'owner_id': False,
            'ownership_date': fields.Datetime.now()
        })

        # Log the release
        self._log_ownership_change('release', old_owner, None, reason)

        return True

    def claim_ownership(self, reason=None):
        """Claim ownership of an unowned record"""
        if self.owner_id:
            raise ValidationError(_("This record already has an owner."))

        # Claim ownership
        self.write({
            'owner_id': self.env.user.id,
            'ownership_date': fields.Datetime.now()
        })

        # Log the claim
        self._log_ownership_change('claim', None, self.env.user, reason)

        return True

    def add_co_owner(self, user_id, reason=None):
        """Add a co-owner to the record"""
        if not self.can_manage_co_owners:
            raise AccessError(_("You don't have permission to add co-owners to this record."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified for co-ownership."))

        if user == self.owner_id:
            raise ValidationError(_("The owner cannot be added as a co-owner."))

        if user in self.co_owner_ids:
            raise ValidationError(_("User is already a co-owner of this record."))

        # Add co-owner
        self.co_owner_ids = [(4, user_id)]

        # Log the addition
        self._log_ownership_change('add_co_owner', None, user, reason)

        return True

    def remove_co_owner(self, user_id, reason=None):
        """Remove a co-owner from the record"""
        if not self.can_manage_co_owners:
            raise AccessError(_("You don't have permission to remove co-owners from this record."))

        user = self.env['res.users'].browse(user_id)
        if not user.exists():
            raise ValidationError(_("Invalid user specified."))

        if user not in self.co_owner_ids:
            raise ValidationError(_("User is not a co-owner of this record."))

        # Remove co-owner
        self.co_owner_ids = [(3, user_id)]

        # Log the removal
        self._log_ownership_change('remove_co_owner', user, None, reason)

        return True

    def add_multiple_co_owners(self, user_ids, reason=None):
        """Add multiple co-owners to the record"""
        if not self.can_manage_co_owners:
            raise AccessError(_("You don't have permission to add co-owners to this record."))

        if not user_ids:
            raise ValidationError(_("At least one user must be specified."))

        # Ensure user_ids is a list
        if not isinstance(user_ids, list):
            user_ids = [user_ids] if user_ids else []

        users = self.env['res.users'].browse(user_ids)
        if not all(user.exists() for user in users):
            raise ValidationError(_("One or more invalid users specified."))

        # Check for owner and existing co-owners
        for user in users:
            if user == self.owner_id:
                raise ValidationError(_("The owner cannot be added as a co-owner."))
            if user in self.co_owner_ids:
                raise ValidationError(_("User %s is already a co-owner.") % user.name)

        # Add all co-owners
        self.co_owner_ids = [(4, user_id) for user_id in user_ids]

        # Log the addition with usernames
        user_names = ', '.join(users.mapped('name'))
        extra_reason = f"Added co-owners: {user_names}"
        if reason:
            extra_reason += f" - {reason}"

        self._log_ownership_change('add_multiple_co_owners', None, None, extra_reason)

        return True

    def remove_all_co_owners(self, reason=None):
        """Remove all co-owners from the record"""
        if not self.can_manage_co_owners:
            raise AccessError(_("You don't have permission to remove co-owners from this record."))

        if not self.co_owner_ids:
            raise ValidationError(_("This record has no co-owners to remove."))

        old_co_owners = self.co_owner_ids
        user_names = ', '.join(old_co_owners.mapped('name'))

        # Remove all co-owners
        self.co_owner_ids = [(5, 0, 0)]

        # Log the removal
        extra_reason = f"Removed all co-owners: {user_names}"
        if reason:
            extra_reason += f" - {reason}"

        self._log_ownership_change('remove_all_co_owners', None, None, extra_reason)

        return True

    def is_owner_or_co_owner(self, user=None):
        """Check if a user is the owner or a co-owner"""
        if user is None:
            user = self.env.user

        return user == self.owner_id or user in self.co_owner_ids

    def get_all_owners(self):
        """Get all owners (owner + co-owners) as a recordset"""
        owners = self.env['res.users']
        if self.owner_id:
            owners |= self.owner_id
        owners |= self.co_owner_ids
        return owners

    def _log_ownership_change(self, action, old_owner, new_owner, reason):
        """Log ownership changes"""
        self.env['tk.ownership.log'].create({
            'model_name': self._name,
            'res_id': self.id,
            'action': action,
            'old_owner_id': old_owner.id if old_owner else False,
            'new_owner_id': new_owner.id if new_owner else False,
            'reason': reason or '',
            'user_id': self.env.user.id,
            'date': fields.Datetime.now()
        })

    def _search_is_owned(self, operator, value):
        """Search method for is_owned field"""
        if operator == '=' and value:
            # Records that have an owner OR co-owners
            return ['|', ('owner_id', '!=', False), ('co_owner_ids', '!=', False)]
        elif operator == '=' and not value:
            # Records that have NO owner AND NO co-owners
            return [('owner_id', '=', False), ('co_owner_ids', '=', False)]
        elif operator == '!=' and value:
            # Records that have NO owner AND NO co-owners
            return [('owner_id', '=', False), ('co_owner_ids', '=', False)]
        elif operator == '!=' and not value:
            # Records that have an owner OR co-owners
            return ['|', ('owner_id', '!=', False), ('co_owner_ids', '!=', False)]
        return []

    def _search_can_transfer(self, operator, value):
        """Search method for can_transfer field"""
        if operator == '=' and value:
            # Current user is owner or system admin
            domain = [('owner_id', '=', self.env.user.id)]
            if self.env.user.has_group('base.group_system'):
                domain = ['|', ('owner_id', '=', self.env.user.id), ('owner_id', '!=', False)]
            return domain
        elif operator == '=' and not value:
            # Current user is NOT owner and not system admin
            domain = [('owner_id', '!=', self.env.user.id)]
            if not self.env.user.has_group('base.group_system'):
                domain.append(('owner_id', '!=', False))
            return domain
        return []

    def _search_can_release(self, operator, value):
        """Search method for can_release field"""
        if operator == '=' and value:
            # Current user is owner or system admin
            domain = [('owner_id', '=', self.env.user.id)]
            if self.env.user.has_group('base.group_system'):
                domain = ['|', ('owner_id', '=', self.env.user.id), ('owner_id', '!=', False)]
            return domain
        elif operator == '=' and not value:
            # Current user is NOT owner and not system admin
            domain = [('owner_id', '!=', self.env.user.id)]
            if not self.env.user.has_group('base.group_system'):
                domain.append(('owner_id', '!=', False))
            return domain
        return []

    def _search_can_manage_co_owners(self, operator, value):
        """Search method for can_manage_co_owners field"""
        if operator == '=' and value:
            # Current user is owner or system admin
            domain = [('owner_id', '=', self.env.user.id)]
            if self.env.user.has_group('base.group_system'):
                domain = ['|', ('owner_id', '=', self.env.user.id), ('owner_id', '!=', False)]
            return domain
        elif operator == '=' and not value:
            # Current user is NOT owner and not system admin
            domain = [('owner_id', '!=', self.env.user.id)]
            if not self.env.user.has_group('base.group_system'):
                domain.append(('owner_id', '!=', False))
            return domain
        return []

    def _search_is_owned_by_me(self, operator, value):
        """Search method for is_owned_by_me field"""
        if operator == '=' and value:
            # Current user is owner OR co-owner
            return ['|', ('owner_id', '=', self.env.user.id), ('co_owner_ids', 'in', [self.env.user.id])]
        elif operator == '=' and not value:
            # Current user is NOT owner AND NOT co-owner
            return [('owner_id', '!=', self.env.user.id), ('co_owner_ids', 'not in', [self.env.user.id])]
        elif operator == '!=' and value:
            # Current user is NOT owner AND NOT co-owner
            return [('owner_id', '!=', self.env.user.id), ('co_owner_ids', 'not in', [self.env.user.id])]
        elif operator == '!=' and not value:
            # Current user is owner OR co-owner
            return ['|', ('owner_id', '=', self.env.user.id), ('co_owner_ids', 'in', [self.env.user.id])]
        return []
