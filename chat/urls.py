from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list_view, name='chat_list'),
    path('<int:chat_id>/', views.chat_detail_view, name='chat_detail'),
    path('chat/start/<str:username>/', views.start_chat_view, name='start_chat'),
    path("chats/", views.chat, name="chats"),
]
