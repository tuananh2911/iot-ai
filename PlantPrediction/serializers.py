from rest_framework import serializers

class PlantPredictionSerializer(serializers.Serializer):
    prediction=serializers.CharField()
    suggestions = serializers.ListField(child=serializers.CharField())