from decimal import Decimal
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Sale
from .services import ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY, bootstrap_roles, create_sale, void_sale


class SaleServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="testpass123")
        self.category = Category.objects.create(name="Cake")
        self.product = Product.objects.create(
            name="Chocolate Cake",
            category=self.category,
            sku="CK-001",
            price=Decimal("500.00"),
            cost=Decimal("300.00"),
            stock_quantity=10,
        )

    def test_sale_deducts_product_stock(self):
        sale = create_sale(
            cashier=self.user,
            payment_type="cash",
            payment_amount=Decimal("1000.00"),
            items=[{"product_id": self.product.id, "quantity": 2}],
            notes="Test sale",
        )

        self.product.refresh_from_db()

        self.assertEqual(sale.total_amount, Decimal("1000.00"))
        self.assertEqual(self.product.stock_quantity, 8)
        self.assertEqual(sale.items.count(), 1)

    def test_void_sale_restores_stock_and_records_voided_items(self):
        sale = create_sale(
            cashier=self.user,
            payment_type="cash",
            payment_amount=Decimal("1000.00"),
            items=[{"product_id": self.product.id, "quantity": 2}],
            notes="Test sale",
        )

        void_sale(sale=sale, approved_by=self.user, reason="Customer cancellation")

        sale.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(sale.status, Sale.STATUS_VOIDED)
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertEqual(sale.voided_items.count(), 1)
        self.assertEqual(sale.total_profit, Decimal("0.00"))

    def test_sale_rejects_when_payment_is_insufficient(self):
        with self.assertRaises(ValidationError):
            create_sale(
                cashier=self.user,
                payment_type="cash",
                payment_amount=Decimal("100.00"),
                items=[{"product_id": self.product.id, "quantity": 1}],
            )

    def test_sale_rejects_duplicate_lines_that_exceed_product_stock(self):
        self.product.stock_quantity = 3
        self.product.save(update_fields=["stock_quantity"])

        with self.assertRaises(ValidationError):
            create_sale(
                cashier=self.user,
                payment_type="cash",
                payment_amount=Decimal("2000.00"),
                items=[
                    {"product_id": self.product.id, "quantity": 2},
                    {"product_id": self.product.id, "quantity": 2},
                ],
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

class ProductCategoryWorkflowTests(TestCase):
    def setUp(self):
        bootstrap_roles()
        self.user = User.objects.create_user(username="inventory", password="testpass123")
        self.user.groups.add(Group.objects.get(name=ROLE_INVENTORY))
        self.client.force_login(self.user)

    def test_product_page_creates_category_visible_in_products_and_categories(self):
        response = self.client.post(
            reverse("product-list"),
            {
                "name": "Pastries",
                "description": "Freshly baked pastry items.",
            },
        )

        self.assertRedirects(response, reverse("product-list"))
        self.assertTrue(Category.objects.filter(name="Pastries").exists())

        product_response = self.client.get(reverse("product-list"))
        self.assertContains(product_response, "Pastries")

        category_response = self.client.get(reverse("category-list"))
        self.assertContains(category_response, "Pastries")


class EmployeeAccountTests(TestCase):
    def setUp(self):
        bootstrap_roles()
        self.admin = User.objects.create_user(username="manager", password="RolePass#123", is_staff=True)
        self.admin.groups.add(Group.objects.get(name=ROLE_ADMIN))
        self.client.force_login(self.admin)

    def test_employee_creation_hashes_password_and_assigns_role(self):
        response = self.client.post(
            reverse("employee-add"),
            {
                "username": "newcashier",
                "first_name": "New",
                "last_name": "Cashier",
                "email": "newcashier@example.com",
                "role": "Cashier",
                "is_active": "on",
                "password1": "OvenShift#789",
                "password2": "OvenShift#789",
            },
        )

        self.assertRedirects(response, reverse("employee-list"))
        employee = User.objects.get(username="newcashier")
        self.assertTrue(employee.is_active)
        self.assertNotEqual(employee.password, "OvenShift#789")
        self.assertTrue(employee.check_password("OvenShift#789"))
        self.assertTrue(employee.groups.filter(name=ROLE_CASHIER).exists())

    def test_admin_can_assign_roles_to_other_accounts(self):
        employee = User.objects.create_user(username="stocker", password="Stocker#123", is_staff=True)
        employee.groups.add(Group.objects.get(name=ROLE_CASHIER))

        response = self.client.post(
            reverse("employee-edit", args=[employee.pk]),
            {
                "username": "stocker",
                "first_name": "",
                "last_name": "",
                "email": "",
                "role": ROLE_INVENTORY,
                "is_active": "on",
            },
        )

        employee.refresh_from_db()
        self.assertRedirects(response, reverse("employee-list"))
        self.assertTrue(employee.is_active)
        self.assertTrue(employee.groups.filter(name=ROLE_INVENTORY).exists())

    def test_last_active_admin_cannot_be_deleted_archived_or_stripped(self):
        archive_response = self.client.post(reverse("employee-archive", args=[self.admin.pk]))
        self.assertRedirects(archive_response, reverse("employee-list"))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

        update_response = self.client.post(
            reverse("employee-edit", args=[self.admin.pk]),
            {
                "username": "manager",
                "first_name": "",
                "last_name": "",
                "email": "",
                "role": ROLE_CASHIER,
                "is_active": "on",
            },
        )
        self.assertEqual(update_response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.groups.filter(name=ROLE_ADMIN).exists())

        delete_response = self.client.post(reverse("employee-delete", args=[self.admin.pk]))
        self.assertRedirects(delete_response, reverse("employee-list"))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
