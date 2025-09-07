from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResponsibilityAssignWizard(models.TransientModel):
    _name = 'tk.responsibility.assign.wizard'
    _description = 'Responsibility Assignment Wizard'

    responsible_user_ids = fields.Many2many('res.users', string='Responsible Users', required=True)
    responsibility_end_date = fields.Datetime(string='End Date')
    responsibility_description = fields.Text(string='Description')
    is_secondary = fields.Boolean(string='Secondary Responsibility', default=False)
    reason = fields.Text(string='Reason')
    record_count = fields.Integer(string='Records Count', default=0)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            defaults['record_count'] = len(self.env.context.get('active_ids', []))
        return defaults

    def action_assign_responsibility(self):
        """Assign responsibility to selected records"""
        self.ensure_one()

        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not active_ids or not active_model:
            raise ValidationError(_("No records selected for responsibility assignment."))

        records = self.env[active_model].browse(active_ids)
        success_count = 0
        error_records = []

        for record in records:
            try:
                if self.is_secondary:
                    record.assign_secondary_responsibility(
                        user_ids=self.responsible_user_ids.ids,
                        reason=self.reason
                    )
                else:
                    record.assign_responsibility(
                        user_ids=self.responsible_user_ids.ids,
                        end_date=self.responsibility_end_date,
                        description=self.responsibility_description,
                        reason=self.reason
                    )
                success_count += 1
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        responsibility_type = "secondary responsibility" if self.is_secondary else "responsibility"
        if error_records:
            message = _("Assignment completed with errors.\nSuccessful: %s\nErrors: %s") % (
                success_count, '\n'.join(error_records)
            )
        else:
            message = _("Successfully assigned %s to %s records.") % (responsibility_type, success_count)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Responsibility Assignment Complete'),
                'message': message,
                'type': 'warning' if error_records else 'success',
                'sticky': True,
            }
        }


class ResponsibilityTransferWizard(models.TransientModel):
    _name = 'tk.responsibility.transfer.wizard'
    _description = 'Responsibility Transfer Wizard'

    transfer_type = fields.Selection([
        ('delegate', 'Delegate'),
        ('transfer', 'Transfer'),
        ('escalate', 'Escalate')
    ], string='Transfer Type', required=True, default='transfer')
    target_user_ids = fields.Many2many('res.users', string='Target Users', required=True)
    is_secondary = fields.Boolean(string='Secondary Responsibility', default=False)
    reason = fields.Text(string='Reason')
    record_count = fields.Integer(string='Records Count', default=0)
    current_responsible_info = fields.Html(string='Current Responsibility', compute='_compute_current_responsible_info')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            defaults['record_count'] = len(self.env.context.get('active_ids', []))
        return defaults

    @api.depends('record_count')
    def _compute_current_responsible_info(self):
        for wizard in self:
            active_ids = self.env.context.get('active_ids', [])
            active_model = self.env.context.get('active_model')

            if active_ids and active_model:
                records = self.env[active_model].browse(active_ids[:5])  # Show first 5 records
                info_html = "<ul>"
                for record in records:
                    if hasattr(record, 'responsible_user_ids'):
                        primary = ', '.join(record.responsible_user_ids.mapped('name')) or 'None'
                        secondary = ', '.join(record.secondary_responsible_ids.mapped('name')) or 'None'
                        info_html += f"<li><strong>{record.display_name}</strong><br/>Primary: {primary}<br/>Secondary: {secondary}</li>"
                if len(active_ids) > 5:
                    info_html += f"<li>... and {len(active_ids) - 5} more records</li>"
                info_html += "</ul>"
                wizard.current_responsible_info = info_html
            else:
                wizard.current_responsible_info = "<p>No records selected</p>"

    def action_transfer_responsibility(self):
        """Transfer responsibility for selected records"""
        self.ensure_one()

        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not active_ids or not active_model:
            raise ValidationError(_("No records selected for responsibility transfer."))

        records = self.env[active_model].browse(active_ids)
        success_count = 0
        error_records = []

        for record in records:
            try:
                if self.transfer_type == 'escalate':
                    if len(self.target_user_ids) != 1:
                        raise ValidationError(_("Escalation requires exactly one target user."))
                    record.escalate_responsibility(
                        escalation_user_id=self.target_user_ids[0].id,
                        reason=self.reason
                    )
                elif self.is_secondary:
                    if self.transfer_type == 'delegate':
                        record.delegate_secondary_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                    else:  # transfer
                        record.transfer_secondary_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                else:
                    if self.transfer_type == 'delegate':
                        record.delegate_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                    else:  # transfer
                        record.transfer_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                success_count += 1
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        if error_records:
            message = _("Transfer completed with errors.\nSuccessful: %s\nErrors: %s") % (
                success_count, '\n'.join(error_records)
            )
        else:
            message = _("Successfully %s responsibility for %s records.") % (
                self.transfer_type + 'd', success_count
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Responsibility Transfer Complete'),
                'message': message,
                'type': 'warning' if error_records else 'success',
                'sticky': True,
            }
        }


