from django.contrib import admin
from .models import Metric, MetricAggregate


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('time', 'temperature', 'device')


@admin.register(MetricAggregate)
class AnotherMetricFromTimeScaleModelAdmin(admin.ModelAdmin):
    list_display = ['time', 'device', 'first_temperature', 'last_temperature']
