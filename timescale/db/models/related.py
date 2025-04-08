from django.db import models
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor, ReverseManyToOneDescriptor, \
    create_reverse_many_to_one_manager
from django.db.models.sql.where import WhereNode, AND
from django.utils.functional import cached_property


class TimeBasedPrefetchMixin:
    def get_prefetch_querysets(self, instances, querysets=None):
        queryset = querysets[0] if querysets else super().get_queryset()
        times = set(instance.time for instance in instances)
        queryset = queryset.filter(time__in=times)
        return super().get_prefetch_querysets(instances, [queryset])


class TimescaleRelatedReverseManyToOneDescriptor(ReverseManyToOneDescriptor):
    @cached_property
    def related_manager_cls(self):
        class TimescaleRelatedManager(TimeBasedPrefetchMixin, super().related_manager_cls):
            def get_queryset(self):
                queryset = super().get_queryset()
                if self.instance is not None:
                    queryset = queryset.filter(time=self.instance.time)
                return queryset

        return TimescaleRelatedManager


class TimescaleRelatedForwardManyToOneDescriptor(TimeBasedPrefetchMixin, ForwardManyToOneDescriptor):
    def get_queryset(self, **hints):
        queryset = super().get_queryset(**hints)
        instance = hints.get('instance')
        if instance:
            queryset = queryset.filter(time=instance.time)
        return queryset


class TimescaleRelatedForeignKey(models.ForeignKey):
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, TimescaleRelatedForwardManyToOneDescriptor(self))

    def contribute_to_related_class(self, cls, related):
        super().contribute_to_related_class(cls, related)
        if not self.remote_field.hidden:
            setattr(cls, related.get_accessor_name(), TimescaleRelatedReverseManyToOneDescriptor(related))

    def get_extra_restriction(self, alias, related_alias):
        super().get_extra_restriction(alias, related_alias)
        time_field = self.opts.get_field('time')
        related_time_field = self.remote_field.model._meta.get_field('time')
        time_lookup = time_field.get_lookup('exact')(
            time_field.get_col(alias), related_time_field.get_col(related_alias))
        return WhereNode([time_lookup], connector=AND)
