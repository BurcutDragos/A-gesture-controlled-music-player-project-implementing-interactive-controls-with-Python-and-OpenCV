import cv2  # OpenCV library for capturing and processing video images.
import tensorflow as tf  # TensorFlow library for using machine learning model.
import numpy as np  # The library for manipulating numerical data (arrays).
import mediapipe as mp  # Mediapipe library for hand detection and tracking.

# Load the gesture recognition model only once for efficiency.
model = tf.keras.models.load_model("gesture_model.h5")
# Initializes Mediapipe's Hands solution for hand detection and tracking.
mp_hands = mp.solutions.hands
# Configures parameters for hand detection: dynamic mode, maximum number of hands, and minimum confidence for detection and tracking.
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7,
                       min_tracking_confidence=0.5)
# The list of gestures recognized by the model, corresponding to the labels in the model.
gestures = ['Play', 'Pause', 'Next', 'Previous', 'Volume Up', 'Volume Down', 'Victory', 'Thumb Up', 'Rock and Roll']

# The function for recognizing gestures in a video frame.
def recognize_gesture(frame):
    # Converts the frame from BGR (OpenCV) format to RGB (Mediapipe) format for processing.
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Processes the RGB frame to detect hands and their landmarks.
    results = hands.process(frame_rgb)

    # Checks if hand landmarks have been detected.
    if results.multi_hand_landmarks:
        # Iterates through each detected hand.
        for hand_landmarks in results.multi_hand_landmarks:
            # Converts hand landmarks to an array of x, y, and z coordinates.
            landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]).flatten()
            # Reshapes to fit model input (1 row and all coordinates).
            processed_landmarks = landmarks.reshape(1, -1)

            # Makes the prediction using the loaded model without showing additional details.
            predictions = model.predict(processed_landmarks, verbose=0)
            # Determines the class (gesture) with the highest probability.
            predicted_class = np.argmax(predictions)
            # Gets the maximum likelihood (confidence) associated with the prediction.
            confidence = np.max(predictions)

            # Returns the name of the recognized gesture and confidence in the prediction.
            gesture_name = gestures[predicted_class]
            return gesture_name, confidence

    # If no hands were detected, we return None and a confidence of 0.
    return None, 0.0

# The function for detecting motion between two consecutive frames.
def detect_motion(frame1, frame2):
    # Calculates the absolute difference between the two frames.
    diff = cv2.absdiff(frame1, frame2)
    # Converts the difference frame to gray for easier processing.
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    # Applies a Gaussian blur to reduce image noise.
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Applies a threshold operation to obtain a binary (black and white) image.
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    # Returns True value if the sum of white pixels in the binary image exceeds a threshold, indicating significant motion.
    return np.sum(thresh) > 10000  # The threshold can be adjusted according to the desired sensitivity.

# The main block for running the gesture recognition application.
if __name__ == "__main__":
    # Opens the webcam for capturing video images.
    cap = cv2.VideoCapture(0)
    prev_frame = None  # Initializes the variable to store the previous frame.
    while True:
        # Reads a new frame from the webcam.
        ret, frame = cap.read()
        if not ret:  # If we can't read the frame, we exit the loop.
            break

        # It resizes the frame to reduce resource consumption and speed up processing.
        frame = cv2.resize(frame, (320, 240))

        # If there is a previous frame and no significant motion is detected, we continue to the next frame.
        if prev_frame is not None and not detect_motion(frame, prev_frame):
            prev_frame = frame  # Updates the previous frame with the current frame.
            continue  # Skips the rest of the loop if no motion is detected.

        # Recognizes the gesture in the current frame.
        gesture, confidence = recognize_gesture(frame)
        if gesture:  # If a gesture has been recognized.
            # Displays the gesture name and prediction confidence on the video frame.
            cv2.putText(frame, f"Gesture: {gesture} ({confidence:.2f})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0), 2)

        # Displays the video frame in the "Gesture Recognition" window.
        cv2.imshow("Gesture Recognition", frame)
        prev_frame = frame  # Updates the previous frame with the current frame.

        # Checks if the user presses the 'q' key to exit the loop.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Closes the room and all open windows.
    cap.release()
    cv2.destroyAllWindows()
