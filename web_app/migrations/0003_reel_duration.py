# Generated by Django 4.0.4 on 2025-02-14 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_app', '0002_video_reel'),
    ]

    operations = [
        migrations.AddField(
            model_name='reel',
            name='duration',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
