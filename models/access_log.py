from odoo import models, fields, api, _


class AccessLog(models.Model):
    _name = 'tk.access.log'
    _description = 'Access Control Log'
    _order = 'date desc'
    _rec_name = 'display_name'

    # Record reference
    model_name = fields.Char('Model', required=True, index=True)
    res_id = fields.Integer('Record ID', required=True, index=True)
    record_reference = fields.Char('Record', compute='_compute_record_reference', store=True)

    # Action details
    action = fields.Selection([
        ('grant_user', 'Grant User Access'),
        ('revoke_user', 'Revoke User Access'),
        ('grant_group', 'Grant Group Access'),
        ('revoke_group', 'Revoke Group Access'),
        ('grant_custom_group', 'Grant Custom Group Access'),
        ('revoke_custom_group', 'Revoke Custom Group Access'),
        ('bulk_grant_users', 'Bulk Grant Users'),
        ('bulk_revoke_users', 'Bulk Revoke Users'),
        ('create_assign_custom_group', 'Create and Assign Custom Group'),
        ('change_level', 'Change Access Level'),
        ('change_duration', 'Change Access Duration'),
    ], string='Action', required=True, index=True)

    # Target details
    target_user_id = fields.Many2one('res.users', 'Target User')
    target_group_id = fields.Many2one('res.groups', 'Target Group')
    target_custom_group_id = fields.Many2one('tk.accessible.group', 'Target Custom Group')

    # Metadata
    user_id = fields.Many2one('res.users', 'Changed By', required=True, default=lambda self: self.env.user)
    date = fields.Datetime('Date', required=True, default=fields.Datetime.now)
    reason = fields.Text('Reason')
    extra_info = fields.Text('Additional Information')

    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)

    @api.depends('model_name', 'res_id')
    def _compute_record_reference(self):
        for log in self:
            if log.model_name and log.res_id:
                try:
                    record = self.env[log.model_name].browse(log.res_id)
                    if record.exists():
                        log.record_reference = record.display_name
                    else:
                        log.record_reference = f"{log.model_name}({log.res_id}) [Deleted]"
                except Exception:
                    log.record_reference = f"{log.model_name}({log.res_id}) [Error]"
            else:
                log.record_reference = False

    @api.depends('action', 'record_reference', 'target_user_id', 'target_group_id', 'target_custom_group_id')
    def _compute_display_name(self):
        for log in self:
            action_name = dict(log._fields['action'].selection).get(log.action, log.action)
            target = ""

            if log.target_user_id:
                target = f" for {log.target_user_id.name}"
            elif log.target_group_id:
                target = f" for {log.target_group_id.name}"
            elif log.target_custom_group_id:
                target = f" for {log.target_custom_group_id.name}"

            log.display_name = f"{action_name}{target} on {log.record_reference or 'Unknown Record'}"

    def open_record(self):
        """Open the referenced record"""
        self.ensure_one()
        if not self.model_name or not self.res_id:
            return False

        try:
            record = self.env[self.model_name].browse(self.res_id)
            if not record.exists():
                raise ValidationError(_("The referenced record no longer exists."))

            return {
                'type': 'ir.actions.act_window',
                'res_model': self.model_name,
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            raise ValidationError(_("Cannot open record: %s") % str(e))

    @api.model
    def cleanup_old_logs(self, days=90):
        """Clean up old access logs"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([('date', '<', cutoff_date)])
        count = len(old_logs)
        old_logs.unlink()
        return count
