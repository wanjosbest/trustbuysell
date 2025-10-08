from django.urls import path
from . import views

urlpatterns = [
    path('chat-list/', views.chat_list_view, name='chat_list'),
    path('chat/start/<str:username>/', views.start_chat_view, name='start_chat'),
    path('chat/<int:chat_id>/', views.chat_detail_view, name='chat_detail'),
]
