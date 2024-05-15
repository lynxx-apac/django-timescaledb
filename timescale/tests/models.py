from datetime import datetime
from django.db import models
from django.utils import timezone
from django.conf import settings
from ..db.models.models import ContinuousAggregateModel, TimescaleModel
from ..db.models.fields import TimescaleDateTimeField
from ..db.models.aggregates import First, Last
from ..db.models.expressions import Interval
from ..db.models.managers import TimescaleManager, CompressionManager, RetentionManager, ContinuousAggregateManager


class MetricRetentionManager(RetentionManager):
    drop_after = Interval('1 day')
    schedule_interval = Interval('1 hour')
    initial_start = timezone.now
    timezone = settings.TIME_ZONE
    if_not_exists = True
    drop_created_before = True


class MetricCompressionManager(CompressionManager):
    enable = True
    order_by = ['device', 'time']
    segment_by = ['last_temperature']
    chunk_time_interval = Interval('1 hour')
    # compression policy parameters
    schedule_interval = Interval('2 hours')
    initial_start = None
    timezone = None
    if_not_exists = True
    compress_created_before = None


class Metric(TimescaleModel):
    time = TimescaleDateTimeField(interval="10 minutes")
    temperature = models.FloatField(default=0.0)
    device = models.IntegerField(default=0)

    objects = models.Manager()
    compression = MetricCompressionManager()
    retention = MetricRetentionManager()
    timescale = TimescaleManager()


class MetricMaterializedView(ContinuousAggregateManager):
    materialized_only = True
    create_group_indexes = False
    finalized = False
    # continuous aggregate policy
    start_offset: (Interval, int) = None
    end_offset: (Interval, int) = None
    schedule_interval: Interval = None
    initial_start: datetime = None
    timezone: str = None

    def create_materialized_view(self):
        return Metric.timescale.time_bucket('time', interval='20 minutes').values('bucket', 'device').annotate(
            first_temperature=First('temperature', 'time'),
            last_temperature=Last('temperature', 'time'),
        )


class MetricCompression(CompressionManager):
    enable = True
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
    drop_after = Interval('1 day')
    schedule_interval = Interval('1 hour')
    initial_start: datetime = timezone.now
    timezone = settings.TIME_ZONE
    if_not_exists = True
    drop_created_before = True


class MetricAggregate(ContinuousAggregateModel):
    time = TimescaleDateTimeField(interval="2 day", primary_key=True)
    first_temperature = models.FloatField(null=True, blank=True)
    last_temperature = models.FloatField(null=True, blank=True)
    device = models.IntegerField(default=0)

    continuous_aggregate = MetricMaterializedView()
    compression = MetricCompression()
    retention = MetricAggregateRetentionManager()
