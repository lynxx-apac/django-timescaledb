from django.db import migrations, models
from django.utils import timezone
from django.conf import settings
from ...db.models.fields import TimescaleDateTimeField
from ...db.models.managers import ContinuousAggregateManager, CompressionManager, RetentionManager
from ...db.models.aggregates import First, Last
from ...db.models.expressions import Interval


class MetricMaterializedView(ContinuousAggregateManager):
    def first_last_temperature_view(self):
        return self.model.timescale.time_bucket('time', interval='2 days').values('bucket', 'device').annotate(
            first_temperature=First('temperature', 'time'),
            last_temperature=Last('temperature', 'time'),
        )


class MetricCompression(CompressionManager):
    enable: bool = True
    order_by = ['device', 'time']
    segment_by = ['last_temperature']
    chunk_time_interval = Interval('1 hour')
    # compression policy parameters
    schedule_interval = Interval('2 hours')
    initial_start = None
    timezone = None
    if_not_exists = True
    compress_created_before = None


class MetricAggregateRetentionManager(RetentionManager):
    drop_after: Interval = Interval('1 day')
    schedule_interval: Interval = Interval('1 hour')
    initial_start = timezone.now
    timezone = settings.TIME_ZONE
    if_not_exists = True
    drop_created_before = True


class Migration(migrations.Migration):
    dependencies = [
        ("postgres_tests", "0001_setup_extensions"),
    ]

    operations = [
        migrations.CreateModel(
            name="Metric",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "time",
                    TimescaleDateTimeField(interval="1 day"),
                ),
                ("temperature", models.FloatField(default=0.0)),
                ("device", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="MetricAggregate",
            fields=[
                (
                    "time",
                    TimescaleDateTimeField(
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
                ("continuous_aggregate", MetricMaterializedView()),
                ("compression", MetricCompression()),
            ],
        ),
    ]