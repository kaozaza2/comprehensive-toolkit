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
