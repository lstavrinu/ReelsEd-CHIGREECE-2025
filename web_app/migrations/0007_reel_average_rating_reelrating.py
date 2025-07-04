# Generated by Django 4.0.4 on 2025-02-18 03:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web_app', '0006_alter_video_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='reel',
            name='average_rating',
            field=models.FloatField(default=0.0),
        ),
        migrations.CreateModel(
            name='ReelRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(default=0)),
                ('reel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='web_app.reel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'reel')},
            },
        ),
    ]
