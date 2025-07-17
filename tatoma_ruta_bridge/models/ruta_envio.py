import logging
import random
from odoo import models, fields
from geopy.distance import geodesic

_logger = logging.getLogger(__name__)

class RutaEnvio(models.Model):
    _name = 'ruta.envio'
    _description = 'Ruta de Envío'
    _order = 'fecha desc, name asc'

    name = fields.Char(required=True)
    fecha = fields.Date(required=True, default=fields.Date.context_today)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('en_ruta', 'En ruta'),
        ('finalizada', 'Finalizada')
    ], default='borrador', tracking=True)
    transportista_id = fields.Many2one(
        'hr.employee',
        string="Repartidor",
        domain="[('user_id.share','=',False),('active','=',True)]",
        tracking=True,
    )
    pedidos_asignados = fields.One2many('ruta.punto', 'ruta_id', string="Puntos de Entrega")
    distancia_estim = fields.Float(string="Distancia estimada (km)", tracking=True)
    duracion_estim = fields.Float(string="Duración estimada (min)", tracking=True)
    mapa_html = fields.Html(string="Mapa")

    PESO_MAXIMO_KG = 380

    def asignar_puntos(self, puntos):
        for i, punto in enumerate(puntos, 1):
            punto.write({'ruta_id': self.id, 'orden': i, 'estado': 'en_proceso'})

    def _es_prioritario(self, punto):
        claves = ['HOTEL', 'PANADERIA', 'FORN']
        if punto.prioridad_manual:
            return True
        return any(k in (punto.direccion or '').upper() for k in claves)

    def _calcular_distancia_total(self, puntos):
        total = 0.0
        for a, b in zip(puntos, puntos[1:]):
            total += geodesic((a.latitud, a.longitud), (b.latitud, b.longitud)).km
        return round(total, 2)

    def agrupar_entregas_por_peso_y_horario(self):
        puntos = self.env['ruta.punto'].search([('ruta_id', '=', False), ('tipo', '=', 'entrega')])
        empleados = self.env['hr.employee'].search([('user_id.share','=',False),('active','=',True)])
        if not empleados:
            raise models.ValidationError("No hay transportistas disponibles")

        puntos_ord = sorted(puntos, key=lambda p: (not self._es_prioritario(p), p.hora_apertura or 0, -p.peso_kg))
        rutas = 0
        grupo = []
        peso = 0
        idx = 0
        for p in puntos_ord:
            if self._es_prioritario(p):
                emp = random.choice(empleados)
                ruta = self.create({
                    'name': f'Ruta Prioritaria {p.id}',
                    'fecha': fields.Date.context_today(self),
                    'transportista_id': emp.id,
                    'distancia_estim': 0,
                })
                ruta.asignar_puntos([p])
                rutas += 1
                continue
            if peso + p.peso_kg > self.PESO_MAXIMO_KG and grupo:
                emp = empleados[idx % len(empleados)]
                ruta = self.create({
                    'name': f'Ruta #{rutas+1}',
                    'fecha': fields.Date.context_today(self),
                    'transportista_id': emp.id,
                    'distancia_estim': self._calcular_distancia_total(grupo),
                })
                ruta.asignar_puntos(grupo)
                rutas += 1
                grupo = []
                peso = 0
                idx += 1
            grupo.append(p)
            peso += p.peso_kg
        if grupo:
            emp = empleados[idx % len(empleados)]
            ruta = self.create({
                'name': f'Ruta #{rutas+1}',
                'fecha': fields.Date.context_today(self),
                'transportista_id': emp.id,
                'distancia_estim': self._calcular_distancia_total(grupo),
            })
            ruta.asignar_puntos(grupo)
            rutas += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Planificación Completa',
                'message': f'Se han generado {rutas} rutas.',
                'sticky': False,
            }
        }
