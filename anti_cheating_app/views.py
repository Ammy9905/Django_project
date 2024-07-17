from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .recording import record  # Import your recording function from the existing code
import threading
import os


recording_thread = None
recordings_directory = 'recordings'  # Ensure this matches the directory where recordings are saved

@csrf_exempt
def start_recording(request):
    global recording_thread
    if request.method == 'GET':
        if recording_thread is None or not recording_thread.is_alive():
            recording_thread = threading.Thread(target=record)
            recording_thread.start()
            return JsonResponse({'message': 'Recording started successfully.'})
        else:
            return JsonResponse({'message': 'Recording is already running.'})
    else:
        return JsonResponse({'error': 'Only GET requests are allowed.'}, status=400)

@csrf_exempt
def stop_recording(request):
    global recording_thread
    if request.method == 'GET':
        if recording_thread is not None and recording_thread.is_alive():
            recording_thread = threading.Thread(target=record)
            
         
            return JsonResponse({'message': 'Recording stopped successfully.'})
        else:
            return JsonResponse({'message': 'No recording is running.'})
    else:
        return JsonResponse({'error': 'Only GET requests are allowed.'}, status=400)

@csrf_exempt
def get_recordings(request):
    if request.method == 'GET':
        if not os.path.exists(recordings_directory):
            return JsonResponse({'recordings': []})
        
        recordings_list = os.listdir(recordings_directory)
        recordings_list = [f for f in recordings_list if os.path.isfile(os.path.join(recordings_directory, f))]
        return JsonResponse({'recordings': recordings_list})
    else:
        return JsonResponse({'error': 'Only GET requests are allowed.'}, status=400)


