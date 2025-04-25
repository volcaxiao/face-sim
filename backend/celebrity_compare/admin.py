from django.contrib import admin
from django.utils.html import format_html
from .models import Celebrity, ComparisonResult, ComparisonDetail

@admin.register(Celebrity)
class CelebrityAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'occupation', 'birth_date', 'source', 'show_photo', 'created_at')
    search_fields = ('name', 'nationality', 'occupation', 'description', 'works')
    list_filter = ('nationality', 'occupation', 'source', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'show_photo_large')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'photo', 'show_photo_large', 'description')
        }),
        ('详细信息', {
            'fields': ('nationality', 'occupation', 'birth_date', 'works')
        }),
        ('技术信息', {
            'fields': ('source', 'detail_url', 'face_token', 'created_at', 'updated_at')
        }),
    )
    
    def show_photo(self, obj):
        """在列表中显示缩略图"""
        if obj.photo:
            # 检查是否为外部URL
            if str(obj.photo).startswith(('http://', 'https://')):
                return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', str(obj.photo))
            else:
                return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.photo.url)
        return "无照片"
    show_photo.short_description = '照片'
    
    def show_photo_large(self, obj):
        """在详情页中显示大图"""
        if obj.photo:
            # 检查是否为外部URL
            if str(obj.photo).startswith(('http://', 'https://')):
                return format_html('<img src="{}" width="200" />', str(obj.photo))
            else:
                return format_html('<img src="{}" width="200" />', obj.photo.url)
        return "无照片"
    show_photo_large.short_description = '照片预览'

@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'show_user_photo', 'created_at', 'session_id_short', 'processing_status', 'progress', 'is_public')
    list_filter = ('processing_status', 'created_at', 'is_public')
    readonly_fields = ('id', 'created_at', 'session_id', 'face_token', 'show_user_photo_large')
    search_fields = ('session_id', 'id', 'message', 'share_code')
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'user_photo', 'show_user_photo_large', 'created_at')
        }),
        ('处理信息', {
            'fields': ('processing_status', 'progress', 'message')
        }),
        ('分享信息', {
            'fields': ('is_public', 'share_code')
        }),
        ('技术信息', {
            'fields': ('session_id', 'face_token')
        }),
    )
    
    def id_short(self, obj):
        """显示ID的前8位"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def session_id_short(self, obj):
        """显示会话ID的前8位"""
        if obj.session_id:
            return obj.session_id[:8] + '...'
        return "无会话ID"
    session_id_short.short_description = '会话ID'
    
    def show_user_photo(self, obj):
        """在列表中显示用户照片缩略图"""
        if obj.user_photo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.user_photo.url)
        return "无照片"
    show_user_photo.short_description = '用户照片'
    
    def show_user_photo_large(self, obj):
        """在详情页中显示大图"""
        if obj.user_photo:
            return format_html('<img src="{}" width="200" />', obj.user_photo.url)
        return "无照片"
    show_user_photo_large.short_description = '照片预览'
    
    def has_add_permission(self, request):
        """禁止手动添加比对结果"""
        return False

@admin.register(ComparisonDetail)
class ComparisonDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'comparison_id', 'celebrity_name', 'similarity_percent')
    list_filter = ('similarity',)
    search_fields = ('comparison__id', 'celebrity__name')
    readonly_fields = ('comparison', 'celebrity', 'similarity')
    
    def id(self, obj):
        return obj.pk
    id.short_description = 'ID'
    
    def comparison_id(self, obj):
        """显示比对结果ID的前8位"""
        return str(obj.comparison.id)[:8] + '...'
    comparison_id.short_description = '比对结果ID'
    
    def celebrity_name(self, obj):
        """显示名人姓名"""
        return obj.celebrity.name
    celebrity_name.short_description = '名人'
    
    def similarity_percent(self, obj):
        """将相似度显示为百分比"""
        return f"{obj.similarity:.2f}%"
    similarity_percent.short_description = '相似度'
    
    def has_add_permission(self, request):
        """禁止手动添加比对详情"""
        return False
