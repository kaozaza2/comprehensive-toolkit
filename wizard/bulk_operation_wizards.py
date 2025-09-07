from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BulkAssignWizard(models.TransientModel):
    _name = 'tk.bulk.assign.wizard'
    _description = 'Bulk Assignment Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_ids = fields.Text(string='Record IDs', required=True)
    user_ids = fields.Many2many('res.users', string='Assign To', required=True)
    assignment_deadline = fields.Datetime(string='Deadline')
    assignment_description = fields.Text(string='Assignment Description')
    assignment_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    reason = fields.Text(string='Reason')

    def action_assign(self):
        """Bulk assign users to selected records"""
        self.ensure_one()

        # Parse record IDs
        record_ids = eval(self.record_ids) if self.record_ids else []
        if not record_ids:
            raise ValidationError(_("No records selected for assignment."))

        # Get the records
        records = self.env[self.model_name].browse(record_ids)

        # Assign users to each record
        success_count = 0
        error_records = []

        for record in records:
            try:
                if hasattr(record, 'assign_to_users'):
                    record.assign_to_users(
                        user_ids=self.user_ids.ids,
                        deadline=self.assignment_deadline,
                        description=self.assignment_description,
                        priority=self.assignment_priority,
                        reason=self.reason
                    )
                    success_count += 1
                else:
                    error_records.append(record.display_name)
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        message = _("Successfully assigned %s records.") % success_count
        if error_records:
            message += _("\n\nErrors occurred for: %s") % ", ".join(error_records)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Assignment Complete'),
                'message': message,
                'type': 'success' if not error_records else 'warning',
                'sticky': True,
            }
        }


class BulkOwnershipWizard(models.TransientModel):
    _name = 'tk.bulk.ownership.wizard'
    _description = 'Bulk Ownership Transfer Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_ids = fields.Text(string='Record IDs', required=True)
    new_owner_id = fields.Many2one('res.users', string='New Owner', required=True)
    reason = fields.Text(string='Reason')

    def action_transfer(self):
        """Bulk transfer ownership of selected records"""
        self.ensure_one()

        # Parse record IDs
        record_ids = eval(self.record_ids) if self.record_ids else []
        if not record_ids:
            raise ValidationError(_("No records selected for ownership transfer."))

        # Get the records
        records = self.env[self.model_name].browse(record_ids)

        # Transfer ownership for each record
        success_count = 0
        error_records = []

        for record in records:
            try:
                if hasattr(record, 'transfer_ownership'):
                    record.transfer_ownership(
                        new_owner_id=self.new_owner_id.id,
                        reason=self.reason
                    )
                    success_count += 1
                else:
                    error_records.append(record.display_name)
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        message = _("Successfully transferred ownership for %s records.") % success_count
        if error_records:
            message += _("\n\nErrors occurred for: %s") % ", ".join(error_records)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Ownership Transfer Complete'),
                'message': message,
                'type': 'success' if not error_records else 'warning',
                'sticky': True,
            }
        }


class BulkAccessWizard(models.TransientModel):
    _name = 'tk.bulk.access.wizard'
    _description = 'Bulk Access Control Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_ids = fields.Text(string='Record IDs', required=True)
    access_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('private', 'Private')
    ], string='Access Level', required=True)
    allowed_user_ids = fields.Many2many('res.users', string='Allowed Users')
    allowed_group_ids = fields.Many2many('res.groups', string='Allowed Groups')
    custom_access_group_ids = fields.Many2many('tk.accessible.group', string='Allowed Custom Groups')
    access_start_date = fields.Datetime(string='Access Start Date', help="Date from which access is granted")
    access_end_date = fields.Datetime(string='Access End Date', help="Date until which access is granted")
    reason = fields.Text(string='Reason')

    def action_set_access(self):
        """Bulk set access control for selected records"""
        self.ensure_one()

        # Parse record IDs
        record_ids = eval(self.record_ids) if self.record_ids else []
        if not record_ids:
            raise ValidationError(_("No records selected for access control update."))

        # Get the records
        records = self.env[self.model_name].browse(record_ids)

        # Update access control for each record
        success_count = 0
        error_records = []

        for record in records:
            try:
                if hasattr(record, 'set_access_level'):
                    record.set_access_level(self.access_level, reason=self.reason)

                    # Set allowed users and groups if restricted
                    if self.access_level in ['restricted', 'private']:
                        if self.allowed_user_ids:
                            record.bulk_grant_access_to_users(self.allowed_user_ids.ids, reason=self.reason)
                        if self.allowed_group_ids:
                            for group in self.allowed_group_ids:
                                record.grant_access_to_group(group.id, reason=self.reason)
                        if self.custom_access_group_ids:
                            for access_group in self.custom_access_group_ids:
                                record.grant_access_to_custom_group(access_group.id, reason=self.reason)

                # Set access duration if specified
                if hasattr(record, 'set_access_duration'):
                    if self.access_start_date or self.access_end_date:
                        record.set_access_duration(
                            start_date=self.access_start_date,
                            end_date=self.access_end_date,
                            reason=self.reason
                        )

                    success_count += 1
                else:
                    error_records.append(record.display_name)
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        message = _("Successfully updated access control for %s records.") % success_count
        if error_records:
            message += _("\n\nErrors occurred for: %s") % ", ".join(error_records)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Access Control Update Complete'),
                'message': message,
                'type': 'success' if not error_records else 'warning',
                'sticky': True,
            }
        }


