from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    partner_ids = fields.Many2many('res.partner', string="Default Followers in Tasks")

    @api.model_create_multi
    def create(self, vals_list):
        # Retrieve partner IDs from ir.config_parameter
        partner_ids_str = self.env['ir.config_parameter'].sudo().get_param(
            'rishvi_default_follower_project.default_partner_ids', False)
        if partner_ids_str:
            partner_ids = [int(pid) for pid in partner_ids_str.split(',')]
            # Add default followers to each project in vals_list
            for vals in vals_list:
                if 'message_follower_ids' not in vals:
                    vals['message_follower_ids'] = []
                vals['message_follower_ids'].extend([
                    (0, 0, {'res_model': 'project.project', 'partner_id': pid})
                    for pid in partner_ids
                ])

        projects = super(ProjectProject, self.sudo()).create(vals_list)
        return projects


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model_create_multi
    def create(self, vals_list):
        print("\n vals_list======", vals_list)
        for vals in vals_list:
            print("\n vals======", vals)
            if 'project_id' in vals:
                project = self.env['project.project'].browse(vals['project_id'])
                if project.partner_ids:
                    if 'message_follower_ids' not in vals:
                        vals['message_follower_ids'] = []
                    vals['message_follower_ids'].extend([
                        (0, 0, {'res_model': 'project.task', 'partner_id': pid.id})
                        for pid in project.partner_ids
                    ])
        tasks = super(ProjectTask, self.sudo()).create(vals_list)
        return tasks

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.partner_ids:
            existing_follower_ids = set(self.message_follower_ids.mapped('partner_id').ids)
            new_follower_ids = set(self.project_id.partner_ids.ids) - existing_follower_ids
            self.message_follower_ids = [
                (4, pid) for pid in new_follower_ids
            ]