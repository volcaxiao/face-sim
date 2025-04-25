import uuid
from django.db import models
from django.utils import timezone

class Celebrity(models.Model):
    """名人模型"""
    name = models.CharField('姓名', max_length=100)
    photo = models.ImageField('照片', upload_to='celebrities/')
    description = models.TextField('描述', blank=True, null=True)
    face_token = models.CharField('Face++ Token', max_length=100, blank=True, null=True)
    birth_date = models.DateField('出生日期', blank=True, null=True)
    detail_url = models.URLField('详情链接', max_length=500, blank=True, null=True)
    source = models.CharField('来源', max_length=50, blank=True, null=True)
    # 新增字段
    nationality = models.CharField('国籍', max_length=50, blank=True, null=True)
    occupation = models.CharField('职业', max_length=100, blank=True, null=True)
    works = models.TextField('代表作品', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '名人'
        verbose_name_plural = '名人列表'


class ComparisonResult(models.Model):
    """比对结果模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_photo = models.ImageField('用户照片', upload_to='user_photos/')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    session_id = models.CharField('会话ID', max_length=100, blank=True, null=True)
    face_token = models.CharField('Face++ Token', max_length=100, blank=True, null=True)
    processing_status = models.CharField('处理状态', max_length=20, default='processing',
                                       choices=[
                                           ('processing', '处理中'), 
                                           ('completed', '已完成'), 
                                           ('failed', '失败')
                                       ])
    progress = models.IntegerField('处理进度', default=0)  # 0-100表示进度百分比
    message = models.TextField('处理消息', blank=True, null=True)  # 添加消息字段，用于存储错误信息
    is_public = models.BooleanField('是否公开分享', default=False)  # 添加字段标记是否可公开访问
    share_code = models.CharField('分享码', max_length=20, blank=True, null=True)  # 可选的短分享码
    
    def __str__(self):
        return f"比对结果 {self.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = '比对结果'
        verbose_name_plural = '比对结果列表'
        ordering = ['-created_at']


class ComparisonDetail(models.Model):
    """比对详情模型"""
    comparison = models.ForeignKey(
        ComparisonResult, 
        on_delete=models.CASCADE, 
        related_name='details',
        verbose_name='比对结果'
    )
    celebrity = models.ForeignKey(
        Celebrity, 
        on_delete=models.CASCADE,
        verbose_name='名人'
    )
    similarity = models.FloatField('相似度')
    
    def __str__(self):
        return f"{self.comparison.id} - {self.celebrity.name} ({self.similarity:.1f}%)"
    
    class Meta:
        verbose_name = '比对详情'
        verbose_name_plural = '比对详情列表'
        ordering = ['-similarity']
