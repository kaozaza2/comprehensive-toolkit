from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
        if self.is_temporary and self.expiry_date:
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
