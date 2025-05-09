# Generated by Django 5.2 on 2025-04-24 14:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Celebrity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='姓名')),
                ('photo', models.ImageField(upload_to='celebrities/', verbose_name='照片')),
                ('face_token', models.CharField(blank=True, max_length=255, null=True, verbose_name='Face++ 人脸Token')),
                ('description', models.TextField(blank=True, null=True, verbose_name='简介')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '名人',
                'verbose_name_plural': '名人',
            },
        ),
        migrations.CreateModel(
            name='ComparisonResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_photo', models.ImageField(upload_to='user_photos/', verbose_name='用户照片')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '比对结果',
                'verbose_name_plural': '比对结果',
            },
        ),
        migrations.CreateModel(
            name='ComparisonDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('similarity', models.FloatField(verbose_name='相似度')),
                ('celebrity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='celebrity_compare.celebrity', verbose_name='名人')),
                ('comparison', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='celebrity_compare.comparisonresult', verbose_name='比对结果')),
            ],
            options={
                'verbose_name': '比对详情',
                'verbose_name_plural': '比对详情',
                'ordering': ['-similarity'],
            },
        ),
    ]
