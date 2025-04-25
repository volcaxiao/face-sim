from rest_framework import serializers
from celebrity_compare.models import Celebrity, ComparisonResult, ComparisonDetail


class CelebritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Celebrity
        fields = ['id', 'name', 'photo', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class ComparisonDetailSerializer(serializers.ModelSerializer):
    celebrity = CelebritySerializer(read_only=True)
    
    class Meta:
        model = ComparisonDetail
        fields = ['celebrity', 'similarity']


class ComparisonResultSerializer(serializers.ModelSerializer):
    details = ComparisonDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = ComparisonResult
        fields = ['id', 'user_photo', 'created_at', 'details']
        read_only_fields = ['id', 'created_at']
        

class PhotoUploadSerializer(serializers.Serializer):
    photo = serializers.ImageField(required=True)