from rest_framework import serializers
from celebrity_compare.models import Celebrity, ComparisonResult, ComparisonDetail


class CelebritySerializer(serializers.ModelSerializer):
    # 添加自定义字段处理外部URL
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Celebrity
        fields = [
            'id', 'name', 'photo', 'photo_url', 'description', 
            'detail_url', 'birth_date', 'nationality', 
            'occupation', 'works', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_photo_url(self, obj):
        """
        处理明星照片URL，确保正确处理外部链接和本地媒体文件
        """
        # 检查照片URL是否为外部链接
        if obj.photo and str(obj.photo).startswith(('http://', 'https://')):
            # 直接使用外部URL，不需要本地路径处理
            return str(obj.photo)
        elif obj.photo:
            # 本地媒体文件，通过request构建完整URL
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


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