import tkinter as tk  # The library for building the GUI.
from tkinter import ttk  # Extension for advanced widgets in tkinter.
import pygame  # Library for playing sounds and music.
import os  # Library for interacting with the file system.
from mutagen.mp3 import MP3  # Library for manipulating MP3 files and getting information about them.
import time  # Time management library.
import cv2  # Library for capturing and manipulating video images.
import threading  # The library for managing threads.
from gesture_recognizer import recognize_gesture, detect_motion  # Features for gesture recognition and motion detection.

# The class for the music player.
class MusicPlayer:
    def __init__(self, master):
        self.master = master  # Reference to main window.
        self.master.title("Music Player")  # The title of the window.
        self.master.geometry("400x400")  # The size of the window.
        self.master.minsize(400, 400)  # Minimum window size.

        pygame.mixer.init()  # Initializes the mixer for playing sounds.

        # Player state variables.
        self.is_playing = False  # Indicates whether music is playing.
        self.is_repeat = False  # Indicates whether Repeat mode is active.
        self.current_time = 0  # The current time of the song.
        self.song_length = 0  # Total duration of the song.
        self.current_song_index = 0  # Current song index.
        self.songs = self.get_songs()  # Gets the playlist.
        self.last_repeat_time = 0  # The time of the last press of the Repeat button.
        self.repeat_cooldown = 2  # Two second cooldown for Repeat button.
        self.repeat_active_color = '#a0a0a0'  # The color of the activated Repeat button.
        self.repeat_inactive_color = '#e0e0e0'  # The color of the disabled Repeat button.

        self.create_widgets()  # Creates the interface elements.

        if self.songs:  # If there are songs, we load the first song.
            self.load_song()

        self.gesture_control_active = False  # Indicates whether gesture control is active.
        self.gesture_thread = None  # The gesture thread is initialized to None value.
        # Button to activate gesture control.
        self.gesture_control_button = tk.Button(self.master, text="Activare control gestual",
                                                command=self.toggle_gesture_control)
        self.gesture_control_button.pack(pady=10)  # Shows the button in the interface.

        # It updates the time and checks the end of the song periodically.
        self.master.after(100, self.update_time)
        self.master.after(500, self.check_end)

    # Function for creating GUI elements.
    def create_widgets(self):
        # The label that displays the song information.
        self.song_info_label = tk.Label(self.master, text="", font=("Arial", 12))
        self.song_info_label.pack(pady=5)  # Shows the label in the interface.

        # Frame for current time and total time.
        self.time_frame = tk.Frame(self.master)
        self.time_frame.pack(fill='x', padx=20)  # Shows the frame in the interface.

        # Tag for the current time of the song.
        self.current_time_label = tk.Label(self.time_frame, text="00:00")
        self.current_time_label.pack(side='left')  # Shows the label on the left.

        # Tag for the total time of the song.
        self.total_time_label = tk.Label(self.time_frame, text="00:00")
        self.total_time_label.pack(side='right')  # Shows the label on the right.

        # Progress bar for song playback.
        self.progress_canvas = tk.Canvas(self.master, height=10, bg="white")
        self.progress_canvas.pack(fill='x', padx=20)  # Shows progress bar.
        # Creates a blue progress bar.
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill="#1E90FF")

        # Frame for control buttons (Play, Next, Previous, etc.).
        self.control_frame = tk.Frame(self.master)
        self.control_frame.pack(pady=20)  # Shows the button frame.

        # Defines the buttons and their actions.
        button_data = [
            ("⏮", self.previous, '#e0e0e0'),  # Previous button.
            ("▶", self.play_pause, '#e0e0e0'),  # Play/Pause button.
            ("⏹", self.stop, '#e0e0e0'),  # Stop button.
            ("⏭", self.next, '#e0e0e0'),  # Next button.
            ("🔁", self.toggle_repeat, '#e0e0e0')  # Repeat button.
        ]

        self.buttons = {}  # Dictionary for storing buttons.
        for symbol, command, color in button_data:
            # Creates each button and add it to the interface.
            btn = tk.Button(self.control_frame, text=symbol, command=command,
                            font=("Arial", 16), width=3, bg=color)
            btn.pack(side='left', padx=10)  # Shows the button in the interface.
            # Adds hover effects to buttons.
            btn.bind("<Enter>", lambda e, b=btn: self.on_hover(b))
            btn.bind("<Leave>", lambda e, b=btn: self.on_leave(b))
            self.buttons[symbol] = btn  # Stores the button in the dictionary.

        # Slider for volume control.
        self.volume_var = tk.IntVar()  # Variable to store the volume value.
        self.volume_slider = ttk.Scale(self.master, from_=0, to=100, orient='horizontal',
                                       variable=self.volume_var, command=self.set_volume)
        self.volume_slider.set(50)  # Sets the initial volume to 50%.
        self.volume_slider.pack(fill='x', padx=20, pady=20)  # Shows the slider in the interface.

        # Binds various functions to keys (Play/Pause, Previous, Next, etc.).
        self.master.bind('<space>', lambda e: self.play_pause())  # Play/Pause button.
        self.master.bind('a', lambda e: self.previous())  # Previous button.
        self.master.bind('d', lambda e: self.next())  # Next button.
        self.master.bind('<Up>', lambda e: self.adjust_volume(5))  # Increases the sound volume.
        self.master.bind('<Down>', lambda e: self.adjust_volume(-5))  # Decreases the sound volume.
        self.master.bind('<Return>', lambda e: self.toggle_repeat())  # Enable/Disable Repeat option.
        self.master.bind('<Delete>', lambda e: self.stop())  # Stop playback.

    # Feature to enable/disable gesture control.
    def toggle_gesture_control(self):
        if self.gesture_control_active:  # If gesture control is active.
            self.gesture_control_active = False  # Disables gesture control.
            self.gesture_control_button.config(text="Activate gesture control")  # Changes the button text.
            if self.gesture_thread:  # If there is a thread for gestures.
                self.gesture_thread.join(timeout=1.0)  # Waits for the thread to end.
        else:  # If gesture control is disabled.
            self.gesture_control_active = True  # Activate gesture control.
            self.gesture_control_button.config(text="Disable gesture control")  # Changes the button text.
            self.gesture_thread = threading.Thread(target=self.process_gestures, daemon=True)  # Creates the thread for processing gestures.
            self.gesture_thread.start()  # Starts the execution thread.

    # The function that processes gestures using the video camera.
    def process_gestures(self):
        cap = cv2.VideoCapture(0)  # Turn on the video camera.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Sets the width of the video frame.
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Sets the height of the video frame.

        last_gesture_time = time.time()  # The time of the last gesture processed.
        gesture_cooldown = 0.5  # 0.5 second cooldown between processing gestures.
        frame_interval = 0.1  # Interval between analyzed frames.
        prev_frame = None  # Previous framework for motion detection.

        while self.gesture_control_active:  # While gesture control is active.
            current_time = time.time()  # Current time.
            if current_time - last_gesture_time < frame_interval:  # Checks the interval between frames.
                time.sleep(0.01)  # Waits a little.
                continue  # Goes to the next frame.

            ret, frame = cap.read()  # Reads a frame from the video stream.
            if not ret:  # If it can't read the frame, it continues.
                continue

            frame = cv2.resize(frame, (160, 120))  # Resizes the video frame.

            if prev_frame is not None and not detect_motion(frame, prev_frame):  # Checks for motion between frames.
                prev_frame = frame  # Updates the previous frame.
                continue  # Goes to the next frame.

            gesture, confidence = recognize_gesture(frame)  # Recognizes the gesture in the frame.

            if gesture and confidence > 0.8 and (current_time - last_gesture_time) > gesture_cooldown:  # If the gesture is recognized with high confidence.
                last_gesture_time = current_time  # Updates the time of the last gesture.
                self.master.after(0, lambda g=gesture: self.execute_gesture_command(g))  # Executes the command associated with the gesture.

            prev_frame = frame  # Updates the previous frame.
            time.sleep(0.05)  # Waits before moving to the next frame.

        cap.release()  # Releases the video camera.

    # Function for executing the command associated with the recognized gesture.
    def execute_gesture_command(self, gesture):
        print(f"Executing gesture: {gesture}")  # Displays the recognized gesture in the console.
        current_time = time.time()  # Current time.
        if gesture == 'Play':  # If the gesture is Play.
            if not self.is_playing:  # If the music is not playing.
                self.simulate_button_press(self.buttons["▶"])  # Simulates pressing the Play button.
                self.play_pause()  # Starts playback.
        elif gesture == 'Pause':  # If the gesture is Pause.
            if self.is_playing:  # If the music is playing.
                self.simulate_button_press(self.buttons["▶"])  # Simulates pressing the Pause button.
                self.play_pause()  # Pause
        elif gesture == 'Next':  # If the gesture is Next.
            self.simulate_button_press(self.buttons["⏭"])  # Simulates pressing the Next button.
            self.next()  # Skips to next song.
        elif gesture == 'Previous':  # If the gesture is Previous.
            self.simulate_button_press(self.buttons["⏮"])  # Simulates pressing the Previous button.
            self.previous()  # Skips to the previous song.
        elif gesture == 'Volume Up':  # If the gesture is for volume up.
            self.adjust_volume(5)  # Increases the volume by 5 units.
        elif gesture == 'Volume Down':  # If the gesture is for volume down.
            self.adjust_volume(-5)  # Decreases the volume by 5 units.
        elif gesture == 'Thumb Up':  # If the gesture is Thumb Up.
            if current_time - self.last_repeat_time > self.repeat_cooldown:  # Checks if the cooldown for Repeat has expired.
                self.simulate_button_press(self.buttons["🔁"])  # Simulates pressing the Repeat button.
                self.toggle_repeat()  # Enable/Disable Repeat mode.
                self.last_repeat_time = current_time  # Updates the time of the last activation of Repeat.
        elif gesture == 'Victory':  # If the gesture is Victory.
            self.simulate_button_press(self.buttons["⏹"])  # Simulates pressing the Stop button.
            self.stop()  # Stops playing music.
        elif gesture == 'Rock and Roll':  # If the gesture is Rock and Roll.
            print("Rock and Roll gesture detected. Closing application.")  # Displays the message and closes the application.
            self.master.after(0, self.master.quit)  # Exits the application.

    # Function to simulate pressing a button in the interface.
    def simulate_button_press(self, button):
        if button == self.buttons["🔁"]:  # Pressing the Repeat button is not simulated, because it changes its state.
            return
        original_color = button.cget('bg')  # Saves the original color of the button.
        button.config(bg='#a0a0a0')  # Changes button color to simulate pressing.
        self.master.after(100, lambda: button.config(bg=original_color))  # Returns to original color after 100ms.

    # Function to get the list of songs from the Songs directory.
    def get_songs(self):
        songs_dir = os.path.join(os.path.dirname(__file__), 'Songs')  # The directory where the songs are located.
        if not os.path.exists(songs_dir):  # Checks if the directory exists.
            print(f"Directory not found: {songs_dir}")  # Displays an error message if the directory does not exist.
            return []  # Returns an empty list if the directory does not exist.
        songs = sorted([f for f in os.listdir(songs_dir) if f.endswith('.mp3')])  # Filters and sorts MP3 files.
        return songs  # Returns the list of songs.

    # Function to load a song.
    def load_song(self):
        if not self.songs:  # Checks if there are songs in the list.
            self.current_time_label.config(text="No songs")  # Displays the message if there are no songs.
            return

        song_path = os.path.join(os.path.dirname(__file__), 'Songs', self.songs[self.current_song_index])  # The path to the current song.
        pygame.mixer.music.load(song_path)  # Loads the song into the player.
        audio = MP3(song_path)  # Gets MP3 song information using mutagen.
        self.song_length = audio.info.length  # Stores the total duration of the song.
        self.total_time_label.config(text=self.format_time(self.song_length))  # Shows the total duration of the song.

        song_file = os.path.basename(song_path)  # Gets the file name of the song.
        if '-' in song_file:  # If the file name contains the character '-'.
            artist, title = song_file.rsplit('-', 1)  # Splits the filename into artist and title.
            title = title.rsplit('.', 1)[0]  # Removes the file extension.
            song_info = f"{artist.strip()} - {title.strip()}"  # Formats the artist and title information.
        else:
            artist = "Unknown"  # Sets the artist as unknown if there is no separator '-'.
            title = song_file.rsplit('.', 1)[0]  # Uses the filename as the title.
            song_info = f"{artist.strip()} - {title.strip()}"  # Formats the information.

        self.song_info_label.config(text=song_info)  # Displays information about the current song.

    # Function to start or stop playing music.
    def play_pause(self):
        if not self.songs:  # If there are no songs, the function is exited.
            return
        if self.is_playing:  # If the song is playing, it stops playing (pause).
            pygame.mixer.music.pause()  # Pauses the current song.
            self.buttons["▶"].config(text="▶")  # Changes the button text to Play.
            self.is_playing = False  # Sets the playback state to False.
        else:  # If the music is not playing.
            if pygame.mixer.music.get_pos() == -1:  # If the song never started.
                pygame.mixer.music.play(start=self.current_time)  # Plays the song from the current time.
            else:
                pygame.mixer.music.unpause()  # Plays the song again.
            self.buttons["▶"].config(text="⏸")  # Changes the button text to Pause.
            self.is_playing = True  # Sets the playback state to True.

    # Function to stop playing music.
    def stop(self):
        pygame.mixer.music.stop()  # Stops playing music.
        self.is_playing = False  # Sets the playback state to False.
        self.current_time = 0  # Resets the current time to 0.
        self.buttons["▶"].config(text="▶")  # Changes the button text to Play.
        self.current_time_label.config(text="00:00")  # Resets the current time label.
        self.update_progress_bar(0)  # Resets the progress bar.

    # Function to skip to the previous song.
    def previous(self):
        if not self.songs:  # If there are no songs, the function is exited.
            return
        self.current_song_index = (self.current_song_index - 1) % len(self.songs)  # Skips to the previous song in the list.
        self.load_song()  # Loads the song.
        self.current_time = 0  # Resets the current time to 0.
        if self.is_playing:  # If the song is playing.
            pygame.mixer.music.play()  # Plays the song.

    # Function to skip to the next song.
    def next(self):
        if not self.songs:  # If there are no songs, the function is exited.
            return
        self.current_song_index = (self.current_song_index + 1) % len(self.songs)  # Skips to the next song in the list.
        self.load_song()  # Loads the song.
        self.current_time = 0  # Resets the current time to 0.
        if self.is_playing:  # If the song is playing.
            pygame.mixer.music.play()  # Plays the song.

    # Function to enable/disable Repeat mode.
    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat  # Toggles Repeat state (on/off).
        if self.is_repeat:  # If Repeat is enabled.
            self.buttons["🔁"].config(bg=self.repeat_active_color)  # Changes the color of the Repeat button to on.
            self.buttons["🔁"].unbind("<Enter>")  # Disables the hover effect for the Repeat button.
            self.buttons["🔁"].unbind("<Leave>")  # Disables the hover effect for the Repeat button.
        else:  # If Repeat is disabled.
            self.buttons["🔁"].config(bg=self.repeat_inactive_color)  # Changes the color of the Repeat button when disabled.
            self.buttons["🔁"].bind("<Enter>", lambda e: self.on_hover(self.buttons["🔁"]))  # Reactivates the hover effect.
            self.buttons["🔁"].bind("<Leave>", lambda e: self.on_leave(self.buttons["🔁"]))  # Reactivates the hover effect.
        print(f"Repeat mode: {'On' if self.is_repeat else 'Off'}")  # Displays the Repeat status in the console.

    # Function to check the end of the current song.
    def check_end(self):
        if self.is_playing:  # If the song is playing.
            if not pygame.mixer.music.get_busy():  # If the song is over.
                if self.is_repeat:  # If Repeat mode is enabled.
                    pygame.mixer.music.play()  # Plays the song again.
                    self.current_time = 0  # Resets the current time to 0.
                else:
                    self.next()  # Skips to next song.
        self.master.after(500, self.check_end)  # Checks again over 500ms.

    # Function to update current time and progress bar.
    def update_time(self):
        if self.is_playing:  # If the song is playing.
            self.current_time = pygame.mixer.music.get_pos() / 1000  # Gets the current time of the song.
            if self.current_time >= 0:  # If the current time is valid.
                self.current_time_label.config(text=self.format_time(self.current_time))  # Displays the current time.
                self.update_progress_bar(self.current_time)  # Updates the progress bar.
        self.master.after(100, self.update_time)  # Refresh again after 100ms.

    # Function to update the progress bar according to the current time.
    def update_progress_bar(self, current_time):
        if self.song_length > 0:  # If the song duration is valid.
            progress_ratio = current_time / self.song_length  # Calculates the percentage of progress.
            progress_width = progress_ratio * self.progress_canvas.winfo_width()  # Calculates the width of the progress bar.
            self.progress_canvas.coords(self.progress_bar, 0, 0, progress_width, 10)  # Updates the progress bar.

    # Volume setting function.
    def set_volume(self, value):
        volume = float(value) / 100  # Converts the volume value to a proportion (between 0 and 1).
        pygame.mixer.music.set_volume(volume)  # Sets the volume of the player.

    # Function to adjust the volume by a given value.
    def adjust_volume(self, step):
        current_volume = self.volume_slider.get()  # Gets the current volume.
        new_volume = max(0, min(100, current_volume + step))  # Calculates the new volume (between 0 and 100).
        self.volume_slider.set(new_volume)  # Sets the new volume on the slider.
        self.set_volume(new_volume)  # Sets the volume of the player.

    # Function for formatting the time in minutes and seconds.
    def format_time(self, seconds):
        return time.strftime('%M:%S', time.gmtime(seconds))  # Converts time to MM:SS format.

    # Function for the hover effect when a button is pressed.
    def on_hover(self, button):
        if button != self.buttons["🔁"] or not self.is_repeat:  # If the button is not Repeat or Repeat is disabled.
            button.config(bg='#cccccc')  # Changes the color of the hover button.

    # Function for the hover retract effect when the button is no longer pressed.
    def on_leave(self, button):
        if button != self.buttons["🔁"] or not self.is_repeat:  # If the button is not Repeat or Repeat is disabled.
            button.config(bg=self.repeat_inactive_color)  # Returns to inactive color.
        else:  # If Repeat is enabled.
            button.config(bg=self.repeat_active_color)  # Keeps the active color.

# Initializes the main window and the music player.
if __name__ == "__main__":
    root = tk.Tk()  # Creates the main window.
    player = MusicPlayer(root)  # Initializes the music player.
    root.mainloop()  # Starts the main GUI loop.