class ResponsibilityRevokeWizard(models.TransientModel):
    _name = 'tk.responsibility.revoke.wizard'
    _description = 'Responsibility Revocation Wizard'

    revoke_type = fields.Selection([
        ('all', 'All Responsibility'),
        ('primary', 'Primary Only'),
        ('secondary', 'Secondary Only')
    ], string='Revoke Type', required=True, default='all')
    reason = fields.Text(string='Reason', required=True)
    record_count = fields.Integer(string='Records Count', default=0)
    current_assignments_info = fields.Html(string='Current Assignments', compute='_compute_current_assignments_info')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            defaults['record_count'] = len(self.env.context.get('active_ids', []))
        return defaults

    @api.depends('record_count')
    def _compute_current_assignments_info(self):
        for wizard in self:
            active_ids = self.env.context.get('active_ids', [])
            active_model = self.env.context.get('active_model')

            if active_ids and active_model:
                records = self.env[active_model].browse(active_ids[:5])
                info_html = "<ul>"
                for record in records:
                    if hasattr(record, 'responsible_user_ids'):
                        primary = ', '.join(record.responsible_user_ids.mapped('name')) or 'None'
                        secondary = ', '.join(record.secondary_responsible_ids.mapped('name')) or 'None'
                        info_html += f"<li><strong>{record.display_name}</strong><br/>Primary: {primary}<br/>Secondary: {secondary}</li>"
                if len(active_ids) > 5:
                    info_html += f"<li>... and {len(active_ids) - 5} more records</li>"
                info_html += "</ul>"
                wizard.current_assignments_info = info_html
            else:
                wizard.current_assignments_info = "<p>No records selected</p>"

    def action_revoke_responsibility(self):
        """Revoke responsibility for selected records"""
        self.ensure_one()

        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not active_ids or not active_model:
            raise ValidationError(_("No records selected for responsibility revocation."))

        records = self.env[active_model].browse(active_ids)
        success_count = 0
        error_records = []

        for record in records:
            try:
                if self.revoke_type == 'all':
                    record.revoke_all_responsibility(reason=self.reason)
                elif self.revoke_type == 'primary':
                    record.write({'responsible_user_ids': [(5, 0, 0)]})
                    record._log_responsibility_change('revoke_primary', record.responsible_user_ids, None, self.reason)
                elif self.revoke_type == 'secondary':
                    record.write({'secondary_responsible_ids': [(5, 0, 0)]})
                    record._log_responsibility_change('revoke_secondary', record.secondary_responsible_ids, None,
                                                      self.reason)
                success_count += 1
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        if error_records:
            message = _("Revocation completed with errors.\nSuccessful: %s\nErrors: %s") % (
                success_count, '\n'.join(error_records)
            )
        else:
            message = _("Successfully revoked %s responsibility for %s records.") % (
                self.revoke_type, success_count
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Responsibility Revocation Complete'),
                'message': message,
                'type': 'warning' if error_records else 'success',
                'sticky': True,
            }
        }


