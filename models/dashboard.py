from odoo import models, fields, api, _
from datetime import datetime, timedelta


class ComprehensiveDashboard(models.TransientModel):
    _name = 'tk.comprehensive.dashboard'
    _description = 'Comprehensive Toolkit Dashboard'

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

    # Current Status Counts (these would be computed based on models using the mixins)
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

    @api.depends('date_from', 'date_to')
    def _compute_statistics(self):
        for record in self:
            domain = [
                ('date', '>=', record.date_from),
                ('date', '<=', record.date_to)
            ]

            # Count changes in each log type
            record.total_ownership_changes = self.env['tk.ownership.log'].search_count(domain)
            record.total_assignment_changes = self.env['tk.assignment.log'].search_count(domain)
            record.total_access_changes = self.env['tk.access.log'].search_count(domain)
            record.total_responsibility_changes = self.env['tk.responsibility.log'].search_count(domain)

    @api.depends('date_from', 'date_to')
    def _compute_recent_activity(self):
        for record in self:
            recent_date = fields.Date.today() - timedelta(days=7)
            domain = [('date', '>=', recent_date)]

            # Count recent activity in each log type
            record.recent_ownership_transfers = self.env['tk.ownership.log'].search_count(
                domain + [('action', 'in', ['transfer', 'claim', 'release'])]
            )
            record.recent_new_assignments = self.env['tk.assignment.log'].search_count(
                domain + [('action', 'in', ['assign_multiple', 'add_assignee'])]
            )
            record.recent_access_grants = self.env['tk.access.log'].search_count(
                domain + [('action', 'in', ['grant_access', 'add_user'])]
            )
            record.recent_responsibility_changes = self.env['tk.responsibility.log'].search_count(
                domain + [('action', 'in', ['assign_multiple', 'delegate_multiple', 'transfer_multiple'])]
            )

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

    def _compute_current_status(self):
        """Compute current status counts from actual models using mixins"""
        for record in self:
            current_user = self.env.user

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
                    my_secondary_responsibilities_count += model.search_count([('secondary_responsible_ids', 'in', [current_user.id])])
                except:
                    continue

            record.my_owned_records_count = my_owned_count
            record.my_assignments_count = my_assignments_count
            record.my_responsibilities_count = my_responsibilities_count
            record.my_overdue_assignments_count = my_overdue_assignments_count
            record.my_co_owned_records_count = my_co_owned_count
            record.my_secondary_responsibilities_count = my_secondary_responsibilities_count

    def action_view_ownership_logs(self):
        """Open ownership logs view"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ownership Logs'),
            'res_model': 'tk.ownership.log',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_date_from': self.date_from, 'default_date_to': self.date_to}
        }

    def action_view_assignment_logs(self):
        """Open assignment logs view"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assignment Logs'),
            'res_model': 'tk.assignment.log',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_date_from': self.date_from, 'default_date_to': self.date_to}
        }

    def action_view_access_logs(self):
        """Open access logs view"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Access Logs'),
            'res_model': 'tk.access.log',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_date_from': self.date_from, 'default_date_to': self.date_to}
        }

    def action_view_responsibility_logs(self):
        """Open responsibility logs view"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Responsibility Logs'),
            'res_model': 'tk.responsibility.log',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_date_from': self.date_from, 'default_date_to': self.date_to}
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

    def action_refresh_dashboard(self):
        """Refresh all dashboard statistics"""
        self._compute_statistics()
        self._compute_current_status()
        self._compute_user_statistics()
        self._compute_recent_activity()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
