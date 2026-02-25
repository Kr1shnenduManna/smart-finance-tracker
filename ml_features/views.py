from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .ml_utils import (
    get_categorizer,
    get_budget_predictor,
    retrain_categorizer_if_ready,
    retrain_budget_predictor_if_ready,
)
from .models import MLModel, PredictionLog


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def predict_category(request):
    """
    Predict the category for a transaction description.
    POST body: { "description": "Uber ride to airport" }
    """
    description = request.data.get("description", "").strip()
    if not description:
        return Response(
            {"error": "description is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    categorizer = get_categorizer()
    if not categorizer.is_trained:
        return Response(
            {
                "error": "Categorizer model has not been trained yet. "
                "Run `python manage.py train_models --model categorizer` first."
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    predicted_category, confidence = categorizer.predict(description)

    # Log the prediction
    try:
        ml_model = MLModel.objects.filter(
            model_type="categorization", is_active=True
        ).first()
        if ml_model:
            PredictionLog.objects.create(
                user=request.user,
                model=ml_model,
                input_data={"description": description},
                prediction={"category": predicted_category},
                confidence=confidence,
            )
    except Exception:
        pass  # logging should never break the response

    return Response(
        {
            "description": description,
            "predicted_category": predicted_category,
            "confidence": round(float(confidence), 4),
        }
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def predict_budget(request):
    """
    Predict the budget amount for a category.
    POST body: { "category_id": 3, "month": 6 }
    """
    category_id = request.data.get("category_id")
    month = request.data.get("month")

    if not category_id or not month:
        return Response(
            {"error": "category_id and month are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    predictor = get_budget_predictor()
    if not predictor.is_trained:
        return Response(
            {
                "error": "Budget predictor model has not been trained yet. "
                "Run `python manage.py train_models --model budget` first."
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Build a simple feature vector: [month, category_id, 0 (hist_avg placeholder), 0, 0]
    features = [int(month), int(category_id), 0, 0, 0]
    predicted_amount = predictor.predict(features)

    return Response(
        {
            "category_id": category_id,
            "month": month,
            "predicted_amount": round(float(predicted_amount), 2)
            if predicted_amount
            else None,
        }
    )


@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def train_models(request):
    """
    Trigger model retraining via the API (admin only).
    POST body: { "model": "categorizer" | "budget" | "all" }
    """
    model_choice = request.data.get("model", "all")
    results = {}

    if model_choice in ("categorizer", "all"):
        results["categorizer"] = retrain_categorizer_if_ready(min_samples=5)

    if model_choice in ("budget", "all"):
        results["budget"] = retrain_budget_predictor_if_ready(min_samples=5)

    return Response(
        {
            "message": "Training complete",
            "results": results,
        }
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def model_status(request):
    """Return current status of all ML models."""
    models = MLModel.objects.filter(is_active=True)
    data = []
    for m in models:
        data.append(
            {
                "name": m.name,
                "type": m.model_type,
                "version": m.version,
                "accuracy": m.accuracy,
                "updated_at": m.updated_at.isoformat(),
            }
        )

    # Also check in-memory state
    categorizer = get_categorizer()
    predictor = get_budget_predictor()

    return Response(
        {
            "models": data,
            "categorizer_trained": categorizer.is_trained,
            "budget_predictor_trained": predictor.is_trained,
        }
    )
