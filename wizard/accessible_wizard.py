from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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


class AccessibleGroupWizard(models.TransientModel):
    _name = 'tk.accessible.group.wizard'
    _description = 'Add Custom Access Group Wizard'

    # Basic group information
    name = fields.Char(
        string='Group Name',
        required=True,
        help="Name of the access group"
    )
    description = fields.Text(
        string='Description',
        help="Description of what this group is for"
    )
    group_type = fields.Selection([
        ('general', 'General Access'),
        ('project', 'Project Team'),
        ('department', 'Department'),
        ('temporary', 'Temporary Access'),
        ('external', 'External Users'),
        ('custom', 'Custom')
    ], string='Group Type', default='general', required=True,
       help="Type of access group")

    access_level = fields.Selection([
        ('public', 'Public - Anyone can see'),
        ('internal', 'Internal - Internal users can see'),
        ('restricted', 'Restricted - Only managers can see'),
        ('private', 'Private - Only creator can see')
    ], string='Visibility', default='internal', required=True,
       help="Who can see this group")

    # User selection
    user_ids = fields.Many2many(
        'res.users',
        string='Users',
        help="Users to add to this group"
    )
    manager_ids = fields.Many2many(
        'res.users',
        'wizard_managers_rel',
        'wizard_id',
        'user_id',
        string='Group Managers',
        help="Users who can manage this group (optional)"
    )

    # Template options
    use_template = fields.Boolean(
        string='Use Template',
        help="Create group based on a template"
    )
    template_type = fields.Selection([
        ('project_team', 'Project Team Template'),
        ('department_team', 'Department Team Template'),
        ('external_partners', 'External Partners Template'),
        ('temporary_access', 'Temporary Access Template')
    ], string='Template Type',
       help="Select a pre-configured template")

    # Quick setup options
    auto_add_creator_as_manager = fields.Boolean(
        string='Add Creator as Manager',
        default=True,
        help="Automatically add the group creator as a manager"
    )
    copy_from_existing = fields.Boolean(
        string='Copy from Existing Group',
        help="Copy users from an existing group"
    )
    existing_group_id = fields.Many2one(
        'tk.accessible.group',
        string='Existing Group',
        help="Group to copy users from"
    )

    # Temporary group options
    is_temporary = fields.Boolean(
        string='Temporary Group',
        help="This group will expire after a certain date"
    )
    expiry_date = fields.Datetime(
        string='Expiry Date',
        help="Date when this group should be automatically archived"
    )

    # Department/Project specific fields
    project_name = fields.Char(
        string='Project Name',
        help="Name of the project (for project type groups)"
    )
    department_name = fields.Char(
        string='Department Name',
        help="Name of the department (for department type groups)"
    )

    @api.onchange('group_type')
    def _onchange_group_type(self):
        """Update fields based on group type selection"""
        if self.group_type == 'temporary':
            self.is_temporary = True
        else:
            self.is_temporary = False
            self.expiry_date = False

    @api.onchange('use_template')
    def _onchange_use_template(self):
        """Clear template type when not using template"""
        if not self.use_template:
            self.template_type = False

    @api.onchange('copy_from_existing')
    def _onchange_copy_from_existing(self):
        """Clear existing group when not copying"""
        if not self.copy_from_existing:
            self.existing_group_id = False

    @api.onchange('existing_group_id')
    def _onchange_existing_group_id(self):
        """Copy users from existing group"""
        if self.existing_group_id:
            self.user_ids = [(6, 0, self.existing_group_id.user_ids.ids)]
            self.manager_ids = [(6, 0, self.existing_group_id.manager_ids.ids)]

    def _prepare_group_values(self):
        """Prepare values for group creation"""
        vals = {
            'name': self.name,
            'description': self.description,
            'group_type': self.group_type,
            'access_level': self.access_level,
            'user_ids': [(6, 0, self.user_ids.ids)],
        }

        # Add managers
        manager_ids = list(self.manager_ids.ids)
        if self.auto_add_creator_as_manager and self.env.user.id not in manager_ids:
            manager_ids.append(self.env.user.id)

        if manager_ids:
            vals['manager_ids'] = [(6, 0, manager_ids)]

        # Handle temporary groups
        if self.is_temporary:
            if not self.expiry_date:
                raise ValidationError(_("Expiry date must be set for temporary groups"))

            vals['expiry_date'] = self.expiry_date

        return vals

    def action_create_group(self):
        """Create the access group"""
        vals = self._prepare_group_values()
        group = self.env['tk.accessible.group'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Access Group'),
            'res_model': 'tk.accessible.group',
            'res_id': group.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_and_assign(self):
        """Create group and assign to current record"""
        vals = self._prepare_group_values()
        group = self.env['tk.accessible.group'].create(vals)

        # If called from a specific record context, assign the group
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model and active_id:
            record = self.env[active_model].browse(active_id)
            if hasattr(record, 'tk_access_group_ids'):
                record.tk_access_group_ids = [(4, group.id)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Group created and assigned successfully'),
                'type': 'success'
            }
        }

    def action_create_and_close(self):
        """Create group and close wizard"""
        vals = self._prepare_group_values()
        group = self.env['tk.accessible.group'].create(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Group "%s" created successfully') % group.name,
                'type': 'success'
            }
        }

    def action_create_and_new(self):
        """Create group and open wizard for creating another"""
        vals = self._prepare_group_values()
        group = self.env['tk.accessible.group'].create(vals)

        # Return action to open new wizard
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Access Group'),
            'res_model': 'tk.accessible.group.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_type': self.group_type,
                'default_access_level': self.access_level,
            }
        }
