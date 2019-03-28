from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from store.models import DeliveryTask, DeliveryStatus
from ..serializers import serializer
from store import queue


class DeliveryTaskListingAPI(ListAPIView):
    """
    API returns lists of delivery tasks.
    """
    permission_classes = (AllowAny,)
    serializer_class = serializer.StoreTaskSerializer

    def get_queryset(self):
        queryset = DeliveryTask.objects.filter(user_store__user_id=self.kwargs["pk"])
        return queryset


class GetLatestDeliveryTaskAPI(APIView):
    """
    This endpoint is used to return the latest delivery task.
    This API is used by the delivery boys to get the latest delivery task.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        if queue.read_data_from_queue() is False:
            return Response({"status": False, "message": "No New Order", "data": None}, status=status.HTTP_200_OK)

        result = DeliveryTask.objects.filter(id=queue.read_data_from_queue()["id"]).first()
        if result.last_known_state == "CANCELLED" or result.last_known_state == "DECLINED":
            queue.read_data_from_queue(acknowledge=True)
            return Response({"status": False, "message": "No New Order", "data": None}, status=status.HTTP_200_OK)
        else:
            return Response({"status": True, "message": None, "data": queue.read_data_from_queue()},
                            status=status.HTTP_200_OK)
