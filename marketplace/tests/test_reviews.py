from django.test import TestCase
from django.urls import reverse

from marketplace.models import Order, OrderItem, Review
from marketplace.tests.helpers import make_customer, make_florist, make_product


class ReviewTests(TestCase):
    def setUp(self):
        self.customer = make_customer("review_buyer")
        self.florist = make_florist("review_florist")
        self.product = make_product(self.florist)
        self.order = self.make_order(self.customer, self.product, "delivered")

    def make_order(self, customer, product, fulfillment_status, *, quantity=1):
        order = Order.objects.create(customer=customer, total_amount=product.price * quantity)
        OrderItem.objects.create(
            order=order,
            product=product,
            florist=self.florist,
            product_name=product.name,
            unit_price=product.price,
            quantity=quantity,
            fulfillment_status=fulfillment_status,
        )
        return order

    def test_delivered_buyer_can_submit_review(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("add_review", args=[self.product.pk, self.order.pk]),
            {f"order-{self.order.pk}-rating": "5", f"order-{self.order.pk}-comment": "Beautiful and fresh."},
        )
        self.assertRedirects(response, f"{reverse('product_detail', args=[self.product.pk])}#reviews")
        review = Review.objects.get(product=self.product, customer=self.customer, order=self.order)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Beautiful and fresh.")

    def test_unverified_or_undelivered_buyer_cannot_submit_review(self):
        self.client.force_login(self.customer)
        pending_order = self.make_order(self.customer, self.product, "shipped")
        response = self.client.post(
            reverse("add_review", args=[self.product.pk, pending_order.pk]),
            {f"order-{pending_order.pk}-rating": "4", f"order-{pending_order.pk}-comment": ""},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.filter(order=pending_order).exists())

        other_customer = make_customer("not_the_buyer")
        foreign_order = self.make_order(other_customer, self.product, "delivered")
        response = self.client.post(
            reverse("add_review", args=[self.product.pk, foreign_order.pk]),
            {f"order-{foreign_order.pk}-rating": "4", f"order-{foreign_order.pk}-comment": ""},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.filter(order=foreign_order).exists())

    def test_average_rating_and_count_update_when_reviews_change(self):
        second_order = self.make_order(self.customer, self.product, "delivered")
        first_review = Review.objects.create(
            product=self.product, customer=self.customer, order=self.order, rating=5,
        )
        Review.objects.create(
            product=self.product, customer=self.customer, order=second_order, rating=3,
        )
        self.assertEqual(self.product.average_rating, 4.0)
        self.assertEqual(self.product.total_reviews, 2)

        first_review.delete()
        self.assertEqual(self.product.average_rating, 3.0)
        self.assertEqual(self.product.total_reviews, 1)

    def test_product_and_order_pages_show_review_actions_for_eligible_buyer(self):
        self.client.force_login(self.customer)
        product_response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertEqual(product_response.status_code, 200)
        self.assertContains(product_response, "Share your experience")
        self.assertContains(product_response, "Verified purchase")

        order_response = self.client.get(reverse("order_detail", args=[self.order.pk]))
        self.assertEqual(order_response.status_code, 200)
        self.assertContains(order_response, "Rate &amp; Review")

    def test_duplicate_review_is_rejected(self):
        self.client.force_login(self.customer)
        Review.objects.create(
            product=self.product, customer=self.customer, order=self.order, rating=4,
        )
        response = self.client.post(
            reverse("add_review", args=[self.product.pk, self.order.pk]),
            {f"order-{self.order.pk}-rating": "5", f"order-{self.order.pk}-comment": "Second review."},
        )
        self.assertRedirects(response, reverse("product_detail", args=[self.product.pk]))
        self.assertEqual(Review.objects.filter(product=self.product, customer=self.customer, order=self.order).count(), 1)
