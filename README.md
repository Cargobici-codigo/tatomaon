# Tatoma Ruta Bridge

This repository contains an Odoo add-on that integrates delivery routes with sales, stock, POS and accounting workflows. It defines new models to manage shipping routes and delivery points and extends several core models to link them with logistics information. Two wizards help with manual planning and with rescheduling failed deliveries.

Install the module in Odoo as usual:

```bash
odoo -i tatoma_ruta_bridge
```

A basic usage example:

```python
ruta = env['ruta.envio'].create({'name': 'Ruta demo'})
puntos = env['ruta.punto'].search([('estado', '=', 'pendiente')])
ruta.asignar_puntos(puntos)
```

See the source files in `tatoma_ruta_bridge/` for the full implementation.

