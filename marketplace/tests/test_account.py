from django.test import TestCase
from django.urls import reverse

from marketplace.tests.helpers import make_customer


class AccountPageTests(TestCase):
    def test_account_page_requires_sign_in(self):
        response = self.client.get(reverse("account"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('account')}")

    def test_customer_account_page_is_separate_from_order_history(self):
        customer = make_customer("account_customer")
        customer.email = "buyer@example.com"
        customer.save(update_fields=["email"])
        self.client.force_login(customer)

        response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ACCOUNT OVERVIEW")
        self.assertContains(response, "buyer@example.com")
        self.assertContains(response, reverse("order_history"))
