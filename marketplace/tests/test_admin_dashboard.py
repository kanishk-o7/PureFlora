from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from marketplace.models import CustomUser, Order, OrderItem, Review
from marketplace.tests.helpers import make_customer, make_florist, make_product


class MarketAdminDashboardTests(TestCase):
    def setUp(self):
        self.customer = make_customer("admin_test_customer")
        self.florist = make_florist("admin_test_florist")
        self.product = make_product(self.florist, stock=12, price="20.00", name="Admin Test Rose")
        self.staff = CustomUser.objects.create_user(
            username="market_staff", password="staff-pass-123", role="customer", is_staff=True,
        )

    def make_order(self, status="delivered", quantity=2, price="20.00"):
        order = Order.objects.create(customer=self.customer, total_amount=Decimal(price) * quantity, order_status=status)
        OrderItem.objects.create(
            order=order, product=self.product, florist=self.florist,
            product_name=self.product.name, unit_price=Decimal(price),
            quantity=quantity, fulfillment_status=status,
        )
        return order

    def test_customer_and_florist_cannot_access_market_admin(self):
        for user in (self.customer, self.florist):
            self.client.force_login(user)
            response = self.client.get(reverse("admin_dashboard"))
            self.assertIn(response.status_code, (302, 403))

    def test_staff_sees_live_revenue_and_order_status_counts(self):
        self.make_order("delivered", quantity=2, price="20.00")
        self.make_order("pending", quantity=1, price="20.00")
        cancelled = self.make_order("cancelled", quantity=1, price="20.00")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["revenue"], Decimal("40.00"))
        self.assertEqual(response.context["total_orders"], 3)
        self.assertEqual(response.context["active_orders"], 1)
        self.assertEqual(response.context["delivered_orders"], 1)
        self.assertEqual(response.context["cancelled_orders"], 1)

    def test_staff_can_delete_customer_review(self):
        order = self.make_order("delivered")
        review = Review.objects.create(product=self.product, customer=self.customer, order=order, rating=4, comment="Nice flowers")
        self.client.force_login(self.staff)
        response = self.client.post(reverse("market_admin_delete_review", args=[review.pk]))
        self.assertRedirects(response, reverse("market_admin_reviews"))
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_staff_can_toggle_florist_status_and_hide_suspended_listings(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("market_admin_toggle_florist", args=[self.florist.pk]))
        self.assertRedirects(response, reverse("market_admin_florists"))
        self.florist.refresh_from_db()
        self.assertFalse(self.florist.is_active)
        shop = self.client.get(reverse("products"))
        self.assertNotContains(shop, self.product.name)

