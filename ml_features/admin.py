from django.contrib import admin
from .models import MLModel, PredictionLog


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'version', 'accuracy', 'is_active', 'created_at']
    list_filter = ['model_type', 'is_active']
    search_fields = ['name', 'version']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'model', 'confidence', 'created_at']
    list_filter = ['model', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
