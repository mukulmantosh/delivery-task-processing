import json
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from urban_piper import utils
from . import queue


class Timestamp(models.Model):
    """
    This is an abstract model. Needs to be inherited by other classes.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Store(Timestamp):
    """
    This model is representing to a restaurant, hotel etc.
    """
    name = models.CharField(max_length=255)
    address = models.TextField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class UserStore(Timestamp):
    """
    This model is mapping the relation between the store manager and the restaurant, hotel store.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} -- {self.store}"


class DeliveryTask(Timestamp):
    """
    This model is used to store orders by the store managers based on priority.
    """
    user_store = models.ForeignKey(UserStore, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    priority = models.CharField(max_length=6, choices=utils.TASK_PRIORITY)
    last_known_state = models.CharField(max_length=25, default='NEW')

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.title} -- {self.priority} PRIORITY -- {self.last_known_state}"


class DeliveryLogs(Timestamp):
    """
    This model is used to store logs of the respective delivery task.
    And here user is the delivery boy.
    """
    delivery_task = models.ForeignKey(DeliveryTask, on_delete=models.CASCADE, related_name="delivery_logs")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_status = models.CharField(max_length=25, choices=utils.DELIVERY_STATES)

    def __str__(self):
        return f"{self.user} -- {self.delivery_status}"


class DeliveryStatus(Timestamp):
    """
    This model is used to store delivery status.
    For example: The delivery boys who accepted or declined orders along-with their timestamps.
    """
    delivery_tasks = models.ForeignKey(DeliveryTask, on_delete=models.CASCADE, related_name="delivery_status")
    delivery_log = models.ForeignKey(DeliveryLogs, on_delete=models.CASCADE)
    delivery_status = models.CharField(max_length=25, choices=utils.DELIVERY_STATES)

    def __str__(self):
        return f"{self.delivery_log} -- {self.delivery_status}"


@receiver(post_save, sender=DeliveryTask)
def store_task_status(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "store_task_notify_user_{}".format(instance.user_store.user.id), {
            "type": "user.store.task.notify",
            "event": json.dumps({"is_deleted": False, "is_new": True if created else False, "id": instance.id,
                                 "title": instance.title, "priority": instance.priority,
                                 "last_known_state": instance.last_known_state}),
        }
    )
    if created:
        queue.store_data_in_queue(instance)
        async_to_sync(channel_layer.group_send)(
            "gossip", {
                "type": "user.gossip",
                "event": json.dumps({"is_deleted": False, "data": queue.read_data_from_queue()}),
            }
        )


@receiver(post_delete, sender=DeliveryTask)
def store_task_remove(sender, instance, **kwargs):
    read_queue_data = queue.read_data_from_queue()
    if read_queue_data is not False:
        if read_queue_data["id"] == instance.id:
            queue.read_data_from_queue(acknowledge=True)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "store_task_notify_user_{}".format(instance.user_store.user.id), {
            "type": "user.store.task.notify",
            "event": json.dumps({"is_deleted": True, "id": instance.id}),
        }
    )

    async_to_sync(channel_layer.group_send)(
        "gossip", {
            "type": "user.gossip",
            "event": json.dumps({"is_deleted": True, "data": instance.id}),
        }
    )


@receiver(post_save, sender=DeliveryLogs)
def process_delivery_task(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    if created:
        if instance.delivery_status == "DECLINED":
            delivery_task = DeliveryTask.objects.get(id=instance.delivery_task.id)

            queue.store_data_in_queue(delivery_task)
            async_to_sync(channel_layer.group_send)(
                "gossip", {
                    "type": "user.gossip",
                    "event": json.dumps({"is_deleted": False, "data": queue.read_data_from_queue()}),
                }
            )
        else:

            async_to_sync(channel_layer.group_send)(
                "gossip", {
                    "type": "user.gossip",
                    "event": json.dumps({"is_deleted": True, "data": instance.delivery_task.id}),
                }
            )

    else:
        if instance.delivery_status == "DECLINED":
            delivery_task = DeliveryTask.objects.get(id=instance.delivery_task.id)

            queue.store_data_in_queue(delivery_task)
            async_to_sync(channel_layer.group_send)(
                "gossip", {
                    "type": "user.gossip",
                    "event": json.dumps({"is_deleted": False, "data": queue.read_data_from_queue()}),
                }
            )
        else:
            async_to_sync(channel_layer.group_send)(
                "gossip", {
                    "type": "user.gossip",
                    "event": json.dumps({"is_deleted": True, "data": instance.delivery_task.id}),
                }
            )