class BulkResponsibilityWizard(models.TransientModel):
    _name = 'tk.bulk.responsibility.wizard'
    _description = 'Bulk Responsibility Operations Wizard'

    operation_type = fields.Selection([
        ('assign', 'Assign'),
        ('transfer', 'Transfer'),
        ('escalate', 'Escalate'),
        ('revoke', 'Revoke')
    ], string='Operation Type', required=True)
    target_user_ids = fields.Many2many('res.users', string='Target Users')
    is_secondary = fields.Boolean(string='Secondary Responsibility', default=False)
    responsibility_end_date = fields.Datetime(string='End Date')
    responsibility_description = fields.Text(string='Description')
    reason = fields.Text(string='Reason')
    record_count = fields.Integer(string='Records Count', default=0)
    operation_summary = fields.Html(string='Operation Summary', compute='_compute_operation_summary')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            defaults['record_count'] = len(self.env.context.get('active_ids', []))
        return defaults

    @api.depends('operation_type', 'target_user_ids', 'is_secondary', 'record_count')
    def _compute_operation_summary(self):
        for wizard in self:
            if wizard.operation_type and wizard.record_count:
                summary = f"<p><strong>Operation:</strong> {wizard.operation_type.title()}</p>"
                summary += f"<p><strong>Records:</strong> {wizard.record_count}</p>"

                if wizard.operation_type != 'revoke':
                    target_names = ', '.join(wizard.target_user_ids.mapped('name')) or 'None selected'
                    summary += f"<p><strong>Target Users:</strong> {target_names}</p>"

                if wizard.operation_type in ['assign', 'transfer'] and wizard.is_secondary:
                    summary += f"<p><strong>Type:</strong> Secondary Responsibility</p>"

                wizard.operation_summary = summary
            else:
                wizard.operation_summary = "<p>Configure operation parameters to see summary</p>"

    def action_execute_operation(self):
        """Execute the bulk responsibility operation"""
        self.ensure_one()

        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not active_ids or not active_model:
            raise ValidationError(_("No records selected for bulk operation."))

        records = self.env[active_model].browse(active_ids)
        success_count = 0
        error_records = []

        for record in records:
            try:
                if self.operation_type == 'assign':
                    if self.is_secondary:
                        record.assign_secondary_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                    else:
                        record.assign_responsibility(
                            user_ids=self.target_user_ids.ids,
                            end_date=self.responsibility_end_date,
                            description=self.responsibility_description,
                            reason=self.reason
                        )
                elif self.operation_type == 'transfer':
                    if self.is_secondary:
                        record.transfer_secondary_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                    else:
                        record.transfer_responsibility(
                            user_ids=self.target_user_ids.ids,
                            reason=self.reason
                        )
                elif self.operation_type == 'escalate':
                    if len(self.target_user_ids) != 1:
                        raise ValidationError(_("Escalation requires exactly one target user."))
                    record.escalate_responsibility(
                        escalation_user_id=self.target_user_ids[0].id,
                        reason=self.reason
                    )
                elif self.operation_type == 'revoke':
                    record.revoke_all_responsibility(reason=self.reason)

                success_count += 1
            except Exception as e:
                error_records.append(f"{record.display_name}: {str(e)}")

        # Show result message
        if error_records:
            message = _("Operation completed with errors.\nSuccessful: %s\nErrors: %s") % (
                success_count, '\n'.join(error_records)
            )
        else:
            message = _("Successfully executed %s operation on %s records.") % (
                self.operation_type, success_count
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Operation Complete'),
                'message': message,
                'type': 'warning' if error_records else 'success',
                'sticky': True,
            }
        }