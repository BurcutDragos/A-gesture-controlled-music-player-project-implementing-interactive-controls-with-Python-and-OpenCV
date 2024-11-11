# GestureMusicPlayer
<b>GestureMusicPlayer</b> is an interactive music player that allows users to control playback features using hand gestures, implemented in <b>Python</b> with <b>OpenCV</b> and <b>Mediapipe</b>. This project provides a unique way to manage music playback by leveraging gesture recognition, along with traditional mouse and keyboard controls, making it an engaging and accessible multimedia experience.

## Features:
* <b>Gesture-Controlled Playback:</b> The application recognizes a variety of hand gestures to perform common music playback operations:
     * <b>Play/Pause:</b> Start or pause music playback with a "Play" or "Pause" gesture.
     * <b>Next/Previous Track:</b> Skip to the next or previous track using hand gestures.
     * <b>Volume Adjustment:</b> Raise or lower volume with "Volume Up" or "Volume Down" gestures.
     * <b>Repeat and Stop Functions:</b> Easily repeat the current song or stop playback using gestures.
     * <b>Exit Application:</b> The "Rock and Roll" gesture will close the application.
* <b>Keyboard and Mouse Compatibility:</b> For added flexibility, all playback functions are also accessible via keyboard shortcuts and mouse controls:
     * <b>Keyboard Controls:</b>
          * <b>Spacebar key:</b> Play/Pause.
          * <b>Up and Down Arrow Keys:</b> Volume Up/Down.
          * <b>A/D keys:</b> Previous/Next track.
          * <b>Enter key:</b> Toggle Repeat.
          * <b>Delete key:</b> Stop Playback.
     * <b>Mouse Controls:</b> All controls are interactable with the mouse, allowing easy access to Play/Pause, Volume Up/Down, Next, Previous, and Repeat buttons.
* <b>Automated Track Management:</b>
     * <b>Auto Progression:</b> Automatically plays the next track when the current song finishes.
     * <b>Repeat Mode:</b> Option to repeat the current track.

## Getting Started:
### Prerequisites:
Ensure you have Python 3.11 or 3.12 installed. You will also need to install the following libraries:
* <b>OpenCV:</b> pip install opencv-python
* <b>Pygame:</b> pip install pygame
* <b>Mediapipe:</b> pip install mediapipe
* <b>Mutagen:</b> pip install mutagen
* <b>Tkinter:</b> pip install tkinter
* <b>Time:</b> pip install time
* <b>OS:</b> pip install os-sys
* <b>TensorFlow:</b> pip install tensorflow
* <b>NumPy:</b> pip install numpy

### Installation:
<b>1. Clone the Repository:</b>
git clone https://github.com/BurcutDragos/A-gesture-controlled-music-player-project-implementing-interactive-controls-with-Python-and-OpenCV.git

<b>2. Navigate to the Project Directory:</b>
cd A-gesture-controlled-music-player-project-implementing-interactive-controls-with-Python-and-OpenCV

<b>3. Install Dependencies:</b>
pip install -r requirements.txt

<b>4. Organize Music Files: </b>
Place your .mp3 music files in the Songs folder within the project directory. The naming format should ideally be "Artist - Title.mp3" for proper labeling within the interface. Files without this format will default to "Unknown - [Filename]".

### Running the Application:
Start the application by running: python music_player.py

## Usage Instructions:
* <b>Activate Gesture Control:</b> Click the "Enable Gesture Control" button to start controlling the player with gestures. The camera will automatically activate to recognize hand gestures.
* <b>Gesture Controls:</b>
    * Show a "Thumb Up" gesture to repeat the current song.
    * Make a "Victory" sign to stop the current song.
    * <b>Note:</b> To use gesture control effectively, maintain proper lighting and adjust hand positions as needed for accurate recognition.

## Project Structure:
* <b>gesture_model.h5:</b> This file is the saved gesture recognition model in HDF5 format, which is specific to TensorFlow and Keras. The .h5 file contains the model's architecture, trained weights, and configuration, enabling quick loading and use of the model in TensorFlow/Keras-based projects. This format is particularly useful for development, testing, and updating the model in environments that support TensorFlow.
* <b>gesture_model.onnx:</b> This file represents the same gesture recognition neural network saved in the ONNX (Open Neural Network Exchange) format. ONNX is an open standard that allows the model to be used across various frameworks (such as PyTorch, Caffe2, and other compatible libraries). This format makes the model more portable and interoperable, enabling deployment across a broader range of applications and platforms.
* <b>gesture_collector.py:</b> collects gesture data through the video camera. Using Mediapipe for hand detection, it captures hand landmarks and saves them as .npy files. The collected data is later used to train the gesture recognition model, enabling accurate gesture identification.
* <b>gesture_model.py:</b> defines the neural network model used for gesture recognition. It loads the previously saved gesture data, prepares it for training, and creates a model that can classify different gestures based on hand landmarks. The trained model is then saved for later use in the gesture recognition application.
* <b>gesture_recognizer.py:</b> Defines the gesture recognition logic, utilizing the camera and Mediapipe's hand landmark detection.
* <b>music_player.py:</b> Core file containing the music player functionality.
* <b>Songs/:</b> Folder where all playable music files are stored.
* <b>gestures/:</b> The gestures folder stores the captured gesture data as .npy files, where each file represents the hand landmarks (coordinates of reference points) for a specific gesture. These files are essential for training the gesture recognition model, enabling it to learn the unique characteristics of each gestures.
* <b>requirements.txt:</b> Contains all required Python libraries for easy setup.

## Future Enhancements:
* Adding more customizable gesture options.
* Support for different media formats (e.g., .wav, .flac).
* Implementing improved error handling and user feedback.

## License:
This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## Authors: 
Burcut Ioan Dragos, Burcut Vasile Cezar.
