# -*- coding: utf-8 -*-
#############################################################################
#
#    Rishvi Pvt Ltd
#
#    Copyright (C) 2025-TODAY Rishvi Pvt Ltd (<https://www.rishvi.com>)
#    Author: Rishvi Development Team (<https://www.rishvi.com>)
#
#    This software is proprietary and confidential.
#
#    Unauthorized copying, modification, distribution, or use of this
#    software, via any medium, is strictly prohibited without the prior
#    written permission of Rishvi Pvt Ltd.
#
#    This software is licensed, not sold. A valid commercial license
#    from Rishvi Pvt Ltd is required to use this software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NON-INFRINGEMENT.
#
#    For licensing information, contact: support@rishvi.com
#
##########################################################################
import base64
from io import BytesIO
from PIL import Image
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
# from odoo.addons.website.tools import get_video_embed_code

class FloorPlans(models.Model):
    _name = 'floor.plans'
    _description = "Floor Plans"
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char("Name", required=True)
    sequence = fields.Integer(default=10, index=True)
    image_1920 = fields.Image(required=True)
    building_id = fields.Many2one('building', "Building", index=True, ondelete='cascade')
    video_url = fields.Char('Video URL',
                            help='URL of a video for showcasing your property.')
    embed_code = fields.Char(compute="_compute_embed_code")
    can_image_1024_be_zoomed = fields.Boolean("Can Image 1024 be zoomed", compute='_compute_can_image_1024_be_zoomed', store=True)

    @api.depends('image_1920', 'image_1024')
    def _compute_can_image_1024_be_zoomed(self):
        for image in self:
            image.can_image_1024_be_zoomed = bool(
                image.image_1920
                and image.image_1024
                and self._is_image_size_above(image.image_1920, image.image_1024)
            )

    @api.depends('video_url')
    def _compute_embed_code(self):
        for image in self:
            image.embed_code = ""
            # image.embed_code = get_video_embed_code(image.video_url)

    @api.constrains('video_url')
    def _check_valid_video_url(self):
        for image in self:
            if image.video_url and not image.embed_code:
                raise ValidationError(_("Provided video URL for '%s' is not valid. Please enter a valid video URL.", image.name))

    def _is_image_size_above(self, original_image, resized_image):
        """Return True if original image is larger than resized image."""
        if not original_image or not resized_image:
            return False
        try:
            original_data = base64.b64decode(original_image)
            resized_data = base64.b64decode(resized_image)

            with Image.open(BytesIO(original_data)) as img_original, Image.open(BytesIO(resized_data)) as img_resized:
                return (
                        img_original.width > img_resized.width
                        or img_original.height > img_resized.height
                )
        except Exception:
            return False
