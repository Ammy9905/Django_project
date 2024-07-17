import cv2
import dlib
from datetime import datetime
import os
import threading
import tkinter as tk
from tkinter import messagebox
import numpy as np
import time
from queue import Queue

# Function to show popup
def show_popup(message, popup_queue):
    root = tk.Tk()
    root.withdraw()
    while True:
        message = popup_queue.get()
        if message is None:  # Sentinel to end the thread
            break
        messagebox.showinfo("Alert", message)
    root.destroy()

def record(popup_queue):
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

    last_position = None
    tolerance = 7  # Reduced tolerance for finer movement detection
    smoothing_factor = 0.5  # Increased smoothing factor

    direction_detected = None
    direction_timestamps = {"left": None, "right": None, "up": None, "down": None}
    detection_state = {"book_detected": False, "smartwatch_detected": False}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

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
                        direction_detected = "right"
                        direction_timestamps["right"] = time.time()
                        for key in direction_timestamps:
                            if key != "right":
                                direction_timestamps[key] = None
                    elif dx < -tolerance and direction_detected != "left":
                        direction_detected = "left"
                        direction_timestamps["left"] = time.time()
                        for key in direction_timestamps:
                            if key != "left":
                                direction_timestamps[key] = None
                else:
                    if dy < -tolerance and direction_detected != "up":
                        direction_detected = "up"
                        direction_timestamps["up"] = time.time()
                        for key in direction_timestamps:
                            if key != "up":
                                direction_timestamps[key] = None
                    elif dy > tolerance and direction_detected != "down":
                        direction_detected = "down"
                        direction_timestamps["down"] = time.time()
                        for key in direction_timestamps:
                            if key != "down":
                                direction_timestamps[key] = None

            last_position = (smoothed_x, smoothed_y)

            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.circle(frame, (smoothed_x, smoothed_y), 5, (0, 0, 255), -1)
            cv2.circle(frame, nose, 5, (255, 0, 0), -1)
            cv2.circle(frame, left_eye, 5, (0, 255, 0), -1)
            cv2.circle(frame, right_eye, 5, (0, 255, 0), -1)

            current_time = time.time()

            # Check if the direction has been detected for at least 4 seconds
            for direction, timestamp in direction_timestamps.items():
                if timestamp is not None and (current_time - timestamp) >= 4:
                    popup_queue.put(f"Don't Turn: {direction.capitalize()}")
                    direction_timestamps[direction] = None  # Reset timestamp

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
                        person_count += 1
                        cv2.rectangle(frame, (startX, startY), (endX, endY), (255, 0, 0), 2)
                        cv2.putText(frame, "Person", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                        if person_count > 1:
                            popup_queue.put("Multiple Persons Detected")

                    elif detected_class == "book":
                        cv2.rectangle(frame, (startX, startY), (endX + width, endY + height), (0, 255, 255), 2)
                        cv2.circle(frame, (startX, startY), 5, (0, 0, 255), -1)
                        cv2.putText(frame, "Book Detected", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        if not detection_state["book_detected"]:
                            popup_queue.put("Book Detected")
                            detection_state["book_detected"] = True

        # Perform smartwatch-related actions outside the loop
        if detection_state["smartwatch_detected"]:
            popup_queue.put("Smartwatch Detected")
            detection_state["smartwatch_detected"] = False

        storage.write(frame)
        cv2.imshow('Recording', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    storage.release()
    cv2.destroyAllWindows()
    popup_queue.put(None)  # Send sentinel to stop the popup thread

if __name__ == "__main__":
    popup_queue = Queue()
    threading.Thread(target=show_popup, args=("Alert", popup_queue)).start()
    record(popup_queue)







