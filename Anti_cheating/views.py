
from django.http import JsonResponse

def start_recording (request):
    # Your code for starting recording
    return JsonResponse({'status': 'Recording started'})

def stop_recording(request):
    # Your code for stopping recording
    return JsonResponse({'status': 'Recording stopped'})
