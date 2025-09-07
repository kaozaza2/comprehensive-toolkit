from odoo import models, fields, api, _
from datetime import datetime, timedelta


class ComprehensiveDashboard(models.TransientModel):
    _name = 'tk.comprehensive.dashboard'
    _description = 'Comprehensive Toolkit Dashboard'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='Comprehensive Toolkit Dashboard', readonly=True)

    # Date filters
    date_from = fields.Date(
        string='Date From',
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )
    date_to = fields.Date(
        string='Date To',
        default=fields.Date.today
    )

    # Summary Statistics
    total_ownership_changes = fields.Integer(
        string='Total Ownership Changes',
        compute='_compute_statistics'
    )
    total_assignment_changes = fields.Integer(
        string='Total Assignment Changes',
        compute='_compute_statistics'
    )
    total_access_changes = fields.Integer(
        string='Total Access Changes',
        compute='_compute_statistics'
    )
    total_responsibility_changes = fields.Integer(
        string='Total Responsibility Changes',
        compute='_compute_statistics'
    )

    # Current Status Counts
    unowned_records_count = fields.Integer(
        string='Unowned Records',
        compute='_compute_current_status'
    )
    unassigned_records_count = fields.Integer(
        string='Unassigned Records',
        compute='_compute_current_status'
    )
    overdue_assignments_count = fields.Integer(
        string='Overdue Assignments',
        compute='_compute_current_status'
    )
    expired_responsibilities_count = fields.Integer(
        string='Expired Responsibilities',
        compute='_compute_current_status'
    )
    restricted_access_count = fields.Integer(
        string='Restricted Access Records',
        compute='_compute_current_status'
    )

    # User-specific counts
    my_owned_records_count = fields.Integer(
        string='My Owned Records',
        compute='_compute_user_statistics'
    )
    my_assignments_count = fields.Integer(
        string='My Assignments',
        compute='_compute_user_statistics'
    )
    my_responsibilities_count = fields.Integer(
        string='My Responsibilities',
        compute='_compute_user_statistics'
    )
    my_overdue_assignments_count = fields.Integer(
        string='My Overdue Assignments',
        compute='_compute_user_statistics'
    )
    my_co_owned_records_count = fields.Integer(
        string='My Co-owned Records',
        compute='_compute_user_statistics'
    )
    my_secondary_responsibilities_count = fields.Integer(
        string='My Secondary Responsibilities',
        compute='_compute_user_statistics'
    )

    # Recent Activity Statistics
    recent_ownership_transfers = fields.Integer(
        string='Recent Ownership Transfers',
        compute='_compute_recent_activity'
    )
    recent_new_assignments = fields.Integer(
        string='Recent New Assignments',
        compute='_compute_recent_activity'
    )
    recent_access_grants = fields.Integer(
        string='Recent Access Grants',
        compute='_compute_recent_activity'
    )
    recent_responsibility_changes = fields.Integer(
        string='Recent Responsibility Changes',
        compute='_compute_recent_activity'
    )

    # Additional fields for the view
    top_ownership_transferrer = fields.Char(
        string='Top Ownership Transferrer',
        compute='_compute_top_users'
    )
    top_assigner = fields.Char(
        string='Top Assigner',
        compute='_compute_top_users'
    )
    most_responsible_user = fields.Char(
        string='Most Responsible User',
        compute='_compute_top_users'
    )

    # Recent logs fields
    recent_ownership_logs = fields.Many2many(
        'tk.ownership.log',
        compute='_compute_recent_logs',
        string='Recent Ownership Logs'
    )
    recent_assignment_logs = fields.Many2many(
        'tk.assignment.log',
        compute='_compute_recent_logs',
        string='Recent Assignment Logs'
    )
    recent_access_logs = fields.Many2many(
        'tk.access.log',
        compute='_compute_recent_logs',
        string='Recent Access Logs'
    )
    recent_responsibility_logs = fields.Many2many(
        'tk.responsibility.log',
        compute='_compute_recent_logs',
        string='Recent Responsibility Logs'
    )

    def _compute_statistics(self):
        """Compute general statistics"""
        for dashboard in self:
            # Get date range
            date_from = dashboard.date_from or fields.Date.today() - timedelta(days=30)
            date_to = dashboard.date_to or fields.Date.today()

            # Convert dates to datetime for comparison
            datetime_from = fields.Datetime.to_datetime(date_from)
            datetime_to = fields.Datetime.to_datetime(date_to) + timedelta(days=1)

            # Count ownership changes
            dashboard.total_ownership_changes = self.env['tk.ownership.log'].search_count([
                ('create_date', '>=', datetime_from),
                ('create_date', '<', datetime_to)
            ])

            # Count assignment changes
            dashboard.total_assignment_changes = self.env['tk.assignment.log'].search_count([
                ('create_date', '>=', datetime_from),
                ('create_date', '<', datetime_to)
            ])

            # Count access changes
            dashboard.total_access_changes = self.env['tk.access.log'].search_count([
                ('create_date', '>=', datetime_from),
                ('create_date', '<', datetime_to)
            ])

            # Count responsibility changes
            dashboard.total_responsibility_changes = self.env['tk.responsibility.log'].search_count([
                ('create_date', '>=', datetime_from),
                ('create_date', '<', datetime_to)
            ])

    def _compute_current_status(self):
        """Compute current status counts from actual models using mixins"""
        for record in self:
            # Initialize counts
            unowned_count = 0
            unassigned_count = 0
            overdue_count = 0
            expired_responsibilities_count = 0
            restricted_access_count = 0

            # Count from ownable models
            for model_name in record.get_ownable_models():
                try:
                    model = self.env[model_name]
                    unowned_count += model.search_count([('is_owned', '=', False)])
                except:
                    continue

            # Count from assignable models
            for model_name in record.get_assignable_models():
                try:
                    model = self.env[model_name]
                    unassigned_count += model.search_count([('is_assigned', '=', False)])
                    overdue_count += model.search_count([('is_overdue', '=', True)])
                except:
                    continue

            # Count from responsible models
            for model_name in record.get_responsible_models():
                try:
                    model = self.env[model_name]
                    expired_responsibilities_count += model.search_count([('is_responsibility_expired', '=', True)])
                except:
                    continue

            # Count from accessible models
            for model_name in record.get_accessible_models():
                try:
                    model = self.env[model_name]
                    restricted_access_count += model.search_count([('access_level', '=', 'restricted')])
                except:
                    continue

            record.unowned_records_count = unowned_count
            record.unassigned_records_count = unassigned_count
            record.overdue_assignments_count = overdue_count
            record.expired_responsibilities_count = expired_responsibilities_count
            record.restricted_access_count = restricted_access_count

    def _compute_user_statistics(self):
        """Compute user-specific statistics from actual models using mixins"""
        for record in self:
            current_user = self.env.user

            # Initialize counts
            my_owned_count = 0
            my_assignments_count = 0
            my_responsibilities_count = 0
            my_overdue_assignments_count = 0
            my_co_owned_count = 0
            my_secondary_responsibilities_count = 0

            # Count from ownable models
            for model_name in record.get_ownable_models():
                try:
                    model = self.env[model_name]
                    my_owned_count += model.search_count([('owner_id', '=', current_user.id)])
                    my_co_owned_count += model.search_count([('co_owner_ids', 'in', [current_user.id])])
                except:
                    continue

            # Count from assignable models
            for model_name in record.get_assignable_models():
                try:
                    model = self.env[model_name]
                    my_assignments_count += model.search_count([('assigned_user_ids', 'in', [current_user.id])])
                    my_overdue_assignments_count += model.search_count([
                        ('assigned_user_ids', 'in', [current_user.id]),
                        ('is_overdue', '=', True)
                    ])
                except:
                    continue

            # Count from responsible models
            for model_name in record.get_responsible_models():
                try:
                    model = self.env[model_name]
                    my_responsibilities_count += model.search_count([('responsible_user_ids', 'in', [current_user.id])])
                    my_secondary_responsibilities_count += model.search_count(
                        [('secondary_responsible_ids', 'in', [current_user.id])])
                except:
                    continue

            record.my_owned_records_count = my_owned_count
            record.my_assignments_count = my_assignments_count
            record.my_responsibilities_count = my_responsibilities_count
            record.my_overdue_assignments_count = my_overdue_assignments_count
            record.my_co_owned_records_count = my_co_owned_count
            record.my_secondary_responsibilities_count = my_secondary_responsibilities_count

    def get_ownable_models(self):
        """Get all models that inherit from ownable mixin"""
        models = []
        for model_name in self.env.registry:
            model = self.env.registry[model_name]
            if hasattr(model, '_inherit') and 'tk.ownable.mixin' in (model._inherit or []):
                models.append(model_name)
        return models

    def get_assignable_models(self):
        """Get all models that inherit from assignable mixin"""
        models = []
        for model_name in self.env.registry:
            model = self.env.registry[model_name]
            if hasattr(model, '_inherit') and 'tk.assignable.mixin' in (model._inherit or []):
                models.append(model_name)
        return models

    def get_responsible_models(self):
        """Get all models that inherit from responsible mixin"""
        models = []
        for model_name in self.env.registry:
            model = self.env.registry[model_name]
            if hasattr(model, '_inherit') and 'tk.responsible.mixin' in (model._inherit or []):
                models.append(model_name)
        return models

    def get_accessible_models(self):
        """Get all models that inherit from accessible mixin"""
        models = []
        for model_name in self.env.registry:
            model = self.env.registry[model_name]
            if hasattr(model, '_inherit') and 'tk.accessible.mixin' in (model._inherit or []):
                models.append(model_name)
        return models

    def _compute_recent_activity(self):
        """Compute recent activity statistics"""
        for dashboard in self:
            # Last 7 days
            recent_date = fields.Datetime.now() - timedelta(days=7)

            dashboard.recent_ownership_transfers = self.env['tk.ownership.log'].search_count([
                ('create_date', '>=', recent_date),
                ('action', '=', 'transfer')
            ])

            dashboard.recent_new_assignments = self.env['tk.assignment.log'].search_count([
                ('create_date', '>=', recent_date),
                ('action', 'in', ['assign', 'assign_multiple'])
            ])

            dashboard.recent_access_grants = self.env['tk.access.log'].search_count([
                ('create_date', '>=', recent_date),
                ('action', 'like', 'grant%')
            ])

            dashboard.recent_responsibility_changes = self.env['tk.responsibility.log'].search_count([
                ('create_date', '>=', recent_date),
                ('action', 'in', ['assign', 'delegate', 'transfer'])
            ])

    def _compute_top_users(self):
        """Compute top users statistics"""
        for dashboard in self:
            # Get date range
            date_from = dashboard.date_from or fields.Date.today() - timedelta(days=30)
            date_to = dashboard.date_to or fields.Date.today()
            datetime_from = fields.Datetime.to_datetime(date_from)
            datetime_to = fields.Datetime.to_datetime(date_to) + timedelta(days=1)

            # Top ownership transferrer
            try:
                ownership_logs = self.env['tk.ownership.log'].read_group([
                    ('create_date', '>=', datetime_from),
                    ('create_date', '<', datetime_to),
                    ('action', '=', 'transfer')
                ], ['user_id'], ['user_id'])

                if ownership_logs:
                    top_transferrer = max(ownership_logs, key=lambda x: x['user_id_count'])
                    user = self.env['res.users'].browse(top_transferrer['user_id'][0])
                    dashboard.top_ownership_transferrer = f"{user.name} ({top_transferrer['user_id_count']} transfers)"
                else:
                    dashboard.top_ownership_transferrer = "No transfers"
            except:
                dashboard.top_ownership_transferrer = "No transfers"

            # Top assigner
            try:
                assignment_logs = self.env['tk.assignment.log'].read_group([
                    ('create_date', '>=', datetime_from),
                    ('create_date', '<', datetime_to)
                ], ['user_id'], ['user_id'])

                if assignment_logs:
                    top_assigner = max(assignment_logs, key=lambda x: x['user_id_count'])
                    user = self.env['res.users'].browse(top_assigner['user_id'][0])
                    dashboard.top_assigner = f"{user.name} ({top_assigner['user_id_count']} assignments)"
                else:
                    dashboard.top_assigner = "No assignments"
            except:
                dashboard.top_assigner = "No assignments"

            # Most responsible user
            try:
                responsibility_logs = self.env['tk.responsibility.log'].read_group([
                    ('create_date', '>=', datetime_from),
                    ('create_date', '<', datetime_to)
                ], ['new_responsible_user_id'], ['new_responsible_user_id'])

                if responsibility_logs:
                    most_responsible = max(responsibility_logs, key=lambda x: x['new_responsible_user_id_count'])
                    user = self.env['res.users'].browse(most_responsible['new_responsible_user_id'][0])
                    dashboard.most_responsible_user = f"{user.name} ({most_responsible['new_responsible_user_id_count']} responsibilities)"
                else:
                    dashboard.most_responsible_user = "No responsibilities"
            except:
                dashboard.most_responsible_user = "No responsibilities"

    def _compute_recent_logs(self):
        """Compute recent logs for display"""
        for dashboard in self:
            # Get recent logs (last 10 entries)
            try:
                ownership_logs = self.env['tk.ownership.log'].search([
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
                ], limit=10, order='create_date desc')
                dashboard.recent_ownership_logs = ownership_logs
            except:
                dashboard.recent_ownership_logs = self.env['tk.ownership.log']

            try:
                assignment_logs = self.env['tk.assignment.log'].search([
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
                ], limit=10, order='create_date desc')
                dashboard.recent_assignment_logs = assignment_logs
            except:
                dashboard.recent_assignment_logs = self.env['tk.assignment.log']

            try:
                access_logs = self.env['tk.access.log'].search([
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
                ], limit=10, order='create_date desc')
                dashboard.recent_access_logs = access_logs
            except:
                dashboard.recent_access_logs = self.env['tk.access.log']

            try:
                responsibility_logs = self.env['tk.responsibility.log'].search([
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=7))
                ], limit=10, order='create_date desc')
                dashboard.recent_responsibility_logs = responsibility_logs
            except:
                dashboard.recent_responsibility_logs = self.env['tk.responsibility.log']

    def refresh_dashboard(self):
        """Refresh dashboard data"""
        # Recompute all computed fields
        self._compute_statistics()
        self._compute_user_statistics()
        self._compute_recent_activity()
        self._compute_top_users()
        self._compute_recent_logs()
        self._compute_current_status()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Dashboard refreshed successfully'),
                'type': 'success'
            }
        }

    def action_view_ownership_logs(self):
        """Open ownership logs view"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ownership Logs'),
            'res_model': 'tk.ownership.log',
            'view_mode': 'tree,form',
            'domain': [
                ('create_date', '>=', self.date_from or fields.Date.today() - timedelta(days=30)),
                ('create_date', '<=', self.date_to or fields.Date.today())
            ],
            'context': {'create': False}
        }

    def action_view_assignment_logs(self):
        """Open assignment logs view"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assignment Logs'),
            'res_model': 'tk.assignment.log',
            'view_mode': 'tree,form',
            'domain': [
                ('create_date', '>=', self.date_from or fields.Date.today() - timedelta(days=30)),
                ('create_date', '<=', self.date_to or fields.Date.today())
            ],
            'context': {'create': False}
        }

    def action_view_access_logs(self):
        """Open access logs view"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Access Logs'),
            'res_model': 'tk.access.log',
            'view_mode': 'tree,form',
            'domain': [
                ('create_date', '>=', self.date_from or fields.Date.today() - timedelta(days=30)),
                ('create_date', '<=', self.date_to or fields.Date.today())
            ],
            'context': {'create': False}
        }

    def action_view_responsibility_logs(self):
        """Open responsibility logs view"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Responsibility Logs'),
            'res_model': 'tk.responsibility.log',
            'view_mode': 'tree,form',
            'domain': [
                ('create_date', '>=', self.date_from or fields.Date.today() - timedelta(days=30)),
                ('create_date', '<=', self.date_to or fields.Date.today())
            ],
            'context': {'create': False}
        }

    def action_view_my_owned_records(self):
        """Open user's owned records"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('My Owned Records'),
            'res_model': 'tk.ownership.log',
            'view_mode': 'tree,form',
            'domain': [('new_owner_id', '=', self.env.user.id)],
            'context': {'default_new_owner_id': self.env.user.id}
        }

    def action_view_my_assignments(self):
        """Open user's assignments"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('My Assignments'),
            'res_model': 'tk.assignment.log',
            'view_mode': 'tree,form',
            'domain': [('new_assigned_user_id', '=', self.env.user.id)],
            'context': {'default_new_assigned_user_id': self.env.user.id}
        }

    def action_view_my_responsibilities(self):
        """Open user's responsibilities"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('My Responsibilities'),
            'res_model': 'tk.responsibility.log',
            'view_mode': 'tree,form',
            'domain': [('new_responsible_user_id', '=', self.env.user.id)],
            'context': {'default_new_responsible_user_id': self.env.user.id}
        }
