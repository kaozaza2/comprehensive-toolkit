/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class ComprehensiveDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            isLoading: false,
            lastRefresh: new Date(),
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        this.state.isLoading = true;
        try {
            // Dashboard data is loaded through the form view
            // This is a placeholder for any additional JS functionality
            this.state.lastRefresh = new Date();
        } catch (error) {
            this.notification.add(
                "Failed to load dashboard data",
                { type: "danger" }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    async refreshDashboard() {
        this.state.isLoading = true;
        try {
            await this.rpc("/web/dataset/call_button", {
                model: "tk.comprehensive.dashboard",
                method: "refresh_dashboard",
                args: [[]],
            });

            this.notification.add(
                "Dashboard refreshed successfully",
                { type: "success" }
            );

            // Reload the current view
            window.location.reload();
        } catch (error) {
            this.notification.add(
                "Failed to refresh dashboard",
                { type: "danger" }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    // Auto-refresh functionality
    startAutoRefresh(interval = 300000) { // 5 minutes
        setInterval(() => {
            this.loadDashboardData();
        }, interval);
    }

    // Utility function to format numbers
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Chart data preparation (for future chart integration)
    prepareChartData(logs) {
        const chartData = {};
        logs.forEach(log => {
            const date = log.date.split(' ')[0];
            chartData[date] = (chartData[date] || 0) + 1;
        });
        return chartData;
    }
}

ComprehensiveDashboard.template = "comprehensive_toolkit.Dashboard";

// Register the component
registry.category("actions").add("comprehensive_toolkit_dashboard", ComprehensiveDashboard);

// Additional utility functions for the comprehensive toolkit
export const ComprehensiveToolkitUtils = {

    // Format action labels
    formatActionLabel(action, modelType) {
        const actionLabels = {
            ownership: {
                'transfer': 'Transferred',
                'release': 'Released',
                'claim': 'Claimed'
            },
            assignment: {
                'assign': 'Assigned',
                'unassign': 'Unassigned',
                'reassign': 'Reassigned',
                'start': 'Started',
                'complete': 'Completed',
                'cancel': 'Cancelled'
            },
            access: {
                'grant_user': 'User Access Granted',
                'revoke_user': 'User Access Revoked',
                'grant_group': 'Group Access Granted',
                'revoke_group': 'Group Access Revoked',
                'change_level': 'Access Level Changed'
            },
            responsibility: {
                'assign': 'Assigned',
                'delegate': 'Delegated',
                'revoke': 'Revoked',
                'transfer': 'Transferred',
                'escalate': 'Escalated',
                'add_secondary': 'Secondary Added',
                'remove_secondary': 'Secondary Removed'
            }
        };

        return actionLabels[modelType]?.[action] || action;
    },

    // Get status badge class
    getStatusBadgeClass(status) {
        const statusClasses = {
            'assigned': 'badge-info',
            'in_progress': 'badge-warning',
            'completed': 'badge-success',
            'cancelled': 'badge-danger',
            'unassigned': 'badge-secondary',
            'public': 'badge-success',
            'internal': 'badge-info',
            'restricted': 'badge-warning',
            'private': 'badge-danger'
        };

        return statusClasses[status] || 'badge-secondary';
    },

    // Format datetime for display
    formatDateTime(dateTime) {
        if (!dateTime) return '';

        const date = new Date(dateTime);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return 'Today ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } else if (diffDays === 1) {
            return 'Yesterday ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } else if (diffDays < 7) {
            return diffDays + ' days ago';
        } else {
            return date.toLocaleDateString();
        }
    }
};

// Global event handlers for the comprehensive toolkit
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers for dashboard cards
    const dashboardCards = document.querySelectorAll('.card[data-action]');
    dashboardCards.forEach(card => {
        card.addEventListener('click', function() {
            const action = this.dataset.action;
            if (action) {
                // Trigger the appropriate action
                console.log('Dashboard card clicked:', action);
            }
        });
    });

    // Add tooltips to dashboard elements
    const tooltipElements = document.querySelectorAll('[title]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            // Add tooltip functionality here if needed
        });
    });
});
