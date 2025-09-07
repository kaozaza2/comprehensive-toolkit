from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
