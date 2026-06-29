from odoo import fields, models,api
from odoo.exceptions import UserError
import requests
import re

import logging

_logger = logging.getLogger(__name__)



class ProjectTask(models.Model):
    _inherit = 'project.task'

    github_create_branch = fields.Boolean(
        string="Create Branch in GitHub"
    )

    github_branch_name = fields.Char(
        string="Branch Name"
    )

    github_repo_id = fields.Many2one(
        'github.repository',
        string="Repository",
        related='project_id.github_repo_id',
        store=True,
        
    )

    github_branch_created = fields.Boolean(
        string="Branch Created",
        readonly=True
    )

    github_branch_url = fields.Char(
        string="Branch URL",
        readonly=True
    )


    @api.onchange('name')
    def _onchange_name_set_branch(self):
        if self.name:
            branch_name = f"{self.name}-{self.env.user.login}"

            import re
            branch_name = branch_name.lower()
            branch_name = re.sub(r'[^a-z0-9\- ]', '', branch_name)
            branch_name = branch_name.replace(' ', '-')

            self.github_branch_name = branch_name



   

    def action_create_github_branch(self):
        self.ensure_one()

        if not self.github_branch_name:
            raise UserError(
                ("Please enter the Branch Name.")
            )

        if not self.github_repo_id:
            raise UserError(
                ("No GitHub repository is linked to this project.")
            )

        token = self.env['ir.config_parameter'].sudo().get_param(
            'github_token'
        )

        if not token:
            raise UserError(
                ("GitHub token is not configured.")
            )

        repo_full_name = self.github_repo_id.full_name

        if not repo_full_name:
            raise UserError(
                ("Repository full name is missing.")
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        _logger.info("========== CREATE BRANCH START ==========")
        _logger.info("Repository: %s", repo_full_name)
        _logger.info("Branch Name: %s", self.github_branch_name)

        # --------------------------------------------------
        # Fetch Repository Details
        # --------------------------------------------------

        repo_response = requests.get(
            f"https://api.github.com/repos/{repo_full_name}",
            headers=headers,
            timeout=30,
        )

        _logger.info(
            "Repository Fetch Status: %s",
            repo_response.status_code
        )

        _logger.info(
            "Repository Fetch Response: %s",
            repo_response.text
        )

        if repo_response.status_code != 200:

            _logger.error(
                "GitHub Repository Fetch Failed. "
                "Status=%s Response=%s",
                repo_response.status_code,
                repo_response.text
            )

            if repo_response.status_code == 401:
                raise UserError(
                    ("GitHub authentication failed. Please verify the configured token.")
                )

            elif repo_response.status_code == 403:
                raise UserError(
                    ("Permission denied. The configured GitHub token does not have sufficient access.")
                )

            elif repo_response.status_code == 404:
                raise UserError(
                    ("The selected GitHub repository could not be found.")
                )

            else:
                raise UserError(
                    ("Unable to access the GitHub repository. Please try again later.")
                )

        default_branch = repo_response.json().get(
            "default_branch",
            "main"
        )

        _logger.info(
            "Default Branch: %s",
            default_branch
        )

        # --------------------------------------------------
        # Fetch SHA of Default Branch
        # --------------------------------------------------

        sha_response = requests.get(
            f"https://api.github.com/repos/"
            f"{repo_full_name}/git/ref/heads/{default_branch}",
            headers=headers,
            timeout=30,
        )

        _logger.info(
            "SHA Fetch Status: %s",
            sha_response.status_code
        )

        _logger.info(
            "SHA Fetch Response: %s",
            sha_response.text
        )

        if sha_response.status_code != 200:

            _logger.error(
                "GitHub SHA Fetch Failed. "
                "Status=%s Response=%s",
                sha_response.status_code,
                sha_response.text
            )

            raise UserError(
                ("Unable to retrieve repository branch information.")
            )

        sha = sha_response.json()["object"]["sha"]

        _logger.info(
            "Source SHA: %s",
            sha
        )

        # --------------------------------------------------
        # Create Branch
        # --------------------------------------------------

        payload = {
            "ref": f"refs/heads/{self.github_branch_name}",
            "sha": sha,
        }

        _logger.info(
            "Branch Creation Payload: %s",
            payload
        )

        branch_response = requests.post(
            f"https://api.github.com/repos/"
            f"{repo_full_name}/git/refs",
            headers=headers,
            json=payload,
            timeout=30,
        )

        _logger.info(
            "Branch Create Status: %s",
            branch_response.status_code
        )

        _logger.info(
            "Branch Create Response: %s",
            branch_response.text
        )

        if branch_response.status_code not in (200, 201):

            try:
                error_data = branch_response.json()
                github_message = error_data.get(
                    "message",
                    ""
                )
            except Exception:
                github_message = branch_response.text

            _logger.error(
                "GitHub Branch Creation Failed. "
                "Status=%s Response=%s",
                branch_response.status_code,
                branch_response.text
            )

            if branch_response.status_code == 401:
                raise UserError(
                    ("GitHub authentication failed. Please verify the configured token.")
                )

            elif branch_response.status_code == 403:
                raise UserError(
                    ("Permission denied. The configured GitHub token does not have sufficient access.")
                )

            elif branch_response.status_code == 404:
                raise UserError(
                    ("The GitHub repository could not be found.")
                )

            elif branch_response.status_code == 422:

                if "Reference already exists" in github_message:
                    raise UserError(
                        ("A branch with this name already exists.")
                    )

                raise UserError(
                    ("Invalid branch name or GitHub rejected the request.")
                )

            else:
                raise UserError(
                    ("Unable to create the GitHub branch. Please try again later.")
                )

        # --------------------------------------------------
        # Success
        # --------------------------------------------------

        branch_url = (
            f"https://github.com/{repo_full_name}"
            f"/tree/{self.github_branch_name}"
        )

        self.write({
            'github_branch_created': True,
            'github_branch_url': branch_url,
        })

        _logger.info(
            "Branch Created Successfully: %s",
            branch_url
        )

        _logger.info(
            "========== CREATE BRANCH END =========="
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Success'),
                'message': (
                    "Branch '%s' created successfully."
                ) % self.github_branch_name,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }