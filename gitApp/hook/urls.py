from django.urls import path
from hook import views

urlpatterns = [
    path('base/', views.base),
    path("hook/", views.receiveHook),
    path("", views.receiveHook)
]