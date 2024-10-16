from django.db import models
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor


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

    def resolve_related_fields(self):
        related_fields = super().resolve_related_fields()
        related_fields.append((self.opts.get_field('time'), self.remote_field.model._meta.get_field('time')))
        return related_fields