class TransferOwnershipWizard(models.TransientModel):
    _name = 'tk.transfer.ownership.wizard'
    _description = 'Transfer Ownership Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_id = fields.Integer(string='Record ID', required=True)
    current_owner_id = fields.Many2one('res.users', string='Current Owner', readonly=True)
    new_owner_id = fields.Many2one('res.users', string='New Owner', required=True)
    reason = fields.Text(string='Reason')

    @api.model
    def default_get(self, fields_list):
        """Set default values including current owner"""
        res = super().default_get(fields_list)

        if 'record_id' in res and 'model_name' in res:
            record = self.env[res['model_name']].browse(res['record_id'])
            if hasattr(record, 'owner_id') and record.owner_id:
                res['current_owner_id'] = record.owner_id.id

        return res

    def action_transfer(self):
        """Transfer ownership of the record"""
        self.ensure_one()

        # Get the record
        record = self.env[self.model_name].browse(self.record_id)

        if not record.exists():
            raise ValidationError(_("Record not found."))

        try:
            if hasattr(record, 'transfer_ownership'):
                record.transfer_ownership(
                    new_owner_id=self.new_owner_id.id,
                    reason=self.reason
                )

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Ownership Transferred'),
                        'message': _('Ownership successfully transferred to %s') % self.new_owner_id.name,
                        'type': 'success',
                    }
                }
            else:
                raise ValidationError(_("This record does not support ownership transfer."))
        except Exception as e:
            raise ValidationError(_("Error transferring ownership: %s") % str(e))


class DelegateResponsibilityWizard(models.TransientModel):
    _name = 'tk.delegate.responsibility.wizard'
    _description = 'Delegate Responsibility Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_id = fields.Integer(string='Record ID', required=True)
    user_ids = fields.Many2many('res.users', string='Delegate To', required=True)
    responsibility_type = fields.Selection([
        ('primary', 'Primary Responsibility'),
        ('secondary', 'Secondary Responsibility'),
        ('shared', 'Shared Responsibility'),
        ('temporary', 'Temporary Responsibility')
    ], string='Responsibility Type', default='primary', required=True)
    end_date = fields.Datetime(string='End Date')
    description = fields.Text(string='Responsibility Description')
    reason = fields.Text(string='Reason for Delegation')

    def action_delegate(self):
        """Delegate responsibility for the record"""
        self.ensure_one()

        # Get the record
        record = self.env[self.model_name].browse(self.record_id)

        if not record.exists():
            raise ValidationError(_("Record not found."))

        try:
            if hasattr(record, 'delegate_responsibility'):
                record.delegate_responsibility(
                    user_ids=self.user_ids.ids,
                    responsibility_type=self.responsibility_type,
                    end_date=self.end_date,
                    description=self.description,
                    reason=self.reason
                )

                user_names = ', '.join(self.user_ids.mapped('name'))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Responsibility Delegated'),
                        'message': _('Responsibility successfully delegated to %s') % user_names,
                        'type': 'success',
                    }
                }
            else:
                raise ValidationError(_("This record does not support responsibility delegation."))
        except Exception as e:
            raise ValidationError(_("Error delegating responsibility: %s") % str(e))


class ManageAccessWizard(models.TransientModel):
    _name = 'tk.manage.access.wizard'
    _description = 'Manage Access Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_id = fields.Integer(string='Record ID', required=True)
    access_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('restricted', 'Restricted'),
        ('private', 'Private')
    ], string='Access Level', required=True)
    allowed_user_ids = fields.Many2many('res.users', string='Allowed Users')
    allowed_group_ids = fields.Many2many('res.groups', string='Allowed Groups')
    custom_access_group_ids = fields.Many2many('tk.accessible.group', string='Custom Access Groups')
    access_start_date = fields.Datetime(string='Access Start Date', help="Date from which access is granted")
    access_end_date = fields.Datetime(string='Access End Date', help="Date until which access is granted")
    reason = fields.Text(string='Reason for Access Change')

    def action_update_access(self):
        """Update access control for the record"""
        self.ensure_one()

        # Get the record
        record = self.env[self.model_name].browse(self.record_id)

        if not record.exists():
            raise ValidationError(_("Record not found."))

        try:
            if hasattr(record, 'set_access_level'):
                record.set_access_level(self.access_level, reason=self.reason)

                # Set allowed users and groups if restricted
                if self.access_level in ['restricted', 'private']:
                    if self.allowed_user_ids:
                        record.bulk_grant_access_to_users(self.allowed_user_ids.ids, reason=self.reason)
                    if self.allowed_group_ids:
                        for group in self.allowed_group_ids:
                            record.grant_access_to_group(group.id, reason=self.reason)
                    if self.custom_access_group_ids:
                        for access_group in self.custom_access_group_ids:
                            record.grant_access_to_custom_group(access_group.id, reason=self.reason)

                # Set access duration if specified
                if hasattr(record, 'set_access_duration'):
                    if self.access_start_date or self.access_end_date:
                        record.set_access_duration(
                            start_date=self.access_start_date,
                            end_date=self.access_end_date,
                            reason=self.reason
                        )

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Access Updated'),
                        'message': _('Access control successfully updated'),
                        'type': 'success',
                    }
                }
            else:
                raise ValidationError(_("This record does not support access control management."))
        except Exception as e:
            raise ValidationError(_("Error updating access control: %s") % str(e))
