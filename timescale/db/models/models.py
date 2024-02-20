from django.db import models
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager, CompressionManager, ContinuousAggregateManager


class TimescaleModel(models.Model):
    """
    A helper class for using Timescale within Django, has the TimescaleManager and 
    TimescaleDateTimeField already present. This is an abstract class it should 
    be inherited by another class for use.
    """
    time = TimescaleDateTimeField(interval="1 day")

    objects = models.Manager()
    timescale = TimescaleManager()
    compression = CompressionManager()

    class Meta:
        abstract = True
        required_db_vendor = 'postgresql'


class ContinuousAggregateModel(models.Model):
    """ Model to create and query timescaledb continuous aggregates """
    bucket = TimescaleDateTimeField(interval="2 day")

    timescale = TimescaleManager()
    compression = CompressionManager()
    continuous_aggregate = ContinuousAggregateManager()

    class Meta:
        abstract = True
        required_db_vendor = 'postgresql'
