from odoo import models, fields, api
from datetime import timedelta

class WizardReprogramacionIncidencias(models.TransientModel):
    _name = 'wizard.reprogramacion.incidencias'

    fecha_reintento = fields.Datetime(default=lambda self: fields.Datetime.now() + timedelta(days=1))
    transportista_id = fields.Many2one('hr.employee', domain="[('user_id.share','=',False),('active','=',True)]")
    punto_ids = fields.Many2many('ruta.punto', domain="[('estado','=','fallido')]")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['punto_ids'] = self.env.context.get('active_ids') or self.env['ruta.punto'].search([('estado','=','fallido')]).ids
        return res

    def action_reprogramar(self):
        nr = self.env['ruta.envio'].create({
            'name': f'Reprog {fields.Datetime.to_string(self.fecha_reintento)}',
            'fecha': self.fecha_reintento,
            'transportista_id': self.transportista_id.id if self.transportista_id else False
        })
        for i, p in enumerate(self.punto_ids, 1):
            p.write({
                'ruta_id': nr.id,
                'estado': 'reprogramado',
                'reintento_fecha': self.fecha_reintento,
                'orden': i,
                'incidencia': (p.incidencia or '') + ' | Reprog'
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Reprog', 'message': f'{len(self.punto_ids)} puntos'}
        }

