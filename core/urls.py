from django.urls import path
from .views import UserListView
from .api import AppUserListView

urlpatterns = [
    path("users/", AppUserListView.as_view(), name="users"),
]
