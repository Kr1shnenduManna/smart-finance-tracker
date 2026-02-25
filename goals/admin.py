from django.contrib import admin
from .models import SavingsGoal, GoalContribution, GoalMilestone


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "category",
        "current_amount",
        "target_amount",
        "target_date",
        "is_active",
    ]
    list_filter = ["category", "priority", "is_active", "created_at"]
    search_fields = ["name", "user__email", "description"]
    readonly_fields = ["start_date", "completed_at", "created_at", "updated_at"]


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ["goal", "amount", "contribution_date", "source"]
    list_filter = ["contribution_date", "goal"]
    search_fields = ["goal__name", "source"]


@admin.register(GoalMilestone)
class GoalMilestoneAdmin(admin.ModelAdmin):
    list_display = ["goal", "name", "target_amount", "target_date", "is_completed"]
    list_filter = ["is_completed", "target_date"]
    search_fields = ["goal__name", "name"]
