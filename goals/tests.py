from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import SavingsGoal, GoalContribution

User = get_user_model()


class SavingsGoalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )
        self.goal = SavingsGoal.objects.create(
            user=self.user,
            name="Emergency Fund",
            target_amount=5000,
            target_date=date.today() + timedelta(days=365),
        )

    def test_goal_creation(self):
        self.assertEqual(self.goal.user, self.user)
        self.assertEqual(self.goal.name, "Emergency Fund")
        self.assertEqual(self.goal.target_amount, 5000)
        self.assertEqual(self.goal.current_amount, 0)

    def test_progress_percentage(self):
        self.goal.current_amount = 2500
        self.goal.save()
        self.assertEqual(self.goal.get_progress_percentage(), 50.0)

    def test_add_contribution(self):
        self.goal.add_contribution(1000)
        self.assertEqual(self.goal.current_amount, 1000)
