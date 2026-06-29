from odoo import fields, models,_
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)



class ProjectProject(models.Model):
    _inherit = 'project.project'   

    github_create_repo = fields.Boolean(
        string="Create Repository in GitHub"
    )

    github_repo_name = fields.Char(
        string="Repository Name"
    )

    github_visibility = fields.Selection(
        [
            ('public', 'Public'),
            ('private', 'Private')
        ],
        string="Visibility",
        default='private'
    )   

    github_description = fields.Text(
        string="Repository Description"
    )

    github_repo_id = fields.Many2one(
        'github.repository',
        string='GitHub Repository'
    )

    github_repo_url = fields.Char(
    string="Repository URL",
    readonly=True
)
    github_repo_created = fields.Boolean(
    string="Repository Created",
    default=False
)
    github_invitation_sent = fields.Boolean(
    string="GitHub Invitation Sent",
    default=False,store=True
)
   

    def _check_github_permission(self):
        if not self.env.user.github_access:
            raise UserError((
                "You are not authorized to perform this action.\n\n"
                "Please contact your administrator to obtain GitHub access."
            ))


    def action_create_github_repo(self):
        self.ensure_one()
        self._check_github_permission()

        if not self.github_repo_name:
            raise UserError("Please enter a Repository Name.")

        token = self.env['ir.config_parameter'].sudo().get_param(
        'github_token'
        )

        if not token:
            raise UserError(
                "GitHub token is not configured in System Parameters."
            )
        

        url = "https://api.github.com/user/repos"

        headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

        payload = {
            "name": self.github_repo_name,
            "description": self.github_description or "",
            "private": self.github_visibility == "private",
            "auto_init": True,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )
        _logger.info("222222222222222222222222222222222222222222222222222222222")

        _logger.info("GitHub Status Code: %s", response.status_code)
        _logger.info("GitHub Response: %s", response.text)


        if response.status_code not in (200, 201):

            try:
                error_data = response.json()
                github_message = error_data.get("message", "")
            except Exception:
                github_message = response.text

            _logger.error(
                "GitHub Repository Creation Failed. "
                "Status=%s Response=%s",
                response.status_code,
                response.text
            )

            if response.status_code == 401:
                raise UserError(
                    ("GitHub authentication failed. Please verify the configured token.")
                )

            elif response.status_code == 403:
                raise UserError(
                    ("Permission denied. The configured GitHub token does not have sufficient access.")
                )

            elif response.status_code == 404:
                raise UserError(
                    ("GitHub repository service could not be reached. Please verify the configuration.")
                )

            elif response.status_code == 422:
                
                # if "already exists" in github_message.lower():
                raise UserError(
                        ("A repository with this name already exists in your GitHub account.")
                    )

                # raise UserError(
                #     ("Invalid repository data. Please verify the entered values.")
                # )

            elif response.status_code == 415:
                raise UserError(
                    ("GitHub API configuration error. Please contact your administrator.")
                )

            else:
                raise UserError(
                    ("Unable to create the repository. Please try again later.")
                )

        repo_data = response.json()
        repo = self.env['github.repository'].create({
            'name': repo_data.get('name'),
            'repo_url': repo_data.get('html_url'),
            'full_name': repo_data.get('full_name'),
        })

        self.write({
            'github_repo_id': repo.id,
            'github_repo_url': repo_data.get('html_url'),
            'github_repo_created': True,
        })

       
        return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': 'Success',
            'message': f"Repository '{self.github_repo_name}' created successfully.",
            'type': 'success',
            'sticky': False,
            'next': {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        }
}
    



        

    def action_send_invitation(self):
        self.ensure_one()
        self._check_github_permission()

        github_token = self.env['ir.config_parameter'].sudo().get_param(
            'github_token'
        )

        if not github_token:
            raise UserError(_("GitHub token is not configured."))

        if not self.github_repo_id:
            raise UserError(
                _("No GitHub repository is linked to this project.")
            )

    
        owner = self.env['ir.config_parameter'].sudo().get_param(
            'github_owner'
        )

        if not owner:
            raise UserError(
                _("GitHub owner is not configured.")
            )

        repo = self.github_repo_id.name

        if not repo:
            raise UserError(
                _("Repository name is missing.")
            )

        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
        }

        _logger.info("========== SEND INVITATION START ==========")
        _logger.info("Repository Owner: %s", owner)
        _logger.info("Repository Name: %s", repo)

        # Debug partner hierarchy
        _logger.info("Project Partners: %s", self.partner_ids.ids)

        for partner in self.partner_ids:
            _logger.info(
                "Partner: %s (ID: %s)",
                partner.name,
                partner.id
            )

            _logger.info(
                "Related Users: %s",
                partner.user_ids.mapped("name")
            )

            for user in partner.user_ids:
                _logger.info(
                    "User: %s",
                    user.name
                )

                _logger.info(
                    "Employee: %s",
                    user.employee_id.name
                    if user.employee_id else False
                )

                _logger.info(
                    "GitHub Username: %s",
                    user.employee_id.github_user_name
                    if user.employee_id else False
                )

        github_user_names = self.partner_ids.mapped(
            "user_ids.employee_id.github_user_name"
        )

        github_user_names = [
            username.strip()
            for username in github_user_names
            if username
        ]

        _logger.info(
            "Final GitHub Usernames Found: %s",
            github_user_names
        )

        invited_users = []
        failed_users = []

        for username in github_user_names:

            url = (
                f"https://api.github.com/repos/"
                f"{owner}/{repo}/collaborators/{username}"
            )

            payload = {
                "permission": "push"
            }

            _logger.info("--------------------------------")
            _logger.info(
                "Sending invitation to: %s",
                username
            )
            _logger.info(
                "Request URL: %s",
                url
            )

            try:
                response = requests.put(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=20,
                )

                _logger.info(
                    "Status Code: %s",
                    response.status_code
                )

                _logger.info(
                    "Response Body: %s",
                    response.text
                )

                if response.status_code in (201, 204):

                    invited_users.append(username)

                    _logger.info(
                        "Invitation successful for %s",
                        username
                    )

                else:

                    failed_users.append(
                        f"{username}: "
                        f"{response.status_code}"
                    )

                    _logger.error(
                        "Invitation failed for %s. "
                        "Status=%s Response=%s",
                        username,
                        response.status_code,
                        response.text
                    )

            except Exception as e:

                _logger.exception(
                    "Exception while inviting %s",
                    username
                )

                failed_users.append(
                    f"{username}: {str(e)}"
                )

        _logger.info(
            "Invited Users: %s",
            invited_users
        )

        _logger.info(
            "Failed Users: %s",
            failed_users
        )

        _logger.info(
            "========== SEND INVITATION END =========="
        )

        message = []

        if invited_users:
            message.append(
                "Invited: " + ", ".join(invited_users)
            )

        if failed_users:
            message.append(
                "Failed: " + "; ".join(failed_users)
            )

        if not message:
            message.append(
                "No valid GitHub usernames found."
            )

        if invited_users:
           self.write({
        'github_invitation_sent': True
    })
        _logger.info(
        "Current value after write: %s",
        self.github_invitation_sent
    )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "GitHub Invitation",
                "message": "\n".join(message),
                "type": (
                    "warning"
                    if failed_users
                    else "success"
                ),
                "sticky": False,
        'next': {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            }
        }
     