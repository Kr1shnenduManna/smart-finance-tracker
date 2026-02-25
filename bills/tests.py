from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from .models import Bill

User = get_user_model()


class BillModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )
        self.bill = Bill.objects.create(
            user=self.user,
            name="Electric Bill",
            amount=100,
            frequency="monthly",
            due_date=15,
            next_due_date=date.today(),
        )

    def test_bill_creation(self):
        self.assertEqual(self.bill.user, self.user)
        self.assertEqual(self.bill.name, "Electric Bill")
        self.assertEqual(self.bill.amount, 100)

    def test_bill_str(self):
        self.assertEqual(str(self.bill), "Electric Bill - 100 (monthly)")
