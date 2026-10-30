from django.db import IntegrityError, transaction
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

    def post_review(self, order, rating, comment="Buyer review"):
        return self.client.post(
            reverse("add_review", args=[self.product.pk, order.pk]),
            {f"order-{order.pk}-rating": str(rating), f"order-{order.pk}-comment": comment},
        )

    def test_delivered_buyer_can_submit_one_product_review(self):
        self.client.force_login(self.customer)
        response = self.post_review(self.order, 4, "Beautiful and fresh.")
        self.assertRedirects(response, f"{reverse('product_detail', args=[self.product.pk])}#reviews")
        review = Review.objects.get(product=self.product, customer=self.customer)
        self.assertEqual(review.order, self.order)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "Beautiful and fresh.")

    def test_second_delivered_order_updates_instead_of_creating_duplicate(self):
        self.client.force_login(self.customer)
        self.post_review(self.order, 4, "First review")
        second_order = self.make_order(self.customer, self.product, "delivered")
        response = self.post_review(second_order, 3, "Updated from my second order")
        self.assertRedirects(response, f"{reverse('product_detail', args=[self.product.pk])}#reviews")
        self.assertEqual(Review.objects.filter(customer=self.customer, product=self.product).count(), 1)
        review = Review.objects.get(customer=self.customer, product=self.product)
        self.assertEqual(review.order, second_order)
        self.assertEqual(review.rating, 3)
        self.assertEqual(review.comment, "Updated from my second order")

    def test_database_constraint_blocks_duplicate_customer_product_reviews(self):
        Review.objects.create(product=self.product, customer=self.customer, order=self.order, rating=4)
        second_order = self.make_order(self.customer, self.product, "delivered")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(product=self.product, customer=self.customer, order=second_order, rating=5)
        self.assertEqual(Review.objects.filter(customer=self.customer, product=self.product).count(), 1)

    def test_review_can_be_edited_from_second_order_and_product_count_stays_one(self):
        self.client.force_login(self.customer)
        self.post_review(self.order, 4, "Original")
        second_order = self.make_order(self.customer, self.product, "delivered")
        before = Review.objects.get(customer=self.customer, product=self.product)
        old_updated_at = before.updated_at
        response = self.post_review(second_order, 5, "Edited to five stars")
        self.assertRedirects(response, f"{reverse('product_detail', args=[self.product.pk])}#reviews")
        before.refresh_from_db()
        self.assertEqual(before.rating, 5)
        self.assertEqual(before.comment, "Edited to five stars")
        self.assertEqual(before.order, second_order)
        self.assertGreaterEqual(before.updated_at, old_updated_at)
        self.assertEqual(Review.objects.filter(product=self.product).count(), 1)

    def test_average_rating_recalculates_after_review_edit(self):
        other_customer = make_customer("another_review_buyer")
        other_order = self.make_order(other_customer, self.product, "delivered")
        first_review = Review.objects.create(product=self.product, customer=self.customer, order=self.order, rating=4)
        Review.objects.create(product=self.product, customer=other_customer, order=other_order, rating=2)
        self.assertEqual(self.product.average_rating, 3.0)
        first_review.rating = 5
        first_review.save()
        self.assertEqual(self.product.average_rating, 3.5)
        self.assertEqual(self.product.total_reviews, 2)

    def test_unverified_or_undelivered_buyer_cannot_submit_review(self):
        self.client.force_login(self.customer)
        pending_order = self.make_order(self.customer, self.product, "shipped")
        response = self.post_review(pending_order, 4, "")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.filter(order=pending_order).exists())

        other_customer = make_customer("not_the_buyer")
        foreign_order = self.make_order(other_customer, self.product, "delivered")
        response = self.post_review(foreign_order, 4, "")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Review.objects.filter(order=foreign_order).exists())

    def test_product_and_order_pages_offer_write_or_edit_review(self):
        self.client.force_login(self.customer)
        product_response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertEqual(product_response.status_code, 200)
        self.assertContains(product_response, "Share your experience")
        self.assertContains(product_response, "Verified purchase")
        order_response = self.client.get(reverse("order_detail", args=[self.order.pk]))
        self.assertContains(order_response, "Write a Review")

        Review.objects.create(product=self.product, customer=self.customer, order=self.order, rating=4, comment="Fresh")
        product_response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertContains(product_response, "Edit your review")
        self.assertContains(product_response, "Update review")
        self.assertContains(product_response, 'value="4" selected')
        self.assertContains(product_response, "Fresh")

        order_response = self.client.get(reverse("order_detail", args=[self.order.pk]))
        self.assertContains(order_response, "Reviewed (4 Stars)")
        self.assertContains(order_response, "Edit Review")
        self.assertContains(order_response, "ORDER JOURNEY")
        self.assertContains(order_response, "Progress updates")

    def test_customer_tracking_entry_goes_to_my_orders(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("tracking"), {"order_number": self.order.order_number})
        self.assertRedirects(response, reverse("order_history"))
