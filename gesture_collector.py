import cv2 # OpenCV library for capturing and processing video images.
import mediapipe as mp # Mediapipe library for hand detection and tracking.
import os # Library for interacting with the file system.
import numpy as np # The library for manipulating numerical data (arrays).

# The main function for collecting gesture data.
def collect_gesture_data():
    # We initialize the Hands solution in Mediapipe for hand detection and tracking.
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

    # We initialize the drawing functionality in Mediapipe for viewing the hand points.
    mp_drawing = mp.solutions.drawing_utils

    # The list of gestures we want to collect.
    gestures = ['Play', 'Pause', 'Next', 'Previous', 'Volume Up', 'Volume Down', 'Victory', 'Thumb Up', 'Rock and Roll']

    # Iterate through each gesture to start capturing.
    for gesture in gestures:
        # User instruction message.
        print(
            f"Collecting data for gesture '{gesture}'. Press 'c' to start capture, 'q' to move to next gesture.")

        while True:
            # We are waiting for input from the user.
            key = input().lower()
            if key == 'c':
                # We start collecting data for a single gesture.
                if collect_single_gesture(gesture, hands, mp_drawing):
                    break # We exit the current loop after the data has been collected.
            elif key == 'q':
                # Next gesture message.
                print(f"Go to next gesture.")
                break
            else:
                # Error message if key pressed is not valid.
                print("Invalid key. Press 'c' to start or 'q' to move to the next gesture.")

    # Message when data collection is complete for all gestures.
    print("Gesture collection completed.")

# Function to collect data for one specific gesture.
def collect_single_gesture(gesture, hands, mp_drawing):
    # We open the web camera to capture images.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Error message if the camera cannot be accessed.
        print("The webcam could not be accessed.")
        return False

    frame_count = 0 # We initialize the number of captured frames.
    max_frames = 2000  # We set the maximum number of frames we want to capture for a gesture.

    while frame_count < max_frames:
        # We read a frame from the web camera.
        ret, frame = cap.read()
        if not ret:
            # Error message if we can't read the frame.
            print("Error reading frame.")
            break

        # We convert the frame from BGR (OpenCV format) to RGB (format used by Mediapipe).
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)  # We process the frame to detect hands.

        if results.multi_hand_landmarks:
            # Iterate through each detected hand and draw the reference points on the video frame.
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

            # Saves current gesture data based on detected reference points.
            save_gesture_data(gesture, results.multi_hand_landmarks, frame_count)
            frame_count += 1  # Increases the number of captured frames.

        # Displays the text with the name of the gesture and the number of frames captured on the video screen.
        cv2.putText(frame, f"{gesture}: {frame_count}/{max_frames}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                    2)
        # Displays the video frame in the "Camera" window.
        cv2.imshow("Camera", frame)

        # We exit the capture loop if the user presses the 'q' key.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # We close the capture stream and the video window.
    cap.release()
    cv2.destroyAllWindows()
    # Capture completion message for the current gesture.
    print(f"Capture of gesture '{gesture}' completed.")
    return True  # We return True to indicate capture success.

# Function to save gesture data.
def save_gesture_data(gesture, hand_landmarks_list, frame_count):
    # We check if the directory 'gestures' exists; if not, we create it.
    if not os.path.exists('gestures'):
        os.makedirs('gestures')

    # We create a subdirectory for each gesture, if it doesn't already exist.
    gesture_dir = os.path.join('gestures', gesture)
    if not os.path.exists(gesture_dir):
        os.makedirs(gesture_dir)

    # Iterate through each detected hand (can be 1 or 2 hands).
    for i, hand_landmarks in enumerate(hand_landmarks_list):
        # We convert the reference points of the hand into an array of (x, y, z) coordinates.
        landmarks_array = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]).flatten()
        # We create a unique file name for each captured frame and hand.
        file_name = f"{gesture}_hand{i + 1}_{frame_count}.npy"
        # We generate the full path for the file.
        file_path = os.path.join(gesture_dir, file_name)
        # We save the coordinate array in a .npy file (NumPy format).
        np.save(file_path, landmarks_array)

# The main block of the script; we initialize gesture data collection when the script is run.
if __name__ == "__main__":
    collect_gesture_data()  # We call the main function to collect the data.
