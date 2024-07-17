import cv2
import os

# Define the folder where images will be saved
image = "captured_images"

# Create the folder if it doesn't exist
if not os.path.exists(image):
    os.makedirs(image)
    print(f"Created folder: {image}")
else:
    print(f"Folder already exists: {image}")

# Start the camera
cam = cv2.VideoCapture(0)

cv2.namedWindow("Image Capture App")

img_counter = 0

while True:
    ret, frame = cam.read()

    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("Image Capture", frame)

    k = cv2.waitKey(1)

    if k % 256 == 27:  # ESC pressed
        print("Escape hit, closing the app")
        break
    elif k % 256 == 32:  # SPACE pressed
        img_name = os.path.join(image, f"opencv_frame_{img_counter}.png")
        cv2.imwrite(img_name, frame)
        print(f"Image Taken: {img_name}")
        img_counter += 1

cam.release()
cv2.destroyAllWindows()
