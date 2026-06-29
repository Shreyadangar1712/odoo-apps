{
    "name": "GitHub Odoo Integration",
    "version": "18.0.1.0.0",
    "summary": "Integrate Odoo Projects with GitHub repositories, branches, and collaborators",
    "description": """
GitHub Odoo Integration
=======================

Features
--------
* Create GitHub repositories directly from Odoo Projects
* Create GitHub branches from Odoo Tasks
* Send collaborator invitations to GitHub users
* Store repository and branch URLs
* Manage GitHub information from Odoo

Benefits
--------
* Centralized project management
* Improved collaboration between developers and project managers
* Seamless GitHub integration within Odoo
""",
    "author": "Rishvi Ltd",
    "website": "https://rishvi.co.uk/",
    "category": "Project",
    "price": 0.0,
    "currency": "USD",
    "depends": [
        "base",
        "project",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/project_views.xml",
        "views/task_views.xml",
        "views/employee.xml",
        "views/res_users.xml"
    ],
    
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "OPL-1",
}
