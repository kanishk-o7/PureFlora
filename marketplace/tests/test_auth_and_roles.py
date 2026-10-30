from django.test import TestCase, override_settings, RequestFactory
from django.urls import reverse
from marketplace.models import CustomUser, FloristProfile
from marketplace.tests.helpers import make_florist, make_product, make_customer
from marketplace.views import handler500


class AuthAndRoleTests(TestCase):
    def test_customer_and_florist_registration_assign_roles(self):
        password = "Fern-Cloud-742!"
        response = self.client.post(reverse("register"), {
            "username": "new_customer", "first_name": "Fern", "last_name": "Buyer",
            "email": "buyer@example.com", "role": "customer", "password1": password, "password2": password,
        })
        self.assertRedirects(response, reverse("home"))
        customer = CustomUser.objects.get(username="new_customer")
        self.assertEqual(customer.role, "customer")

        self.client.logout()
        response = self.client.post(reverse("register"), {
            "username": "new_florist", "first_name": "Fern", "last_name": "Grower",
            "email": "florist@example.com", "role": "florist", "password1": password, "password2": password,
        })
        self.assertRedirects(response, reverse("florist_dashboard"))
        florist = CustomUser.objects.get(username="new_florist")
        self.assertEqual(florist.role, "florist")
        self.assertTrue(FloristProfile.objects.filter(user=florist).exists())

    def test_customer_cannot_access_florist_dashboard_or_profile(self):
        customer = make_customer()
        self.client.force_login(customer)
        dashboard = self.client.get(reverse("florist_dashboard"))
        profile = self.client.get(reverse("florist_profile"))
        self.assertEqual(dashboard.status_code, 403)
        self.assertEqual(profile.status_code, 403)
        self.assertContains(dashboard, "ACCESS DENIED", status_code=403)

    def test_florist_cannot_edit_another_florists_product(self):
        first = make_florist("first_florist")
        second = make_florist("second_florist")
        product = make_product(first)
        self.client.force_login(second)
        response = self.client.get(reverse("product_edit", args=[product.pk]))
        self.assertEqual(response.status_code, 404)

    def test_florist_can_edit_only_their_own_shop_profile(self):
        florist = make_florist("profile_florist")
        other = make_florist("other_profile_florist")
        self.client.force_login(florist)
        response = self.client.post(reverse("florist_profile"), {
            "shop_name": "Petal House", "bio": "Seasonal flowers grown with care.",
            "phone_number": "9876543210", "address": "12 Garden Road",
        })
        self.assertRedirects(response, reverse("florist_profile"))
        florist.florist_profile.refresh_from_db()
        other.florist_profile.refresh_from_db()
        self.assertEqual(florist.florist_profile.shop_name, "Petal House")
        self.assertEqual(florist.florist_profile.phone_number, "9876543210")
        self.assertEqual(other.florist_profile.shop_name, "other_profile_florist Flowers")

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_custom_not_found_page_is_used(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "PAGE NOT FOUND", status_code=404)

    def test_custom_server_error_handler_renders_theme_page(self):
        request = RequestFactory().get("/")
        response = handler500(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"We'll be", response.content)
