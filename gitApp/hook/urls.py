from django.urls import path
from gitApp.hook import views

urlpatterns = [
    path('base/', views.base),
    path("hook/", views.receiveHook)
]