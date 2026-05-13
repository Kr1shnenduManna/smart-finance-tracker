from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from decimal import Decimal
from .models import SavingsGoal, GoalContribution, GoalMilestone
from .serializers import (
    SavingsGoalSerializer,
    GoalContributionSerializer,
    GoalMilestoneSerializer,
)
from transactions.models import Transaction, Category


class SavingsGoalViewSet(viewsets.ModelViewSet):
    """Viewset for managing savings goals"""

    serializer_class = SavingsGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def add_contribution(self, request, pk=None):
        """Add contribution to goal — creates a transaction and updates account"""
        goal = self.get_object()
        amount = request.data.get("amount")
        source = request.data.get("source", "")
        notes = request.data.get("notes", "")

        if not amount:
            return Response(
                {"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        amount = Decimal(str(amount))

        # Use goal's linked account, or fall back to user's primary account
        from accounts.models import Account as UserAccount
        account = goal.account or UserAccount.objects.filter(
            user=request.user, is_active=True
        ).first()

        # Use or create a "Savings" category
        category = Category.objects.filter(
            name="Savings", category_type="expense"
        ).first()
        if not category:
            category = Category.objects.create(
                name="Savings", category_type="expense", is_system=True
            )

        # Always create a transaction (signal handles balance deduction automatically)
        transaction = None
        if account:
            transaction = Transaction.objects.create(
                user=request.user,
                account=account,
                category=category,
                transaction_type="expense",
                amount=amount,
                description=f"Savings contribution: {goal.name}",
                date=timezone.now().date(),
                notes=notes or f"Contribution to goal: {goal.name} ({source})"
                if source
                else f"Contribution to goal: {goal.name}",
            )

        contribution = GoalContribution.objects.create(
            goal=goal,
            amount=amount,
            contribution_date=timezone.now().date(),
            source=source,
            notes=notes,
        )

        goal.add_contribution(amount)

        return Response(
            {
                "message": "Contribution added",
                "contribution": GoalContributionSerializer(contribution).data,
                "goal": SavingsGoalSerializer(goal).data,
                "transaction_id": transaction.id if transaction else None,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark goal as completed"""
        goal = self.get_object()
        goal.is_active = False
        goal.completed_at = timezone.now().date()
        goal.save()

        return Response(
            {"message": "Goal marked as completed"}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get active goals"""
        goals = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def completed(self, request):
        """Get completed goals"""
        goals = self.get_queryset().filter(is_active=False, completed_at__isnull=False)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get goals summary"""
        goals = self.get_queryset()
        active_goals = goals.filter(is_active=True)

        total_active = active_goals.count()
        total_completed = goals.filter(
            is_active=False, completed_at__isnull=False
        ).count()

        total_target = sum(g.target_amount for g in active_goals)
        total_saved = sum(g.current_amount for g in active_goals)

        on_track_count = sum(1 for g in active_goals if g.is_on_track())

        return Response(
            {
                "total_active": total_active,
                "total_completed": total_completed,
                "total_target_amount": str(total_target),
                "total_saved_amount": str(total_saved),
                "on_track_count": on_track_count,
            }
        )

    @action(detail=False, methods=["get"])
    def priority(self, request):
        """Get goals sorted by priority"""
        priority = request.query_params.get("priority", None)
        goals = self.get_queryset().filter(is_active=True)

        if priority:
            goals = goals.filter(priority=priority)

        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)


class GoalContributionViewSet(viewsets.ModelViewSet):
    """Viewset for managing goal contributions"""

    serializer_class = GoalContributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GoalContribution.objects.filter(goal__user=self.request.user)


class GoalMilestoneViewSet(viewsets.ModelViewSet):
    """Viewset for managing goal milestones"""

    serializer_class = GoalMilestoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GoalMilestone.objects.filter(goal__user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        """Mark milestone as completed"""
        milestone = self.get_object()
        milestone.is_completed = True
        milestone.completed_date = timezone.now().date()
        milestone.save()

        return Response(
            {"message": "Milestone marked as completed"}, status=status.HTTP_200_OK
        )
