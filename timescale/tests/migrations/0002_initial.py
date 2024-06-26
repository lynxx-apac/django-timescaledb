# Generated by Django 5.0.4 on 2024-05-20 02:12

import django.db.models.manager
import timescale.db.models.fields
import timescale.tests.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tests", "0001_setup_extensions"),
    ]

    operations = [
        migrations.CreateModel(
            name="Metric",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "time",
                    timescale.db.models.fields.TimescaleDateTimeField(
                        interval="10 minutes"
                    ),
                ),
                ("temperature", models.FloatField(default=0.0)),
                ("device", models.IntegerField(default=0)),
            ],
            options={
                "abstract": False,
                "required_db_vendor": "postgresql",
            },
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("compression", timescale.tests.models.MetricCompressionManager()),
            ],
        ),
        migrations.CreateModel(
            name="MetricAggregate",
            fields=[
                (
                    "time",
                    timescale.db.models.fields.TimescaleDateTimeField(
                        interval="2 day", primary_key=True, serialize=False
                    ),
                ),
                ("first_temperature", models.FloatField(blank=True, null=True)),
                ("last_temperature", models.FloatField(blank=True, null=True)),
                ("device", models.IntegerField(default=0)),
            ],
            options={
                "abstract": False,
                "required_db_vendor": "postgresql",
            },
            managers=[
                (
                    "continuous_aggregate",
                    timescale.tests.models.MetricMaterializedView(),
                ),
                ("compression", timescale.tests.models.MetricCompression()),
            ],
        ),
    ]
