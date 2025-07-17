from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    ruta_envio_id = fields.Many2one('ruta.envio')
