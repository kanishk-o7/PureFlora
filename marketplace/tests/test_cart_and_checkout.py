from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from marketplace.models import Cart, CartItem, CustomUser, DeliveryInfo, Order, OrderItem
from marketplace.tests.helpers import make_customer, make_florist, make_product


class CartAndCheckoutTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.florist = make_florist("cart_florist")
        self.product = make_product(self.florist, stock=3, price="25.00")
        self.client.force_login(self.customer)

    def test_add_update_and_stock_boundary(self):
        add_url = reverse("add_to_cart", args=[self.product.pk])
        for _ in range(3):
            self.client.post(add_url)
        cart = Cart.objects.get(customer=self.customer)
        item = cart.items.get(product=self.product)
        self.assertEqual(item.quantity, 3)

        response = self.client.post(add_url)
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

        response = self.client.post(reverse("update_cart_item", args=[item.pk]), {"quantity": "2"})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.client.post(reverse("update_cart_item", args=[item.pk]), {"quantity": "4"})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

    def test_htmx_quantity_update_returns_updated_cart_and_totals(self):
        cart = Cart.objects.create(customer=self.customer)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(
            reverse("update_cart_item", args=[item.pk]),
            {"quantity": "2"}, HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cart-item-%s"' % item.pk)
        self.assertContains(response, 'id="cartTotal">&#8377;50.00')
        self.assertContains(response, 'id="nav-cart-count"')
        self.assertNotContains(response, "<html")
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

    def test_htmx_remove_updates_cart_row_summary_and_badge(self):
        cart = Cart.objects.create(customer=self.customer)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        response = self.client.post(
            reverse("remove_cart_item", args=[item.pk]), HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="cart-item-%s"' % item.pk)
        self.assertContains(response, 'id="nav-cart-count"')
        self.assertContains(response, 'hx-swap-oob="outerHTML">0</span>')
        self.assertContains(response, "Your bag is waiting to bloom.")
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_cod_checkout_creates_order_reduces_stock_and_clears_cart(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        cart_page = self.client.get(reverse("cart"))
        self.assertContains(cart_page, 'href="/checkout/"')
        self.assertContains(cart_page, "Continue to checkout")
        self.assertIn(b"&#8377;50.00", cart_page.content)
        response = self.client.post(reverse("checkout"), {
            "full_name": "Fern Buyer", "phone": "9876543210", "address": "1 Bloom Street",
            "city": "Pune", "pin_code": "411001",
        })
        order = Order.objects.get(customer=self.customer)
        self.assertRedirects(response, reverse("order_success", args=[order.order_number]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertFalse(cart.items.exists())
        self.assertEqual(order.total_amount, Decimal("50.00"))
        self.assertEqual(order.payment_method, "COD")
        self.assertTrue(DeliveryInfo.objects.filter(order=order, full_name="Fern Buyer").exists())
        self.assertEqual(OrderItem.objects.filter(order=order).get().quantity, 2)
        confirmation = self.client.get(response.url)
        self.assertContains(confirmation, "Order confirmed")
        self.assertContains(confirmation, order.order_number)
        self.assertContains(confirmation, "Track this order")
        self.assertContains(confirmation, "Cancel this order")
        tracking_page = self.client.get(reverse("order_detail", args=[order.pk]))
        self.assertContains(tracking_page, "waiting for the florist")
        self.assertContains(tracking_page, "1 Bloom Street")
        self.assertContains(tracking_page, "Cancel order")

    def test_checkout_rechecks_stock_and_leaves_cart_when_stock_is_insufficient(self):
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        # Simulate inventory changing after the item was placed in the cart.
        type(self.product).objects.filter(pk=self.product.pk).update(stock=1)
        response = self.client.post(reverse("checkout"), {
            "full_name": "Fern Buyer", "phone": "9876543210", "address": "1 Bloom Street",
            "city": "Pune", "pin_code": "411001",
        })
        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Order.objects.filter(customer=self.customer).exists())
        self.assertEqual(cart.items.get().quantity, 2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
