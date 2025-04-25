from django.contrib import admin
from .models import Celebrity, ComparisonResult, ComparisonDetail

@admin.register(Celebrity)
class CelebrityAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)

@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    readonly_fields = ('created_at',)
    
@admin.register(ComparisonDetail)
class ComparisonDetailAdmin(admin.ModelAdmin):
    list_display = ('comparison', 'celebrity', 'similarity')
    list_filter = ('similarity',)
