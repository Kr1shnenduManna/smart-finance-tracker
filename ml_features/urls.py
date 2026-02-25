from django.urls import path
from . import views

urlpatterns = [
    path("predict/category/", views.predict_category, name="predict-category"),
    path("predict/budget/", views.predict_budget, name="predict-budget"),
    path("train/", views.train_models, name="train-models"),
    path("status/", views.model_status, name="model-status"),
]
