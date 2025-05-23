# Generated by Django 5.1.6 on 2025-05-21 00:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chef_co', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PredictionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_data', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('party_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to='chef_co.partyorder')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
