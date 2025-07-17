# Tatoma Ruta Bridge

Tatoma Ruta Bridge integrates logistic routes and delivery points with key Odoo applications such as Sales, Inventory, Accounting and the Point of Sale. The module acts as a connector so that orders automatically create delivery routes that can then be managed or rescheduled.

## Prerequisites

Install the following Odoo modules before adding the bridge:

- `sale_management`
- `stock`
- `account`
- `delivery`
- `contacts`
- `point_of_sale`
- `hr`
- `tatoma_ruta_logistica`

## Installation

1. Copy the `tatoma_ruta_bridge` folder into your custom addons directory.
2. Add that directory to the `addons_path` option in your `odoo.conf`.
3. Restart the Odoo server so it detects the new module.
4. In the Apps menu (developer mode), click **Update Apps List**.
5. Search for **Tatoma Ruta Bridge** and click **Install**.

## Usage and verification

After installation a new **Routes** menu appears. Confirming a Sale Order or POS Order will automatically create a shipping route with the required delivery points. Open the route record to check the generated stops and use the provided wizards to plan or reprogram deliveries.
