from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    _sql_constraints = [("email_uniq", "unique(email)", "Email already exists!")]
