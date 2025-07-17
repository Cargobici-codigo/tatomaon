from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    ruta_envio_id = fields.Many2one('ruta.envio')

    @api.model
    def create(cls, vals):
        rec = super().create(vals)
        r = rec.env['ruta.envio'].create({
            'name': f'Ruta POS {rec.name}',
            'fecha': fields.Date.context_today(rec),
        })
        rec.env['ruta.punto'].create({
            'direccion': rec.partner_id.contact_address,
            'latitud': rec.partner_id.partner_latitude,
            'longitud': rec.partner_id.partner_longitude,
            'tipo': 'entrega',
            'peso_kg': sum(l.qty for l in rec.lines),
            'ruta_id': r.id,
        })
        rec.ruta_envio_id = r.id
        return rec
