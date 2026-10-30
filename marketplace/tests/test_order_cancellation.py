from django.test import TestCase
from django.urls import reverse

from marketplace.models import Order, OrderItem
from marketplace.tests.helpers import make_customer, make_florist, make_product


class CustomerOrderCancellationTests(TestCase):
    def setUp(self):
        self.customer = make_customer("cancel_buyer")
        self.florist = make_florist("cancel_florist")
        self.product = make_product(self.florist, stock=1)
        self.order = Order.objects.create(
            customer=self.customer, total_amount=self.product.price * 2, payment_method="COD",
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            florist=self.florist,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=2,
            fulfillment_status="pending",
        )
        self.client.force_login(self.customer)

    def test_customer_can_cancel_before_shipping_and_stock_is_restored_once(self):
        response = self.client.post(reverse("cancel_order", args=[self.order.pk]))
        self.assertRedirects(response, reverse("order_detail", args=[self.order.pk]))
        self.item.refresh_from_db()
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.item.fulfillment_status, "cancelled")
        self.assertTrue(self.item.stock_restored)
        self.assertEqual(self.order.order_status, "cancelled")
        self.assertEqual(self.order.total_amount, 0)
        self.assertEqual(self.product.stock, 3)

        self.client.post(reverse("cancel_order", args=[self.order.pk]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_customer_cannot_cancel_after_shipping_starts(self):
        self.item.fulfillment_status = "shipped"
        self.item.save(update_fields=["fulfillment_status"])

        response = self.client.post(reverse("cancel_order", args=[self.order.pk]))

        self.assertRedirects(response, reverse("order_detail", args=[self.order.pk]))
        self.item.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.item.fulfillment_status, "shipped")
        self.assertEqual(self.product.stock, 1)

    def test_customer_cannot_cancel_another_customers_order(self):
        other_customer = make_customer("other_cancel_buyer")

        self.client.force_login(other_customer)
        response = self.client.post(reverse("cancel_order", args=[self.order.pk]))
        self.assertEqual(response.status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.fulfillment_status, "pending")
