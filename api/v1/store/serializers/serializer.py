from rest_framework import serializers
from store.models import DeliveryTask


class StoreTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryTask
        fields = ("id", "title", "priority", "last_known_state")
