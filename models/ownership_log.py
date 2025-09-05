from odoo import models, fields, api, _


class OwnershipLog(models.Model):
    _name = 'tk.ownership.log'
    _description = 'Ownership Change Log'
    _order = 'date desc'
    _rec_name = 'display_name'

    model_name = fields.Char(
        string='Model',
        required=True,
        help="Name of the model for which ownership was changed"
    )
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        help="ID of the record for which ownership was changed"
    )
    action = fields.Selection([
        ('transfer', 'Transfer'),
        ('release', 'Release'),
        ('claim', 'Claim'),
        ('add_co_owner', 'Add Co-owner'),
        ('remove_co_owner', 'Remove Co-owner'),
        ('add_multiple_co_owners', 'Add Multiple Co-owners'),
        ('remove_all_co_owners', 'Remove All Co-owners')
    ], string='Action', required=True)
    old_owner_id = fields.Many2one(
        'res.users',
        string='Previous Owner',
        help="Previous owner before the change"
    )
    new_owner_id = fields.Many2one(
        'res.users',
        string='New Owner',
        help="New owner after the change"
    )
    reason = fields.Text(
        string='Reason',
        help="Reason for the ownership change"
    )
    user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
        help="User who made the ownership change"
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        help="Date and time of the ownership change"
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
