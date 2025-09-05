{
    'name': 'Comprehensive Toolkit',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Comprehensive toolkit with ownership, assignment, access control, and responsibility management',
    'description': """
        This module provides comprehensive mixins and functionality for:
        - Ownership management (ownable, hasOwnable, transfer, release)
        - Assignment management (assignable, hasAssignable)
        - Access control (accessible, hasAccessible)
        - Responsibility management (responsible, hasResponsible)
        - Admin dashboard with tracking logs and reasons
        - Example models demonstrating mixin usage with comprehensive actions
        
        Compatible with Odoo 16.0 and higher versions.
    """,
    'author': 'MokiMikore',
    'website': 'https://github.com/kaozaza2',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/ownership_log_views.xml',
        'views/assignment_log_views.xml',
        'views/access_log_views.xml',
        'views/responsibility_log_views.xml',
        'views/accessible_group_views.xml',
        'views/dashboard_views.xml',
        'views/wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'comprehensive_toolkit/static/src/css/dashboard.css',
            'comprehensive_toolkit/static/src/js/dashboard.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
