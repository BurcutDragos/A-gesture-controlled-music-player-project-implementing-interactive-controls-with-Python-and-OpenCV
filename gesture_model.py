import os # Library for interacting with the file system.
import numpy as np # Library for manipulating numerical data (arrays).
import tensorflow as tf # TensorFlow library for building and training neural networks.
from tensorflow.keras import layers, models # Import layers and models from Keras, which is part of TensorFlow.

# Function for loading gesture data.
def load_gesture_data():
    gestures_dir = "gestures"  # The folder where gesture data is stored.
    if not os.path.exists(gestures_dir):  # Checks if the 'gestures' folder exists.
        print(f"Error: The folder '{gestures_dir}' does not exists.")  # Error message if the folder does not exist.
        return None, None, None  # Returns None if the folder does not exist.

    # List of desired gestures to be loaded.
    desired_gestures = ['Play', 'Pause', 'Next', 'Previous', 'Volume Up', 'Volume Down', 'Victory', 'Thumb Up',
                        'Rock and Roll']

    images = []  # List to store gesture images/landmarks.
    labels = []  # List to store tags associated with gestures.
    gestures = []  # List to store the actual gestures (their names).

    # Iterates through each desired gesture and load the corresponding .npy files.
    for label, gesture in enumerate(desired_gestures):
        gesture_dir = os.path.join(gestures_dir, gesture)  # Creates the folder path for each gesture.
        if not os.path.isdir(gesture_dir):  # Checks if the directory for the gesture exists.
            print(f"Warning: Folder for gesture '{gesture}' does not exist.")  # Displays a warning if it doesn't exist.
            continue  # Go to the next gesture if the directory does not exist.

        gesture_files = os.listdir(gesture_dir)  # We list the files in the current gesture directory.
        if not gesture_files:  # Checks for files in the directory.
            print(f"Warning: No files found for gesture '{gesture}'.")  # Displays a warning if there are no files.
            continue  # Go to the next gesture if there are no files.

        gestures.append(gesture)  # Adds the gesture to the list of gestures.
        for file_name in gesture_files:  # Iterates through the files in the current gesture directory.
            file_path = os.path.join(gesture_dir, file_name)  # Creates the full path to the file.
            if file_name.endswith('.npy'):  # Checks if the file is of type .npy (NumPy file).
                landmarks = np.load(file_path)  # Loads the data from the .npy file.
                images.append(landmarks)  # Adds landmarks to the list of images.
                labels.append(label)  # Adds the tag (gesture index) to the tag list.
            else:
                print(f"Warning: File '{file_name}' is not of type .npy and will be ignored.")  # Displays warning if file is not .npy.

    if not images:  # Checks if no images have been uploaded.
        print("Error: Could not load data for any gesture.")  # Error message if no images found.
        return None, None, None  # Returns None if no images have been loaded.

    images = np.array(images)  # Converts the list of images to a NumPy array.
    labels = np.array(labels)  # Converts the list of tags to a NumPy array.

    return images, labels, gestures  # Returns images, tags, and gestures.

# The function for training the gesture recognition model.
def train_model():
    images, labels, gestures = load_gesture_data()  # Loads gesture data.
    if images is None or labels is None or gestures is None:  # Checks if the data has been loaded correctly.
        print("Model training failed due to missing data.")  # Displays a message if data is missing.
        return  # Exit function if data is missing.

    # Displays information about uploaded data.
    print(f"Form of input data: {images.shape}")  # Displays the shape of the input data (images).
    print(f"Form of labels: {labels.shape}")  # Shows the shape of the labels.
    print(f"Number of gestures: {len(gestures)}")  # Shows the number of gestures loaded.
    print(f"Gestures included: {gestures}")  # Shows the list of included gestures.

    # Defining the architecture of the neural model.
    model = models.Sequential([
        layers.Input(shape=(63,)),  # Defines the input of 63 values ​​(21 reference points for each x, y, z dimension).
        layers.Dense(128, activation='relu'),  # The first dense layer with 128 neurons and the ReLU activation function.
        layers.Dropout(0.3),  # 30% dropout layer to prevent overfitting.
        layers.Dense(64, activation='relu'),  # The second dense layer with 64 neurons and the ReLU activation function.
        layers.Dropout(0.3),  # 30% dropout layer to prevent overfitting.
        layers.Dense(len(gestures), activation='softmax')  # Output layer with gesture counts and Softmax activation for classification.
    ])

    # Compiles the model with the Adam optimizer and the 'sparse_categorical_crossentropy' loss function.
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])  # Shows accuracy as an evaluation metric.

    # Displays the model architecture summary.
    model.summary()

    # Train the model using the loaded data.
    model.fit(images, labels, epochs=50, validation_split=0.2, batch_size=32)  # Training on 50 epochs with 20% validation data and batch-size of 32.

    # Saves the trained model to a .h5 file.
    model.save("gesture_model.h5")  # Saves the model to an h5 file.
    print("The model has been trained and saved as 'gesture_model.h5'.")  # Shows the model save success message.

# Checks if this script is run directly.
if __name__ == "__main__":
    train_model()  # Calls the function to train the model.
