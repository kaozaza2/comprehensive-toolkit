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
        message = _("Successfully transferred ownership of %s records.") % success_count
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
    reason = fields.Text(string='Reason')

    def action_set_access(self):
        """Bulk set access level for selected records"""
        self.ensure_one()

        # Parse record IDs
        record_ids = eval(self.record_ids) if self.record_ids else []
        if not record_ids:
            raise ValidationError(_("No records selected for access control update."))

        # Get the records
        records = self.env[self.model_name].browse(record_ids)

        # Update access for each record
        success_count = 0
        error_records = []

        for record in records:
            try:
                if hasattr(record, 'access_level'):
                    vals = {
                        'access_level': self.access_level,
                        'allowed_user_ids': [(6, 0, self.allowed_user_ids.ids)],
                        'allowed_group_ids': [(6, 0, self.allowed_group_ids.ids)],
                    }
                    record.write(vals)
                    success_count += 1
                else:
                    error_records.append(record.display_name)
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        message = _("Successfully updated access for %s records.") % success_count
        if error_records:
            message += _("\n\nErrors occurred for: %s") % ", ".join(error_records)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Access Update Complete'),
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
    reason = fields.Text(string='Reason for Transfer')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        # Get context data
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model and active_id:
            record = self.env[active_model].browse(active_id)
            defaults.update({
                'model_name': active_model,
                'record_id': active_id,
                'current_owner_id': record.owner_id.id if hasattr(record, 'owner_id') and record.owner_id else False,
            })

        return defaults

    def action_transfer(self):
        """Transfer ownership to the new owner"""
        self.ensure_one()

        record = self.env[self.model_name].browse(self.record_id)
        if not record.exists():
            raise ValidationError(_("Record not found."))

        if hasattr(record, 'transfer_ownership'):
            record.transfer_ownership(
                new_owner_id=self.new_owner_id.id,
                reason=self.reason
            )
        else:
            raise ValidationError(_("This record does not support ownership transfer."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Ownership Transferred'),
                'message': _('Ownership has been successfully transferred to %s.') % self.new_owner_id.name,
                'type': 'success',
            }
        }


class DelegateResponsibilityWizard(models.TransientModel):
    _name = 'tk.delegate.responsibility.wizard'
    _description = 'Delegate Responsibility Wizard'

    model_name = fields.Char(string='Model Name', required=True)
    record_id = fields.Integer(string='Record ID', required=True)
    user_ids = fields.Many2many('res.users', string='Delegate To', required=True)
    responsibility_type = fields.Selection([
        ('primary', 'Primary Responsibility'),
        ('secondary', 'Secondary Responsibility'),
        ('backup', 'Backup Responsibility'),
        ('temporary', 'Temporary Responsibility')
    ], string='Responsibility Type', default='primary')
    end_date = fields.Datetime(string='End Date')
    description = fields.Text(string='Description')
    reason = fields.Text(string='Reason for Delegation')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        # Get context data
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model and active_id:
            defaults.update({
                'model_name': active_model,
                'record_id': active_id,
            })

        return defaults

    def action_delegate(self):
        """Delegate responsibility to the selected users"""
        self.ensure_one()

        record = self.env[self.model_name].browse(self.record_id)
        if not record.exists():
            raise ValidationError(_("Record not found."))

        if hasattr(record, 'assign_responsibility'):
            record.assign_responsibility(
                user_ids=self.user_ids.ids,
                responsibility_type=self.responsibility_type,
                end_date=self.end_date,
                description=self.description,
                reason=self.reason
            )
        else:
            raise ValidationError(_("This record does not support responsibility delegation."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Responsibility Delegated'),
                'message': _('Responsibility has been successfully delegated to %s users.') % len(self.user_ids),
                'type': 'success',
            }
        }


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
    access_start_date = fields.Datetime(string='Access Start Date')
    access_end_date = fields.Datetime(string='Access End Date')
    reason = fields.Text(string='Reason')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        # Get context data
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model and active_id:
            record = self.env[active_model].browse(active_id)
            defaults.update({
                'model_name': active_model,
                'record_id': active_id,
                'access_level': record.access_level if hasattr(record, 'access_level') else 'internal',
                'allowed_user_ids': [(6, 0, record.allowed_user_ids.ids)] if hasattr(record, 'allowed_user_ids') else [],
                'allowed_group_ids': [(6, 0, record.allowed_group_ids.ids)] if hasattr(record, 'allowed_group_ids') else [],
                'custom_access_group_ids': [(6, 0, record.custom_access_group_ids.ids)] if hasattr(record, 'custom_access_group_ids') else [],
                'access_start_date': record.access_start_date if hasattr(record, 'access_start_date') else False,
                'access_end_date': record.access_end_date if hasattr(record, 'access_end_date') else False,
            })

        return defaults

    def action_update_access(self):
        """Update access settings for the record"""
        self.ensure_one()

        record = self.env[self.model_name].browse(self.record_id)
        if not record.exists():
            raise ValidationError(_("Record not found."))

        if hasattr(record, 'access_level'):
            vals = {
                'access_level': self.access_level,
                'allowed_user_ids': [(6, 0, self.allowed_user_ids.ids)],
                'allowed_group_ids': [(6, 0, self.allowed_group_ids.ids)],
                'access_start_date': self.access_start_date,
                'access_end_date': self.access_end_date,
            }
            if hasattr(record, 'custom_access_group_ids'):
                vals['custom_access_group_ids'] = [(6, 0, self.custom_access_group_ids.ids)]

            record.write(vals)
        else:
            raise ValidationError(_("This record does not support access management."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Access Updated'),
                'message': _('Access settings have been successfully updated.'),
                'type': 'success',
            }
        }
