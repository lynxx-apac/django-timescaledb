from django.db import models
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.db.models.sql.where import WhereNode, AND


class TimescaleRelatedForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_prefetch_querysets(self, instances, queryset=None):
        queryset = queryset or self.get_queryset()
        times = set(instance.time for instance in instances)
        queryset = queryset.filter(time__in=times)
        return super().get_prefetch_querysets(instances, [queryset])


class TimescaleRelatedForeignKey(models.ForeignKey):
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, TimescaleRelatedForwardManyToOneDescriptor(self))

    def get_extra_restriction(self, alias, related_alias):
        super().get_extra_restriction(alias, related_alias)
        time_field = self.opts.get_field('time')
        related_time_field = self.remote_field.model._meta.get_field('time')
        time_lookup = time_field.get_lookup('exact')(
            time_field.get_col(alias), related_time_field.get_col(related_alias))
        return WhereNode([time_lookup], connector=AND)
