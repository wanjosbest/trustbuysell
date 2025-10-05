from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Chat, Message

@login_required
def chat_list_view(request):
    """List all chats for the logged-in user."""
    chats = Chat.objects.filter(participants=request.user).order_by('-updated_at')
    return render(request, 'chat/chat.html', {'chats': chats})


@login_required
def chat_detail_view(request, chat_id):
    """Display chat messages and allow sending new ones."""
    chat = get_object_or_404(Chat, id=chat_id)

    # Ensure the user is a participant
    if request.user not in chat.participants.all():
        messages.error(request, "You are not authorized to view this chat.")
        return redirect('chat_list')

    messages_qs = chat.messages.all()

    # Mark received messages as read
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(chat=chat, sender=request.user, content=content)
            chat.save()  # updates timestamp
            return redirect('chat_detail', chat_id=chat.id)

    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': messages_qs,
        'other_user': chat.other_user(request.user),
    })


@login_required
def start_chat_view(request, username):
    """Start or open a chat between the logged-in user and another user."""
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        messages.error(request, "You cannot chat with yourself.")
        return redirect('chat_list')

    # Check if a chat already exists between the two users
    chat = Chat.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not chat:
        chat = Chat.objects.create()
        chat.participants.add(request.user, other_user)

    return redirect('chat_detail', chat_id=chat.id)

def chat(request):
    return render(request,"chat/seller_chat.html")