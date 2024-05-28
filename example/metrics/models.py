from datetime import datetime
from typing import Optional
from django.db import models
from django.utils import timezone
from django.conf import settings
from timescale.db.models.aggregates import First, Last
from timescale.db.models.expressions import Interval
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.models import TimescaleModel, ContinuousAggregateModel
from timescale.db.models.managers import (
    TimescaleManager,
    ContinuousAggregateManager,
    CompressionManager,
)
from timescale.db.models.managers import RetentionManager


class MetricRetentionManager(RetentionManager):
    drop_after: Interval = Interval("1 day")
    schedule_interval: Interval = Interval("1 hour")
    initial_start: datetime = timezone.now
    timezone: str = settings.TIME_ZONE
    if_not_exists: bool = True
    drop_created_before: bool = True


class Metric(models.Model):
    time = TimescaleDateTimeField(interval="1 day")
    temperature = models.FloatField(default=0.0)
    device = models.IntegerField(default=0)

    objects = models.Manager()
    retention = MetricRetentionManager()
    timescale = TimescaleManager()


class MetricMaterializedView(ContinuousAggregateManager):
    create_group_indexes = False
    finalized = False
    # continuous aggregate policy
    start_offset: (Interval, int) = None
    end_offset: (Interval, int) = None
    schedule_interval: Interval = None
    initial_start: datetime = None
    timezone: str = None

    def create_materialized_view(self):
        return (
            Metric.timescale.time_bucket("time", interval="2 days")
            .values("bucket", "device")
            .annotate(
                first_temperature=First("temperature", "time"),
                last_temperature=Last("temperature", "time"),
            )
        )


class MetricCompression(CompressionManager):
    enable: bool = True
    order_by: Optional[iter] = ["device", "time"]
    segment_by: Optional[iter] = ["last_temperature"]
    chunk_time_interval: Optional[Interval] = Interval("1 hour")
    # compression policy parameters
    schedule_interval: Optional[str] = Interval("2 hours")
    initial_start: Optional[int] = None
    timezone: Optional[str] = None
    if_not_exists: Optional[bool] = True
    compress_created_before: Optional[bool] = None


class MetricAggregateRetentionManager(RetentionManager):
    drop_after: Interval = Interval("1 day")
    schedule_interval: Interval = Interval("1 hour")
    initial_start: datetime = timezone.now
    timezone: str = settings.TIME_ZONE
    if_not_exists: bool = True
    drop_created_before: bool = True


class MetricAggregate(ContinuousAggregateModel):
    first_temperature = models.FloatField(null=True, blank=True)
    last_temperature = models.FloatField(null=True, blank=True)
    device = models.IntegerField(default=0)

    continuous_aggregate = MetricMaterializedView()
    compression = MetricCompression()
    retention = MetricAggregateRetentionManager()
