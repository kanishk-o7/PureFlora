from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from marketplace.models import Cart, CartItem, CustomerAddress, DeliveryInfo, Order
from marketplace.tests.helpers import make_customer, make_florist, make_product


class CustomerAddressBookTests(TestCase):
    def setUp(self):
        self.customer = make_customer("address_customer")
        self.other_customer = make_customer("other_address_customer")
        florist = make_florist("address_florist")
        self.product = make_product(florist, stock=5, price="12.50")
        self.client.force_login(self.customer)

    def address(self, customer=None, **overrides):
        values = {
            "customer": customer or self.customer,
            "recipient_name": "Fern Buyer",
            "phone_number": "9876543210",
            "street_address": "1 Bloom Street",
            "city": "Pune",
            "state": "Maharashtra",
            "pincode": "411001",
            **overrides,
        }
        return CustomerAddress.objects.create(**values)

    def add_cart_product(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)

    def test_saving_default_address_unsets_previous_default(self):
        first = self.address(is_default=True)
        second = self.address(recipient_name="Second", is_default=True)
        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    def test_checkout_uses_selected_saved_address(self):
        saved = self.address(is_default=True)
        self.add_cart_product()
        response = self.client.post(reverse("checkout"), {"saved_address": str(saved.pk)})
        order = Order.objects.get(customer=self.customer)
        self.assertRedirects(response, reverse("order_success", args=[order.order_number]))
        delivery = DeliveryInfo.objects.get(order=order)
        self.assertEqual(delivery.full_name, saved.recipient_name)
        self.assertEqual(delivery.address, saved.street_address)
        self.assertEqual(delivery.state, saved.state)

    def test_checkout_can_save_new_address(self):
        self.add_cart_product()
        response = self.client.post(reverse("checkout"), {
            "saved_address": "new", "full_name": "Fern Buyer", "phone": "9876543210",
            "address": "1 Bloom Street", "city": "Pune", "state": "Maharashtra",
            "pin_code": "411001", "save_address": "on",
        })
        self.assertEqual(response.status_code, 302)
        saved = CustomerAddress.objects.get(customer=self.customer)
        self.assertEqual(saved.recipient_name, "Fern Buyer")
        self.assertEqual(saved.phone_number, "9876543210")
        self.assertEqual(saved.state, "Maharashtra")
        self.assertTrue(saved.is_default)

    def test_customer_cannot_view_or_delete_another_customers_address(self):
        theirs = self.address(customer=self.other_customer)
        self.assertEqual(self.client.get(reverse("addresses")).status_code, 200)
        response = self.client.post(reverse("address_delete", args=[theirs.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CustomerAddress.objects.filter(pk=theirs.pk).exists())

