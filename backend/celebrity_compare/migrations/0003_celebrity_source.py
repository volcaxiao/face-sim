# Generated by Django 5.2 on 2025-04-25 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celebrity_compare', '0002_celebrity_birth_date_celebrity_detail_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='celebrity',
            name='source',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='数据源'),
        ),
    ]
