##### Tatoma_ruta_bridge
```python
{
    "name": "Tatoma Ruta Bridge",
    "version": "1.2",
    "depends": [
        "sale_management",
        "stock",
        "account",
        "delivery",
        "contacts",
        "point_of_sale",
        "hr",
        "tatoma_ruta_logistica"
    ],
    "author": "Tatoma",
    "category": "Logistics",
    "description": "Módulo puente que integra rutas y puntos de entrega con ventas, stock, facturación, contactos, TPV, empleados y wizards de planificación.",
    "data": [
        "security/ir.model.access.csv",
        "views/menus.xml",
        "views/ruta_envio_buttons.xml",
        "views/sale_order_views.xml",
        "views/pos_order_views.xml",
        "views/stock_picking_views.xml",
        "views/account_move_views.xml",
        "views/ruta_punto_kanban_view.xml",
        "views/ruta_punto_map_selector.xml",
        "views/ruta_punto_tree_view.xml",
        "views/manual_routing_wizard_view.xml",
        "views/wizard_reprogramacion_incidencias_view.xml"
    ],
    "installable": True,
    "application": False
}
```

### tatoma_ruta_bridge/__init__.py
```python
from . import models
from . import wizards
```

---

## models/

### tatoma_ruta_bridge/models/__init__.py
```python
from . import ruta_envio
from . import ruta_punto
from . import sale_order
from . import pos_order
from . import stock_picking
from . import account_move
```

### tatoma_ruta_bridge/models/ruta_envio.py
```python
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
    transportista_id = fields.Many2one('hr.employee', string="Repartidor", domain="[('user_id.share','=',False),('active','=',True)]", tracking=True)
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
        rutas = 0; grupo = []; peso = 0; idx = 0
        for p in puntos_ord:
            if self._es_prioritario(p):
                emp = random.choice(empleados)
                ruta = self.create({'name': f'Ruta Prioritaria {p.id}', 'fecha': fields.Date.context_today(self), 'transportista_id': emp.id, 'distancia_estim': 0})
                ruta.asignar_puntos([p]); rutas += 1; continue
            if peso + p.peso_kg > self.PESO_MAXIMO_KG and grupo:
                emp = empleados[idx % len(empleados)]; ruta = self.create({'name': f'Ruta #{rutas+1}', 'fecha': fields.Date.context_today(self), 'transportista_id': emp.id, 'distancia_estim': self._calcular_distancia_total(grupo)})
                ruta.asignar_puntos(grupo); rutas+=1; grupo=[]; peso=0; idx+=1
            grupo.append(p); peso += p.peso_kg
        if grupo:
            emp = empleados[idx % len(empleados)]; ruta = self.create({'name': f'Ruta #{rutas+1}', 'fecha': fields.Date.context_today(self), 'transportista_id': emp.id, 'distancia_estim': self._calcular_distancia_total(grupo)})
            ruta.asignar_puntos(grupo); rutas+=1
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'Planificación Completa','message':f'Se han generado {rutas} rutas.','sticky':False}}
```

### tatoma_ruta_bridge/models/ruta_punto.py
```python
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
    tipo = fields.Selection([('entrega','Entrega'),('recogida','Recogida')], default='entrega')
    estado = fields.Selection([('pendiente','Pendiente'),('en_proceso','En proceso'),('entregado','Entregado'),('fallido','Fallido'),('reprogramado','Reprogramado')], default='pendiente', tracking=True)
    peso_kg = fields.Float()
    hora_apertura = fields.Float(help="8.5 = 08:30")
    hora_cierre = fields.Float(help="17.0 = 17:00")
    prioridad_manual = fields.Boolean()
    orden = fields.Integer()
    ruta_id = fields.Many2one('ruta.envio', ondelete='cascade')
    incidencia = fields.Text(tracking=True)
    reintento_fecha = fields.Datetime()

    @api.constrains('hora_apertura','hora_cierre')
    def _check_horario(self):
        for r in self:
            if r.hora_cierre <= r.hora_apertura:
                raise models.ValidationError("Hora cierre debe ser > apertura.")
    @api.constrains('latitud','longitud')
    def _check_geo(self):
        for r in self:
            if not (-90<=r.latitud<=90 and -180<=r.longitud<=180):
                raise models.ValidationError("Latitud/Longitud fuera de rango.")
```

