from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SavingsGoalViewSet, GoalContributionViewSet, GoalMilestoneViewSet

router = DefaultRouter()
router.register(r"goals", SavingsGoalViewSet, basename="savings-goal")
router.register(r"contributions", GoalContributionViewSet, basename="goal-contribution")
router.register(r"milestones", GoalMilestoneViewSet, basename="goal-milestone")

urlpatterns = [
    path("", include(router.urls)),
]
