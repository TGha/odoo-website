from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    signup_confirm_email = fields.Boolean(readonly=False)
