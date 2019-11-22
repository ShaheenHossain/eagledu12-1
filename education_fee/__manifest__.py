# -*- coding: utf-8 -*-
###################################################################################
#
###################################################################################

{
    "name": "Educational Fee Management",
    "version": "11.0.1.0.0",
    "author": "Cybrosys Techno Solutions",
    "category": 'Educational',
    "company": "Cybrosys Techno Solutions",
    "website": "http://www.eagle-it-services.com",
    'summary': 'Manage students fee',
    'description': """Manage students fee""",
    "depends": ['base', 'account', 'education_core'],
    "data": [
        'data/account_data.xml',
        'security/ir.model.access.csv',
        'views/fee_menu_view.xml',
        'views/fee_register.xml',
        'views/fee_structure.xml',
        'views/fee_types.xml',
        'views/fee_category.xml',
        'views/fee_journal_dashboard_view.xml',
        'views/fee_journal_inherit.xml',
        'reports/education_fee_receipt.xml',
        'reports/report.xml',
    ],
    "demo": [
        # 'demo/fee_data.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    "installable": True,
    "auto_install": False,
    'application': True,
}
