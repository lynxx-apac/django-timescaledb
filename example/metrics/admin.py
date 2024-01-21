from django.contrib import admin
from .models import Metric, AnotherMetricFromTimeScaleModel


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('time', 'temperature', 'device')


@admin.register(AnotherMetricFromTimeScaleModel)
class AnotherMetricFromTimeScaleModelAdmin(admin.ModelAdmin):
    list_display = ['time', 'value']
