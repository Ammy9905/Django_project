import cv2
import dlib
from datetime import datetime
import os
import threading
import tkinter as tk
from tkinter import messagebox
import numpy as np
from queue import Queue

# Global flag for recording state
is_recording = False

# Queue for thread-safe popup messages
popup_queue = Queue()

# Capture current frame when a popup is shown
current_frame = None

def show_popup(message):
    global current_frame
    messagebox.showinfo("Alert", message)
    save_popup_frame(current_frame)

def process_queue():
    while not popup_queue.empty():
        message = popup_queue.get()
        show_popup(message)

def save_popup_frame(frame):
    popup_folder = 'popup_frames'
    if not os.path.exists(popup_folder):
        os.makedirs(popup_folder)
    
    popup_file = os.path.join(popup_folder, f'popup_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.jpg')
    cv2.imwrite(popup_file, frame)
    print(f"Popup frame saved: {popup_file}")

def record():
    global is_recording, current_frame

    cap = cv2.VideoCapture(0)

    # Initialize dlib's face detector and shape predictor
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')  # Path of .dat file

    # Load the YOLOv4-tiny model for phone, person, book, notebook, and smartwatch detection
    net = cv2.dnn.readNetFromDarknet('yolov4-tiny.cfg', 'yolov4-tiny.weights')
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    try:
        with open("coco.names", "r") as f:
            classes = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print("Error: coco.names file not found.")
        return
    except ValueError as e:
        print(str(e))
        return

    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    # Recordings Folder to save the video 
    output_folder = 'recordings'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file = os.path.join(output_folder, f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.avi')
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    storage = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'MJPG'), 15, (frame_width, frame_height))

    movement_count = {"left": 0, "right": 0, "up": 0, "down": 0}  
    last_position = None
    tolerance = 10  # Reduced tolerance for finer movement detection
    smoothing_factor = 0.3  # Increased smoothing factor

    direction_detected = None
    detection_state = {"book_detected": False, "smartwatch_detected": False}

    is_recording = True  # Start recording

    last_frame = None

    while is_recording:
        ret, frame = cap.read()
        if not ret:
            break

        # Update current frame for popup capture
        current_frame = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if faces:
            face = max(faces, key=lambda rect: rect.width() * rect.height())
            landmarks = predictor(gray, face)

            nose = (landmarks.part(30).x, landmarks.part(30).y)
            left_eye = (landmarks.part(36).x, landmarks.part(36).y)
            right_eye = (landmarks.part(45).x, landmarks.part(45).y)

            center_x = (left_eye[0] + right_eye[0]) // 2
            center_y = (left_eye[1] + right_eye[1]) // 2

            if last_position is not None:
                smoothed_x = int(smoothing_factor * center_x + (1 - smoothing_factor) * last_position[0])
                smoothed_y = int(smoothing_factor * center_y + (1 - smoothing_factor) * last_position[1])
            else:
                smoothed_x, smoothed_y = center_x, center_y

            if last_position is not None:
                dx = smoothed_x - last_position[0]
                dy = smoothed_y - last_position[1]

                # Check for direction and update counts
                if abs(dx) > abs(dy):
                    if dx > tolerance and direction_detected != "right":
                        movement_count["right"] += 1
                        direction_detected = "right"
                        if movement_count["right"] >= 1:
                            popup_queue.put("Don't Turn: Right")
                            movement_count["right"] = 0
                    elif dx < -tolerance and direction_detected != "left":
                        movement_count["left"] += 1
                        direction_detected = "left"
                        if movement_count["left"] >= 1:
                            popup_queue.put("Don't Turn: Left")
                            movement_count["left"] = 0
                else:
                    if dy < -tolerance and direction_detected != "up":
                        movement_count["up"] += 1
                        direction_detected = "up"
                        if movement_count["up"] >= 1:
                            popup_queue.put("Don't Turn: Up")
                            movement_count["up"] = 0
                    elif dy > tolerance and direction_detected != "down":
                        movement_count["down"] += 1
                        direction_detected = "down"
                        if movement_count["down"] >= 1:
                            popup_queue.put("Don't Turn: Down")
                            movement_count["down"] = 0

            last_position = (smoothed_x, smoothed_y)

            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.circle(frame, (smoothed_x, smoothed_y), 5, (0, 0, 255), -1)
            cv2.circle(frame, nose, 5, (255, 0, 0), -1)
            cv2.circle(frame, left_eye, 5, (0, 255, 0), -1)
            cv2.circle(frame, right_eye, 5, (0, 255, 0), -1)

        # Phone, person, book, and smartwatch detection
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        net.setInput(blob)
        detections = net.forward(output_layers)

        person_count = 0

        for detection in detections:
            for obj in detection:
                scores = obj[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.7:  # Adjust confidence threshold as needed
                    box = obj[0:4] * np.array([frame_width, frame_height, frame_width, frame_height])
                    (centerX, centerY, width, height) = box.astype("int")

                    startX = int(centerX - (width / 2))
                    startY = int(centerY - (height / 2))
                    endX = startX + width
                    endY = startY + height

                    detected_class = classes[class_id]
                    if detected_class == "cell phone":
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                        cv2.putText(frame, "Phone Detected", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        popup_queue.put("Phone Detected")

                    elif detected_class == "smartwatch":
                        detection_state["smartwatch_detected"] = True
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 255), 2)
                        cv2.putText(frame, "Smartwatch Detected", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                    elif detected_class == "person":
                        person_count = 1
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (255, 0, 0), 2)
                        cv2.putText(frame, "Person", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                        if person_count >= 1:
                            popup_queue.put("Multiple Persons Detected")

                    elif detected_class == "book":
                        cv2.rectangle(frame, (startX, startY), (endX + w, endY + h), (0, 255, 255), 2)
                        cv2.circle(frame,(startX, startY),5,(0,0,255), -1)
                        cv2.putText(frame, "Book Detected", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        if not detection_state["book_detected"]:
                            popup_queue.put("Book Detected")
                            detection_state["book_detected"] = True

        # Perform smartwatch-related actions outside the loop
        if detection_state["smartwatch_detected"]:
            popup_queue.put("Smartwatch Detected")
            detection_state["smartwatch_detected"] = False

        # Show popup for book detection
        if detection_state["book_detected"]:
            detection_state["book_detected"] = False

        cv2.imshow("Frame", frame)
        storage.write(frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        process_queue()  # Check and display popups from the queue

    cap.release()
    storage.release()
    cv2.destroyAllWindows()

def stop_recording():
    global is_recording
    is_recording = False

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # Start recording
    threading.Thread(target=record).start()

    
    
    # Example: button to stop recording
    button_stop = tk.Button(root, text="Stop Recording", command=stop_recording)
    button_stop.pack()

    # Main loop for tkinter GUI
    root.mainloop()









