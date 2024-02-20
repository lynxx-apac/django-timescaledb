from django.db import models
from timescale.db.models.aggregates import First, Last

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
    def create_materialized_view(self):
        return Metric.timescale.time_bucket('time', interval='2 days').values('bucket', 'device').annotate(
            first_temperature=First('temperature', 'time'),
            last_temperature=Last('temperature', 'time'),
        )

    def create_continuous_aggregate_policy(self):
        pass


class MetricCompression(CompressionManager):
    pass


class MetricAggregate(ContinuousAggregateModel):
    first_temperature = models.FloatField(null=True, blank=True)
    last_temperature = models.FloatField(null=True, blank=True)
    device = models.IntegerField(default=0)

    continuous_aggregate = MetricMaterializedView()
    compression = MetricCompression()
