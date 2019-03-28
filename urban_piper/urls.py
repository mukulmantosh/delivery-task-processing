from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('admin/', admin.site.urls),
    path('store/', login_required(include('store.urls'))),
    path('api/', include('api.v1.urls')),

]
