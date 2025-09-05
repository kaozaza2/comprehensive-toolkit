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
        """Update default settings based on group type"""
        if self.group_type == 'project':
            self.access_level = 'internal'
            self.auto_add_creator_as_manager = True
        elif self.group_type == 'department':
            self.access_level = 'internal'
            self.auto_add_creator_as_manager = True
        elif self.group_type == 'external':
            self.access_level = 'restricted'
            self.auto_add_creator_as_manager = True
        elif self.group_type == 'temporary':
            self.access_level = 'restricted'
            self.is_temporary = True
            self.auto_add_creator_as_manager = True

    @api.onchange('use_template', 'template_type')
    def _onchange_template(self):
        """Apply template settings"""
        if self.use_template and self.template_type:
            if self.template_type == 'project_team':
                self.group_type = 'project'
                self.access_level = 'internal'
                self.description = "Project team access group"
            elif self.template_type == 'department_team':
                self.group_type = 'department'
                self.access_level = 'internal'
                self.description = "Department team access group"
            elif self.template_type == 'external_partners':
                self.group_type = 'external'
                self.access_level = 'restricted'
                self.description = "External partners access group"
            elif self.template_type == 'temporary_access':
                self.group_type = 'temporary'
                self.access_level = 'restricted'
                self.is_temporary = True
                self.description = "Temporary access group"

    @api.onchange('copy_from_existing', 'existing_group_id')
    def _onchange_copy_existing(self):
        """Copy users from existing group"""
        if self.copy_from_existing and self.existing_group_id:
            self.user_ids = self.existing_group_id.user_ids
            self.manager_ids = self.existing_group_id.manager_ids

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        """Validate expiry date for temporary groups"""
        for record in self:
            if record.is_temporary and record.expiry_date:
                if record.expiry_date <= fields.Datetime.now():
                    raise ValidationError(_("Expiry date must be in the future."))

    def action_create_group(self):
        """Create the access group with selected settings"""
        self.ensure_one()

        # Validate data before creating
        self._validate_wizard_data()

        # Prepare group values
        group_vals = {
            'name': self.name,
            'description': self.description,
            'group_type': self.group_type,
            'access_level': self.access_level,
            'user_ids': [(6, 0, self.user_ids.ids)],
            'manager_ids': [(6, 0, self.manager_ids.ids)],
            'active': True,
        }

        # Add creator as manager if requested
        if self.auto_add_creator_as_manager:
            manager_ids = set(self.manager_ids.ids)
            manager_ids.add(self.env.user.id)
            group_vals['manager_ids'] = [(6, 0, list(manager_ids))]

        # Create the group
        group = self.env['tk.accessible.group'].create(group_vals)

        # Set up automatic expiry for temporary groups
        if self.is_temporary and self.expiry_date:
            # Create a scheduled action to archive the group
            self.env['ir.cron'].create({
                'name': f'Archive Temporary Group: {self.name}',
                'model_id': self.env.ref('comprehensive_toolkit.model_tk_accessible_group').id,
                'state': 'code',
                'code': f'model.browse({group.id}).write({{"active": False}})',
                'interval_number': 1,
                'interval_type': 'minutes',
                'nextcall': self.expiry_date,
                'numbercall': 1,
                'active': True,
            })

        # Return action to view the created group
        return {
            'type': 'ir.actions.act_window',
            'name': _('Access Group Created'),
            'res_model': 'tk.accessible.group',
            'res_id': group.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_and_assign(self):
        """Create group and assign to selected records"""
        group_action = self.action_create_group()
        group_id = group_action.get('res_id')

        # Get active records from context
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])

        if active_model and active_ids and group_id:
            # Assign the group to the active records
            records = self.env[active_model].browse(active_ids)
            for record in records:
                if hasattr(record, 'custom_access_group_ids'):
                    record.custom_access_group_ids = [(4, group_id)]

        return group_action

    def action_create_and_close(self):
        """Create the group and close the wizard"""
        result = self.action_create_group()
        # Modify the action to close the wizard
        return {
            'type': 'ir.actions.act_window_close',
        }

    def action_create_and_new(self):
        """Create the group and open a new wizard"""
        self.action_create_group()

        # Return action to open a new wizard
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Access Group'),
            'res_model': 'tk.accessible.group.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_type': self.group_type,
                'default_access_level': self.access_level,
            }
        }

    def _validate_wizard_data(self):
        """Validate wizard input data"""
        if not self.name:
            raise ValidationError(_("Group name is required."))

        # Check for duplicate names
        existing_group = self.env['tk.accessible.group'].search([
            ('name', '=', self.name)
        ])
        if existing_group:
            raise ValidationError(_("A group with this name already exists."))

        # Validate temporary group settings
        if self.is_temporary and not self.expiry_date:
            raise ValidationError(_("Expiry date is required for temporary groups."))

        if self.expiry_date and self.expiry_date <= fields.Datetime.now():
            raise ValidationError(_("Expiry date must be in the future."))

        # Validate project/department specific fields
        if self.group_type == 'project' and not self.project_name and 'Project:' not in self.name:
            raise ValidationError(_("Project name is required for project type groups."))

        if self.group_type == 'department' and not self.department_name and 'Department:' not in self.name:
            raise ValidationError(_("Department name is required for department type groups."))

    @api.model
    def default_get(self, fields_list):
        """Set default values based on context"""
        defaults = super().default_get(fields_list)

        # Set defaults from context
        context = self.env.context
        if context.get('default_users'):
            defaults['user_ids'] = [(6, 0, context.get('default_users', []))]

        if context.get('default_managers'):
            defaults['manager_ids'] = [(6, 0, context.get('default_managers', []))]

        return defaults
