from django.test import TestCase
from django.urls import reverse
import re
from marketplace.tests.helpers import make_florist, make_product


class CatalogFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        florist = make_florist("catalog_florist")
        for index in range(15):
            make_product(florist, name=f"Rose Sample {index}", stock=5, price=str(10 + index), category_name="Roses")
        make_product(florist, name="Rare Lily", stock=4, price="80.00", category_name="Lilies")

    def test_catalog_paginates_results(self):
        first_page = self.client.get(reverse("products"))
        second_page = self.client.get(reverse("products"), {"page": 2})
        self.assertEqual(first_page.context["page_obj"].paginator.count, 16)
        self.assertEqual(len(first_page.context["products"]), 12)
        self.assertEqual(len(second_page.context["products"]), 4)

    def test_search_and_category_filters(self):
        search_response = self.client.get(reverse("products"), {"q": "Rare"})
        self.assertEqual(search_response.context["result_count"], 1)
        self.assertContains(search_response, "Rare Lily")

        category_response = self.client.get(reverse("products"), {"category": "Roses"})
        self.assertEqual(category_response.context["result_count"], 15)
        self.assertNotContains(category_response, "Rare Lily")

    def test_price_stock_and_sort_filters(self):
        response = self.client.get(reverse("products"), {"max_price": "15", "in_stock": "1", "sort": "price-desc"})
        self.assertEqual(response.context["result_count"], 6)
        self.assertEqual(response.context["sort"], "price-desc")

    def test_htmx_catalog_request_returns_only_product_grid_partial(self):
        response = self.client.get(reverse("products"), {"q": "Rare"}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/partials/product_grid.html")
        self.assertContains(response, "Rare Lily")
        self.assertNotContains(response, "<html")
        self.assertNotContains(response, "Shop flowers</a>")

    def test_full_catalog_uses_htmx_base_with_csrf_header(self):
        response = self.client.get(reverse("products"))
        self.assertContains(response, "https://unpkg.com/htmx.org@1.9.12")
        rendered = response.content.decode()
        token_header = re.search(r'hx-headers=\'\{"X-CSRFToken": "([^\"]+)"\}\'', rendered)
        self.assertIsNotNone(token_header)
        self.assertTrue(token_header.group(1))
