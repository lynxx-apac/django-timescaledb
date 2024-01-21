from django.db import models
from django.contrib.postgres.fields import ArrayField


class Histogram(models.Aggregate):
    """
    Implementation of the histogram function from Timescale.
    Read more about it here - https://docs.timescale.com/latest/using-timescaledb/reading-data#histogram
    Response:
    <TimescaleQuerySet [{'histogram': [0, 0, 0, 87, 93, 125, 99, 59, 0, 0, 0, 0], 'device__count': 463}]>

    """
    function = 'histogram'
    name = 'histogram'
    output_field = ArrayField(models.FloatField())

    def __init__(self, expression, min_value, max_value, bucket):
        super().__init__(expression, min_value, max_value, bucket)


class AggregateWithWeakRules(models.Aggregate):
    def _resolve_output_field(self):
        sources_iter = (
            source for source in self.get_source_fields() if source is not None
        )
        for output_field in sources_iter:
            return output_field


class Last(AggregateWithWeakRules):
    function = "last"
    name = "last"


class First(AggregateWithWeakRules):
    function = "first"
    name = "first"
