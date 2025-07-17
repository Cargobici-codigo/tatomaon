from odoo import models, fields, api
from datetime import timedelta

class WizardReprogramacionIncidencias(models.TransientModel):
    _name = 'wizard.reprogramacion.incidencias'
    _description = 'Reprogramar puntos con incidencia'

    fecha_reintento = fields.Datetime(
        string="Fecha reintento",
        default=lambda self: fields.Datetime.now() + timedelta(days=1)
    )
    transportista_id = fields.Many2one(
        'res.users', string="Reasignar a Repartidor",
        domain="[('share','=',False)]"
    )
    punto_ids = fields.Many2many(
        'ruta.punto', string="Puntos con incidencia"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        res['punto_ids'] = active_ids or self.env['ruta.punto'].search([('estado', '=', 'fallido')]).ids
        return res

    def action_reprogramar(self):
        nombre_ruta = f"Reprogramación {fields.Datetime.to_string(fields.Datetime.context_timestamp(self, self.fecha_reintento))}"
        nueva_ruta = self.env['ruta.envio'].create({
            'name': nombre_ruta,
            'fecha': self.fecha_reintento,
            'transportista_id': self.transportista_id.id if self.transportista_id else False
        })
        for orden, punto in enumerate(self.punto_ids, 1):
            punto.write({
                'ruta_id': nueva_ruta.id,
                'estado': 'reprogramado',
                'reintento_fecha': self.fecha_reintento,
                'orden': orden,
                'incidencia': (punto.incidencia or '') + ' | Reprogramado desde wizard'
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Puntos reprogramados',
                'message': f'Se reprogramaron {len(self.punto_ids)} puntos en una nueva ruta.',
                'sticky': False,
            }
        }
