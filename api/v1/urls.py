from django.urls import path, include

urlpatterns = [
    path('v1/store/', include('api.v1.store.urls')),


]
