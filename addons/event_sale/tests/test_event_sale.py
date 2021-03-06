# -*- coding: utf-8 -*-

from odoo.tests import common


class EventSaleTest(common.TransactionCase):

    def setUp(self):
        super(EventSaleTest, self).setUp()

        self.EventRegistration = self.env['event.registration']

        # First I create an event product
        product = self.env['product.product'].create({
            'name': 'test_formation',
            'type': 'service',
            'event_ok': True,
        })

        # I create an event from the same type than my product
        event = self.env['event.event'].create({
            'name': 'test_event',
            'event_type_id': 1,
            'date_end': '2012-01-01 19:05:15',
            'date_begin': '2012-01-01 18:05:15'
        })

        ticket = self.env['event.event.ticket'].create({
            'name': 'test_ticket',
            'product_id': product.id,
            'event_id': event.id,
        })

        # I create a sales order
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'note': 'Invoice after delivery',
            'payment_term_id': self.env.ref('account.account_payment_term').id
        })

        # In the sales order I add some sales order lines. i choose event product
        self.env['sale.order.line'].create({
            'product_id': product.id,
            'price_unit': 190.50,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 8.0,
            'order_id': self.sale_order.id,
            'name': 'sales order line',
            'event_id': event.id,
            'event_ticket_id': ticket.id,
        })

        # In the event registration I add some attendee detail lines. i choose event product
        self.register_person = self.env['registration.editor'].create({
            'sale_order_id': self.sale_order.id,
            'event_registration_ids': [(0, 0, {
                'event_id': event.id,
                'name': 'Administrator',
                'email': 'abc@example.com'
            })],
        })

    def test_00_create_event_product(self):
        # I click apply to create attendees
        self.register_person.action_make_registration()
        # I check if a registration is created
        registrations = self.EventRegistration.search([('origin', '=', self.sale_order.name)])
        self.assertTrue(registrations, "The registration is not created.")

    def test_01_ticket_price_with_pricelist_and_tax(self):
        self.env.user.partner_id.country_id = False
        pricelist = self.env['product.pricelist'].search([], limit=1)

        tax = self.env['account.tax'].create({
            'name': "Tax 10",
            'amount': 10,
        })

        event_product = self.env['product.template'].create({
            'name': 'Event Product',
            'list_price': 10.0,
        })

        event_product.taxes_id = tax

        event = self.env['event.event'].create({
            'name': 'New Event',
            'date_begin': '2020-02-02',
            'date_end': '2020-04-04',
        })
        event_ticket = self.env['event.event.ticket'].create({
            'name': 'VIP',
            'price': 1000.0,
            'event_id': event.id,
            'product_id': event_product.product_variant_id.id,
        })

        pricelist.item_ids = self.env['product.pricelist.item'].create({
            'applied_on': "1_product",
            'base': "list_price",
            'compute_price': "fixed",
            'fixed_price': 6.0,
            'product_tmpl_id': event_product.id,
        })

        pricelist.discount_policy = 'without_discount'

        so = self.env['sale.order'].create({
            'partner_id': self.env.user.partner_id.id,
            'pricelist_id': pricelist.id,
        })
        sol = self.env['sale.order.line'].create({
            'name': event.name,
            'product_id': event_product.product_variant_id.id,
            'product_uom_qty': 1,
            'product_uom': event_product.uom_id.id,
            'price_unit': event_product.list_price,
            'order_id': so.id,
            'event_id': event.id,
            'event_ticket_id': event_ticket.id,
        })
        sol.product_id_change()
        self.assertEqual(so.amount_total, 660.0, "Ticket is $1000 but the event product is on a pricelist 10 -> 6. So, $600 + a 10% tax.")
