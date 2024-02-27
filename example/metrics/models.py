from typing import Optional

from django.db import models
from timescale.db.models.aggregates import First, Last
from timescale.db.models.expressions import Interval

from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.models import TimescaleModel, ContinuousAggregateModel
from timescale.db.models.managers import TimescaleManager, ContinuousAggregateManager, CompressionManager


class Metric(models.Model):
    time = TimescaleDateTimeField(interval="1 day")
    temperature = models.FloatField(default=0.0)
    device = models.IntegerField(default=0)

    objects = models.Manager()
    timescale = TimescaleManager()


class MetricMaterializedView(ContinuousAggregateManager):
    @staticmethod
    def first_last_temperature_view():
        return Metric.timescale.time_bucket('time', interval='2 days').values('bucket', 'device').annotate(
            first_temperature=First('temperature', 'time'),
            last_temperature=Last('temperature', 'time'),
        )

    def first_last_temperature_policy(self):
        pass


class MetricCompression(CompressionManager):
    enable: bool = True
    order_by: Optional[iter] = ['device', 'time']
    segment_by: Optional[iter] = ['last_temperature']
    chunk_time_interval: Optional[Interval] = Interval('1 hour')
    # compression policy parameters
    schedule_interval: Optional[str] = Interval('2 hours')
    initial_start: Optional[int] = None
    timezone: Optional[str] = None
    if_not_exists: Optional[bool] = True
    compress_created_before: Optional[bool] = None


class MetricAggregate(ContinuousAggregateModel):
    first_temperature = models.FloatField(null=True, blank=True)
    last_temperature = models.FloatField(null=True, blank=True)
    device = models.IntegerField(default=0)

    continuous_aggregate = MetricMaterializedView()
    compression = MetricCompression()
