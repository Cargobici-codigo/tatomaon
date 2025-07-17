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
