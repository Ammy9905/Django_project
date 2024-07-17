import cv2
import os
import requests
import base64
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

# Function to capture image with unique filename
def capture_image(image_folder):
    # Start the camera
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("Image Capture App")

    img_name = None

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
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y %m %d_%H %M %S")
            img_name = os.path.join(image_folder, f"opencv_frame_{timestamp}.png")
            
            cv2.imwrite(img_name, frame)
            print(f"Image Taken: {img_name}")

    # Release the camera and close all windows
    cam.release()
    cv2.destroyAllWindows()

    return img_name

# Function to authenticate Aadhaar number using UIDAI API
def authenticate_aadhaar(aadhaar_number, name, image_path, mobile_number, otp):
    # UIDAI Authentication API endpoint (example URL)
    api_url = 'https://intelligent-document-extraction.p.rapidapi.com/'  # Replace with actual UIDAI API URL

    # Read image as base64
    with open(image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    # Example payload (adjust according to UIDAI API specifications)
    payload = {
        "aadhaar_number": aadhaar_number,
        "name": name,
        "image_base64": image_base64,
        "mobile_number": mobile_number,
        "otp": otp
        
    }

    try:
        # Make POST request to UIDAI API
        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("Aadhaar authentication successful.")
                return True
            else:
                print(f"Aadhaar authentication failed: {result.get('message')}")
                return False
        else:
            print(f"Failed to authenticate Aadhaar: {response.status_code}")
            return False

    except Exception as e:
        print(f"Exception during Aadhaar authentication: {str(e)}")
        return False

# Function to save Aadhaar details and image locally
def save_aadhaar_details(aadhaar_number, name, mobile_number, image_path):
    details_folder = "aadhaar_details"
    if not os.path.exists(details_folder):
        os.makedirs(details_folder)

    details_file = os.path.join(details_folder, "aadhaar_details.txt")
    with open(details_file, "a") as f:  # Use 'a' (append mode) instead of 'w' (write mode)
        f.write(f"Aadhaar Number: {aadhaar_number}\n")
        f.write(f"Name: {name}\n")
        f.write(f"Mobile Number: {mobile_number}\n")
        f.write(f"Image Path: {image_path}\n\n")  # Add new line for separation

    print(f"Aadhaar details saved: {details_file}")

# Function to handle UI for entering Aadhaar details, mobile number, and OTP
def enter_aadhaar_details():
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window

    aadhaar_number = simpledialog.askstring("Enter Aadhaar Number", "Enter your Aadhaar number:")
    if aadhaar_number:
        name = simpledialog.askstring("Enter Name", "Enter your full name:")
        if name:
            mobile_number = simpledialog.askstring("Enter Mobile Number", "Enter your Registered mobile number:")
            if mobile_number:
                otp = simpledialog.askstring("Enter OTP", "Enter OTP received on your mobile:")

                if otp:
                    # Call function to capture image
                    image_folder = "aadhar_images"
                    image_path = capture_image(image_folder)

                    if image_path:
                        # Save Aadhaar details locally
                        save_aadhaar_details(aadhaar_number, name, mobile_number, image_path)

                        # Authenticate Aadhaar using UIDAI API
                        authentication_result = authenticate_aadhaar(aadhaar_number, name, image_path, mobile_number, otp)

                        if authentication_result:
                            messagebox.showinfo("Success", "Aadhaar authentication successful!")
                            print(f"Aadhaar Number: {aadhaar_number}")
                            print(f"Name: {name}")
                            print(f"Image Path: {image_path}")
                        else:
                            messagebox.showerror("Error", "Aadhaar authentication failed. Please try again.")
                    else:
                        messagebox.showerror("Error", "Failed to capture image.")
            else:
                messagebox.showwarning("Warning", "Mobile number not entered.")
        else:
            messagebox.showwarning("Warning", "Name not entered.")
    else:
        messagebox.showwarning("Warning", "Aadhaar number not entered.")

    root.destroy()  # Close the hidden tkinter window after interaction

# Main entry point of the program
if __name__ == "__main__":
    enter_aadhaar_details()




