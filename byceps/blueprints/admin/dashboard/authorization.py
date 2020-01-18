"""
byceps.blueprints.admin.dashboard.authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.util.authorization import create_permission_enum


AdminDashboardPermission = create_permission_enum('admin_dashboard', [
    'view_global',
    'view_brand',
    'view_party',
])
