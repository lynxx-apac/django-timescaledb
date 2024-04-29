from datetime import datetime
from django.db import models

from timescale.db.models.expressions import Interval
from timescale.db.models.querysets import TimescaleQuerySet
from typing import Optional


class TimescaleManager(models.Manager):
    """
    A custom model manager specifically designed around the Timescale
    functions and tooling that has been ported to Django's ORM.
    """
    def get_queryset(self):
        return TimescaleQuerySet(self.model, using=self._db)

    def time_bucket(self, field, interval):
        return self.get_queryset().time_bucket(field, interval)

    def time_bucket_gapfill(
            self, field: str, interval: str, start: datetime, end: datetime, datapoints: Optional[int] = None):
        return self.get_queryset().time_bucket_gapfill(field, interval, start, end, datapoints)

    def histogram(self, field: str, min_value: float, max_value: float, num_of_buckets: int = 5):
        return self.get_queryset().histogram(field, min_value, max_value, num_of_buckets)


class ContinuousAggregateManager(TimescaleManager):
    """ Custom manager to define materialized view and refresh policy """
    use_in_migrations = True  # required so it is included in migrations and can be called to generate query for view
    materialized_only = True
    create_group_indexes = False
    finalized = False

    def create_materialized_view(self):
        """ define materialized view for continuous aggregation that will produce its parent table """
        pass

    def create_continuous_aggregate_policy(self):
        """ create refresh policy for continuous aggregation """
        pass


class CompressionManager(models.Manager):
    """ custom manager to define compression of table and its policy """
    use_in_migrations = True
    enable: bool = True
    order_by: Optional[iter] = None
    segment_by: Optional[iter] = None
    chunk_time_interval: Optional[Interval] = None
    # compression policy parameters
    compress_after: Interval = None
    schedule_interval: Optional[Interval] = None
    initial_start: Optional[datetime] = None
    timezone: Optional[str] = None
    if_not_exists: Optional[bool] = True
    compress_created_before: Optional[Interval] = None

    @property
    def compress_order_by(self):
        if self.order_by is None:
            return ''
        order_by = []
        for order_field in self.order_by:
            if order_field.startswith('-'):
                order_field = f'{order_field} ASC'
            order_by.append(order_field)
        return f", compress_orderby = '{",".join(order_by)}'"

    @property
    def compress_segment_by(self):
        if self.segment_by is None:
            return ''
        return f", compress_segmentby = '{",".join(self.segment_by)}'"

    @property
    def compress_chunk_time_interval(self):
        if self.chunk_time_interval is None:
            return ''
        return f", compress_chunk_time_interval = '{self.chunk_time_interval.value}'"


class RetentionManager(models.Manager):
    drop_after: Interval = None
    schedule_interval: Interval = None
    initial_start: datetime = None
    timezone: str = None
    if_not_exists: bool = False
    drop_created_before: bool = False
