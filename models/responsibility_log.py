from odoo import models, fields, api, _


class ResponsibilityLog(models.Model):
    _name = 'tk.responsibility.log'
    _description = 'Responsibility Change Log'
    _order = 'date desc'
    _rec_name = 'display_name'

    model_name = fields.Char(
        string='Model',
        required=True,
        help="Name of the model for which responsibility was changed"
    )
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        help="ID of the record for which responsibility was changed"
    )
    action = fields.Selection([
        ('assign', 'Assign'),
        ('delegate', 'Delegate'),
        ('revoke', 'Revoke'),
        ('transfer', 'Transfer'),
        ('escalate', 'Escalate'),
        ('add_secondary', 'Add Secondary'),
        ('remove_secondary', 'Remove Secondary'),
        ('assign_multiple', 'Assign Multiple'),
        ('delegate_multiple', 'Delegate Multiple'),
        ('transfer_multiple', 'Transfer Multiple'),
        ('add_responsible', 'Add Responsible'),
        ('remove_responsible', 'Remove Responsible'),
        ('revoke_all', 'Revoke All')
    ], string='Action', required=True)
    old_responsible_user_id = fields.Many2one(
        'res.users',
        string='Previously Responsible',
        help="Previously responsible user before the change"
    )
    new_responsible_user_id = fields.Many2one(
        'res.users',
        string='Newly Responsible',
        help="Newly responsible user after the change"
    )
    extra_info = fields.Text(
        string='Additional Information',
        help="Additional information about multiple users involved"
    )
    reason = fields.Text(
        string='Reason',
        help="Reason for the responsibility change"
    )
    user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
        help="User who made the responsibility change"
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        help="Date and time of the responsibility change"
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    record_reference = fields.Char(
        string='Record Reference',
        compute='_compute_record_reference',
        help="Reference to the affected record"
    )

    @api.depends('model_name', 'res_id', 'action', 'date')
    def _compute_display_name(self):
        for record in self:
            action_label = dict(record._fields['action'].selection)[record.action]
            record.display_name = f"{record.model_name} {record.res_id} - {action_label} ({record.date.strftime('%Y-%m-%d %H:%M')})"

    @api.depends('model_name', 'res_id')
    def _compute_record_reference(self):
        for record in self:
            if record.model_name and record.res_id:
                try:
                    target_record = self.env[record.model_name].browse(record.res_id)
                    if target_record.exists():
                        record.record_reference = target_record.display_name or f"ID: {record.res_id}"
                    else:
                        record.record_reference = f"Deleted Record (ID: {record.res_id})"
                except:
                    record.record_reference = f"Invalid Model/ID: {record.model_name}/{record.res_id}"
            else:
                record.record_reference = "N/A"

    def open_record(self):
        """Open the related record"""
        self.ensure_one()
        if not self.model_name or not self.res_id:
            return False

        try:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.model_name,
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'current',
            }
        except:
            return False
