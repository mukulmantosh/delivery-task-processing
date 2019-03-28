from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = "store"

urlpatterns = [
    path('', login_required(views.IndexView.as_view()), name="index"),
    path('task-list/', login_required(views.TaskListView.as_view()), name="task-list"),
    path('create/', login_required(views.StoreView.as_view()), name="create-store"),
    path('detail/<int:pk>/', login_required(views.StoreTaskDetailView.as_view()), name="store-detail"),
    path('cancel/<int:pk>/', login_required(views.CancelStoreOrderView.as_view()), name="store-cancel-order"),

    path('delivery/', login_required(views.DeliveryIndex.as_view()), name="delivery-index"),
    path('delivery-order-list/', login_required(views.DeliveryOrderListView.as_view()), name="delivery-order-list"),
    path('delivery-order-process/', login_required(views.DeliveryOrderProcessView.as_view()),
         name="delivery-order-process"),
    path('delivery-order-accepted/', login_required(views.DeliveryTaskAcceptedOrderView.as_view()),
         name="delivery-task-accepted-order"),

]
