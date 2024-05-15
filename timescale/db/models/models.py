from django.db import models
from django.utils import timezone
from django.db import connection
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager, CompressionManager, ContinuousAggregateManager
from timescale.db.models.managers import RetentionManager


class TimescaleModel(models.Model):
    """
    A helper class for using Timescale within Django, has the TimescaleManager and 
    TimescaleDateTimeField already present. This is an abstract class it should 
    be inherited by another class for use.
    """
    time = TimescaleDateTimeField(interval="1 day")

    objects = models.Manager()
    retention = RetentionManager()
    timescale = TimescaleManager()
    compression = CompressionManager()

    class Meta:
        abstract = True
        required_db_vendor = 'postgresql'


class ContinuousAggregateModel(models.Model):
    """ Model to create and query timescaledb continuous aggregates """
    time = TimescaleDateTimeField(interval="2 day", primary_key=True)

    timescale = TimescaleManager()
    retention = RetentionManager()
    compression = CompressionManager()
    continuous_aggregate = ContinuousAggregateManager()

    class Meta:
        abstract = True
        required_db_vendor = 'postgresql'

    def refresh_continuous_aggregate(self, start_datetime=None, end_datetime=None):
        if end_datetime is None:
            end_datetime = timezone.now()
        if start_datetime is None:
            interval = self._meta.get_field('time').interval.split(' ')  # turns '6 hours' into ['6', 'hours']
            # needs at least double the time interval to aggregate into buckets
            start_datetime = end_datetime - timezone.timedelta(**{interval[1]: int(interval[0])*2})
        cursor = connection.cursor()
        cursor.execute(
            "call refresh_continuous_aggregate('%s', '%s', '%s')" %
            (self._meta.db_table, start_datetime.isoformat(), end_datetime.isoformat())
        )
        connection.commit()
