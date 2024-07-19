from django.shortcuts import render
from .consumers import ChatConsumer
from asgiref.sync import async_to_sync
def index(request):
    rooms = ['Technology','Travel', 'Gaming']  # Add your rooms here
    room_data = {room: async_to_sync(ChatConsumer.get_room_user_count)(room) for room in rooms}
    # room_data["Technology"]=1600
    room_data["Travel"]=3456
    room_data["Gaming"]=470
    return render(request, 'chat/index.html', {'rooms': room_data})

def room(request, room_name):
    
    return render(request, 'chat/room.html', {
        'room_name': room_name
    })
