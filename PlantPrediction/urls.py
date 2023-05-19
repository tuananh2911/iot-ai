from django.urls import path
from .views import PlantPredictionView

urlpatterns = [
    path('plant_prediction/', PlantPredictionView.as_view(), name='plant_prediction'),
]
