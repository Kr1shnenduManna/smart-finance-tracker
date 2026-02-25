from rest_framework import serializers
from decimal import Decimal
from .models import SavingsGoal, GoalContribution, GoalMilestone


class GoalContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalContribution
        fields = ["id", "amount", "contribution_date", "source", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class GoalMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalMilestone
        fields = [
            "id",
            "name",
            "target_amount",
            "target_date",
            "is_completed",
            "completed_date",
        ]
        read_only_fields = ["id", "completed_date"]


class SavingsGoalSerializer(serializers.ModelSerializer):
    contributions = GoalContributionSerializer(many=True, read_only=True)
    milestones = GoalMilestoneSerializer(many=True, read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    suggested_monthly_savings = serializers.SerializerMethodField()
    is_on_track = serializers.SerializerMethodField()
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "description",
            "category",
            "priority",
            "target_amount",
            "current_amount",
            "start_date",
            "target_date",
            "is_active",
            "account",
            "account_name",
            "contributions",
            "milestones",
            "progress_percentage",
            "remaining_amount",
            "days_remaining",
            "suggested_monthly_savings",
            "is_on_track",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "start_date",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def get_progress_percentage(self, obj):
        return obj.get_progress_percentage()

    def get_remaining_amount(self, obj):
        return str(obj.get_remaining_amount())

    def get_days_remaining(self, obj):
        return obj.get_days_remaining()

    def get_suggested_monthly_savings(self, obj):
        return str(obj.get_suggested_monthly_savings())

    def get_is_on_track(self, obj):
        try:
            return obj.is_on_track()
        except (ZeroDivisionError, Exception):
            return False
