from django.db import models


class TimescaleRelatedForeignKey(models.ForeignKey):
    def resolve_related_fields(self):
        related_fields = super().resolve_related_fields()
        related_fields.append((self.opts.get_field('time'), self.remote_field.model._meta.get_field('time')))
        return related_fields
