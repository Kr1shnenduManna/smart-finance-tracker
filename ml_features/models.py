from django.db import models
from accounts.models import User


class MLModel(models.Model):
    """Model to store ML model metadata"""
    MODEL_TYPES = [
        ('categorization', 'Transaction Categorization'),
        ('prediction', 'Budget Prediction'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=20)
    accuracy = models.FloatField(null=True, blank=True)
    file_path = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    class Meta:
        db_table = 'ml_models'
        ordering = ['-created_at']


class PredictionLog(models.Model):
    """Log for ML predictions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prediction_logs')
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    input_data = models.JSONField()
    prediction = models.JSONField()
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.model.name} - {self.user.username} - {self.created_at}"
    
    class Meta:
        db_table = 'prediction_logs'
        ordering = ['-created_at']
