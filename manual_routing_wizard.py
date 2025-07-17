from odoo import models, fields

class ManualRoutingWizard(models.TransientModel):
    _name = 'manual.routing.wizard'
    _description = 'Planificación manual de rutas'

    name = fields.Char(string="Nombre de la ruta", required=True)
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today)
    punto_ids = fields.Many2many('ruta.punto', string="Puntos seleccionados")

    def action_crear_ruta(self):
        if not self.punto_ids:
            raise models.ValidationError('Debe seleccionar al menos un punto.')

        ruta = self.env['ruta.envio'].create({
            'name': self.name or f'Ruta manual {fields.Date.context_today(self)}',
            'fecha': self.fecha,
        })
        ruta.asignar_puntos(self.punto_ids)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ruta creada',
                'message': f'Se ha creado la ruta {ruta.name} con {len(self.punto_ids)} puntos.',
                'sticky': False,
            }
        }
