import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class RutaPunto(models.Model):
    _name = 'ruta.punto'
    _description = 'Punto de Entrega'
    _order = 'orden ASC, prioridad_manual DESC'

    direccion = fields.Char(required=True)
    latitud = fields.Float(required=True)
    longitud = fields.Float(required=True)
    tipo = fields.Selection([
        ('entrega', 'Entrega'),
        ('recogida', 'Recogida')
    ], default='entrega')
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('entregado', 'Entregado'),
        ('fallido', 'Fallido'),
        ('reprogramado', 'Reprogramado')
    ], default='pendiente', tracking=True)
    peso_kg = fields.Float()
    hora_apertura = fields.Float(help="8.5 = 08:30")
    hora_cierre = fields.Float(help="17.0 = 17:00")
    prioridad_manual = fields.Boolean()
    orden = fields.Integer()
    ruta_id = fields.Many2one('ruta.envio', ondelete='cascade')
    incidencia = fields.Text(tracking=True)
    reintento_fecha = fields.Datetime()

    @api.constrains('hora_apertura', 'hora_cierre')
    def _check_horario(self):
        for r in self:
            if r.hora_cierre <= r.hora_apertura:
                raise models.ValidationError("Hora cierre debe ser > apertura.")

    @api.constrains('latitud', 'longitud')
    def _check_geo(self):
        for r in self:
            if not (-90 <= r.latitud <= 90 and -180 <= r.longitud <= 180):
                raise models.ValidationError("Latitud/Longitud fuera de rango.")
