from django.contrib import admin
from . import models


class DeliveryTaskAdmin(admin.ModelAdmin):
    readonly_fields=('last_known_state',)

admin.site.register(models.Store)
admin.site.register(models.DeliveryTask, DeliveryTaskAdmin)
admin.site.register(models.UserStore)
admin.site.register(models.DeliveryLogs)
admin.site.register(models.DeliveryStatus)