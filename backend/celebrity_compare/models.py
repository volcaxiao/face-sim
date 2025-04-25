from django.db import models
import os

class Celebrity(models.Model):
    name = models.CharField(max_length=100, verbose_name="姓名")
    photo = models.CharField(max_length=500, verbose_name="照片URL")
    face_token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Face++ 人脸Token")
    description = models.TextField(blank=True, null=True, verbose_name="简介")
    gender = models.CharField(max_length=10, blank=True, null=True, verbose_name="性别")
    nationality = models.CharField(max_length=50, blank=True, null=True, verbose_name="国籍")
    birth_date = models.CharField(max_length=50, blank=True, null=True, verbose_name="出生日期")
    detail_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="详情页URL")
    source = models.CharField(max_length=20, blank=True, null=True, verbose_name="数据源")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "名人"
        verbose_name_plural = "名人"
    
    def __str__(self):
        return self.name
        
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class ComparisonResult(models.Model):
    user_photo = models.ImageField(upload_to='user_photos/', verbose_name="用户照片")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "比对结果"
        verbose_name_plural = "比对结果"
        
    def __str__(self):
        return f"比对 {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def delete(self, *args, **kwargs):
        if self.user_photo:
            if os.path.isfile(self.user_photo.path):
                os.remove(self.user_photo.path)
        super().delete(*args, **kwargs)


class ComparisonDetail(models.Model):
    comparison = models.ForeignKey(ComparisonResult, on_delete=models.CASCADE, related_name="details", verbose_name="比对结果")
    celebrity = models.ForeignKey(Celebrity, on_delete=models.CASCADE, verbose_name="名人")
    similarity = models.FloatField(verbose_name="相似度")
    
    class Meta:
        verbose_name = "比对详情"
        verbose_name_plural = "比对详情"
        ordering = ['-similarity']
        
    def __str__(self):
        return f"{self.comparison} - {self.celebrity.name} ({self.similarity:.2f}%)"
