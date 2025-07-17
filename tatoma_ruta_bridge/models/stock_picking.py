from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ruta_punto_id = fields.Many2one('ruta.punto')

    def button_validate(self):
        res = super().button_validate()
        for rec in self:
            if rec.ruta_punto_id:
                rec.ruta_punto_id.estado = 'entregado'
        return res
