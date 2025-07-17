from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    ruta_envio_id = fields.Many2one('ruta.envio')

    def action_confirm(self):
        res = super().action_confirm()
        for o in self:
            if not o.ruta_envio_id:
                r = self.env['ruta.envio'].create({
                    'name': f'Ruta {o.name}',
                    'fecha': fields.Date.context_today(self)
                })
                for p in o.picking_ids:
                    pt = self.env['ruta.punto'].create({
                        'direccion': p.partner_id.contact_address,
                        'latitud': p.partner_id.partner_latitude,
                        'longitud': p.partner_id.partner_longitude,
                        'tipo': 'entrega',
                        'peso_kg': sum(m.product_uom_qty for m in p.move_lines),
                        'ruta_id': r.id
                    })
                    p.ruta_punto_id = pt.id
                o.ruta_envio_id = r.id
        return res