### tatoma_ruta_bridge/models/sale_order.py
```python
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    ruta_envio_id = fields.Many2one('ruta.envio')
    def action_confirm(self):
        res = super().action_confirm()
        for o in self:
            if not o.ruta_envio_id:
                r = self.env['ruta.envio'].create({'name':f'Ruta {o.name}','fecha':fields.Date.context_today(self)})
                for p in o.picking_ids:
                    pt = self.env['ruta.punto'].create({'direccion':p.partner_id.contact_address,'latitud':p.partner_id.partner_latitude,'longitud':p.partner_id.partner_longitude,'tipo':'entrega','peso_kg':sum(m.product_uom_qty for m in p.move_lines),'ruta_id':r.id})
                    p.ruta_punto_id = pt.id
                o.ruta_envio_id = r.id
        return res
```

### tatoma_ruta_bridge/models/pos_order.py
```python
from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit='pos.order'
    ruta_envio_id=fields.Many2one('ruta.envio')
    @api.model
def create(cls,vals):
        rec=super().create(vals)
        r = rec.env['ruta.envio'].create({'name':f'Ruta POS {rec.name}','fecha':fields.Date.context_today(rec)})
        pr=rec.env['ruta.punto'].create({'direccion':rec.partner_id.contact_address,'latitud':rec.partner_id.partner_latitude,'longitud':rec.partner_id.partner_longitude,'tipo':'entrega','peso_kg':sum(l.qty for l in rec.lines),'ruta_id':r.id})
        rec.ruta_envio_id=r.id
        return rec
```

### tatoma_ruta_bridge/models/stock_picking.py
```python
from odoo import models, fields, api
class StockPicking(models.Model):
    _inherit='stock.picking'
    ruta_punto_id=fields.Many2one('ruta.punto')
    def button_validate(self):
        res=super().button_validate()
        for rec in self:
            if rec.ruta_punto_id:
                rec.ruta_punto_id.estado='entregado'
        return res
```

### tatoma_ruta_bridge/models/account_move.py
```python
from odoo import models, fields
class AccountMove(models.Model):
    _inherit='account.move'
    ruta_envio_id=fields.Many2one('ruta.envio')
```

---

## wizards/

### tatoma_ruta_bridge/wizards/__init__.py
```python
from . import manual_routing_wizard, wizard_reprogramacion_incidencias
```

### tatoma_ruta_bridge/wizards/manual_routing_wizard.py
```python
from odoo import models, fields
class ManualRoutingWizard(models.TransientModel):
    _name='manual.routing.wizard'
    _description='Planificación manual'
    name=fields.Char(required=True)
    fecha=fields.Date(default=fields.Date.context_today)
    punto_ids=fields.Many2many('ruta.punto',domain="[('estado','=','pendiente')]" )
    def action_crear_ruta(self):
        if not self.punto_ids: raise models.ValidationError('Seleccione puntos')
        r=self.env['ruta.envio'].create({'name':self.name,'fecha':self.fecha})
        r.asignar_puntos(self.punto_ids)
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'Creada','message':f'Ruta {r.name}', 'sticky':False}}
```

### tatoma_ruta_bridge/wizards/wizard_reprogramacion_incidencias.py
```python
from odoo import models, fields, api
from datetime import timedelta
class WizardReprogramacionIncidencias(models.TransientModel):
    _name='wizard.reprogramacion.incidencias'
    fecha_reintento=fields.Datetime(default=lambda self: fields.Datetime.now()+timedelta(days=1))
    transportista_id=fields.Many2one('hr.employee',domain="[('user_id.share','=',False),('active','=',True)]" )
    punto_ids=fields.Many2many('ruta.punto',domain="[('estado','=','fallido')]"
    )
    @api.model
default_get(self,fields):
        res=super().default_get(fields)
        res['punto_ids']=self.env.context.get('active_ids') or self.env['ruta.punto'].search([('estado','=','fallido')]).ids
        return res
    def action_reprogramar(self):
        nr=self.env['ruta.envio'].create({'name':f'Reprog {fields.Datetime.to_string(self.fecha_reintento)}','fecha':self.fecha_reintento,'transportista_id':self.transportista_id.id if self.transportista_id else False})
        for i,p in enumerate(self.punto_ids,1): p.write({'ruta_id':nr.id,'estado':'reprogramado','reintento_fecha':self.fecha_reintento,'orden':i,'incidencia':(p.incidencia or '')+' | Reprog'})
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'Reprog','message':f'{len(self.punto_ids)} puntos'}}
```

## License

This project is released under the GNU General Public License v3.0.
See the [LICENSE](LICENSE) file for the full license text.
