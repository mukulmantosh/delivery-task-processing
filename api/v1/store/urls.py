from django.urls import path
from ..store.controller import views

urlpatterns = [
    path('store-task-listing/<int:pk>/', views.DeliveryTaskListingAPI.as_view()),
    path('latest-delivery-task/', views.GetLatestDeliveryTaskAPI.as_view()),

]
