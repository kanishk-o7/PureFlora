from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from marketplace.models import DeliveryInfo, Order, OrderItem
from marketplace.tests.helpers import make_customer, make_florist, make_product


class MultiVendorOrderTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.florist_one = make_florist("vendor_one")
        self.florist_two = make_florist("vendor_two")
        self.product_one = make_product(self.florist_one, "Rose Bundle", stock=8, price="30.00")
        self.product_two = make_product(self.florist_two, "Lily Bundle", stock=6, price="40.00")
        self.order = Order.objects.create(customer=self.customer, total_amount=Decimal("140.00"))
        DeliveryInfo.objects.create(order=self.order, full_name="Fern Buyer", phone="9876543210", address="1 Bloom St", city="Pune", pin_code="411001")
        self.item_one = OrderItem.objects.create(order=self.order, product=self.product_one, florist=self.florist_one, product_name=self.product_one.name, unit_price=self.product_one.price, quantity=2)
        self.item_two = OrderItem.objects.create(order=self.order, product=self.product_two, florist=self.florist_two, product_name=self.product_two.name, unit_price=self.product_two.price, quantity=2)

    def test_florist_sees_and_updates_only_their_own_order_item(self):
        self.client.force_login(self.florist_one)
        response = self.client.get(reverse("florist_orders"))
        self.assertContains(response, "Rose Bundle")
        self.assertNotContains(response, "Lily Bundle")

        response = self.client.post(reverse("florist_order_status", args=[self.item_one.pk]), {"fulfillment_status": "processing"})
        self.assertEqual(response.status_code, 302)
        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.item_one.fulfillment_status, "processing")
        self.assertEqual(self.item_two.fulfillment_status, "pending")
        self.assertEqual(self.order.order_status, "confirmed")

        forbidden_update = self.client.post(reverse("florist_order_status", args=[self.item_two.pk]), {"fulfillment_status": "shipped"})
        self.assertEqual(forbidden_update.status_code, 404)
        self.item_two.refresh_from_db()
        self.assertEqual(self.item_two.fulfillment_status, "pending")

    def test_cancelled_line_restores_stock_exactly_once(self):
        self.client.force_login(self.florist_one)
        url = reverse("florist_order_status", args=[self.item_one.pk])
        response = self.client.post(url, {"fulfillment_status": "cancelled"}, follow=True)
        self.assertContains(response, "Your fulfillment status was updated.")
        self.product_one.refresh_from_db()
        self.item_one.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.item_one.fulfillment_status, "cancelled")
        self.assertTrue(self.item_one.stock_restored)
        self.assertEqual(self.product_one.stock, 10)
        self.assertEqual(self.order.total_amount, Decimal("80.00"))
        self.assertEqual(self.order.order_status, "partially_fulfilled")

        self.client.post(url, {"fulfillment_status": "cancelled"})
        self.product_one.refresh_from_db()
        self.assertEqual(self.product_one.stock, 10)
