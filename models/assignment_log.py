from odoo import models, fields, api, _


class AssignmentLog(models.Model):
    _name = 'tk.assignment.log'
    _description = 'Assignment Change Log'
    _order = 'date desc'
    _rec_name = 'display_name'

    model_name = fields.Char(
        string='Model',
        required=True,
        help="Name of the model for which assignment was changed"
    )
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        help="ID of the record for which assignment was changed"
    )
    action = fields.Selection([
        ('assign', 'Assign'),
        ('unassign', 'Unassign'),
        ('reassign', 'Reassign'),
        ('start', 'Start'),
        ('complete', 'Complete'),
        ('cancel', 'Cancel'),
        ('assign_multiple', 'Assign Multiple'),
        ('reassign_multiple', 'Reassign Multiple'),
        ('add_assignee', 'Add Assignee'),
        ('remove_assignee', 'Remove Assignee'),
        ('unassign_all', 'Unassign All')
    ], string='Action', required=True)
    old_assigned_user_id = fields.Many2one(
        'res.users',
        string='Previously Assigned To',
        help="Previously assigned user before the change"
    )
    new_assigned_user_id = fields.Many2one(
        'res.users',
        string='Newly Assigned To',
        help="Newly assigned user after the change"
    )
    extra_info = fields.Text(
        string='Additional Information',
        help="Additional information about multiple users involved"
    )
    reason = fields.Text(
        string='Reason',
        help="Reason for the assignment change"
    )
    user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
        help="User who made the assignment change"
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        help="Date and time of the assignment change"
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
