from odoo import models, fields

class ManualRoutingWizard(models.TransientModel):
    _name = 'manual.routing.wizard'
    _description = 'Planificación manual'

    name = fields.Char(required=True)
    fecha = fields.Date(default=fields.Date.context_today)
    punto_ids = fields.Many2many('ruta.punto', domain="[('estado','=','pendiente')]")

    def action_crear_ruta(self):
        if not self.punto_ids:
            raise models.ValidationError('Seleccione puntos')
        r = self.env['ruta.envio'].create({'name': self.name, 'fecha': self.fecha})
        r.asignar_puntos(self.punto_ids)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Creada',
                'message': f'Ruta {r.name}',
                'sticky': False,
            }
        }
