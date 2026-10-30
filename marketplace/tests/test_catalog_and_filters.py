from django.test import TestCase
from django.urls import reverse
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
