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
        print(f"Executing gesture: {gesture}")  # Afișăm gestul recunoscut în consolă.
        current_time = time.time()  # Timpul curent.
        if gesture == 'Play':  # Dacă gestul este Play.
            if not self.is_playing:  # Dacă muzica nu este redată.
                self.simulate_button_press(self.buttons["▶"])  # Simulăm apăsarea butonului Play.
                self.play_pause()  # Pornim redarea.
        elif gesture == 'Pause':  # Dacă gestul este Pause.
            if self.is_playing:  # Dacă muzica este redată.
                self.simulate_button_press(self.buttons["▶"])  # Simulăm apăsarea butonului Pause.
                self.play_pause()  # Punem pauză.
        elif gesture == 'Next':  # Dacă gestul este Next.
            self.simulate_button_press(self.buttons["⏭"])  # Simulăm apăsarea butonului Next.
            self.next()  # Trecem la melodia următoare.
        elif gesture == 'Previous':  # Dacă gestul este Previous.
            self.simulate_button_press(self.buttons["⏮"])  # Simulăm apăsarea butonului Previous.
            self.previous()  # Trecem la melodia precedentă.
        elif gesture == 'Volume Up':  # Dacă gestul este pentru mărirea volumului.
            self.adjust_volume(5)  # Mărim volumul cu 5 unități.
        elif gesture == 'Volume Down':  # Dacă gestul este pentru micșorarea volumului.
            self.adjust_volume(-5)  # Micșorăm volumul cu 5 unități.
        elif gesture == 'Thumb Up':  # Dacă gestul este Thumb Up.
            if current_time - self.last_repeat_time > self.repeat_cooldown:  # Verificăm dacă cooldown-ul pentru Repeat a expirat.
                self.simulate_button_press(self.buttons["🔁"])  # Simulăm apăsarea butonului Repeat.
                self.toggle_repeat()  # Activăm/Dezactivăm modul Repeat.
                self.last_repeat_time = current_time  # Actualizăm timpul ultimei activări a Repeat.
        elif gesture == 'Victory':  # Dacă gestul este Victory.
            self.simulate_button_press(self.buttons["⏹"])  # Simulăm apăsarea butonului Stop.
            self.stop()  # Oprim redarea muzicii.
        elif gesture == 'Rock and Roll':  # Dacă gestul este Rock and Roll.
            print("Rock and Roll gesture detected. Closing application.")  # Afișăm mesajul și închidem aplicația.
            self.master.after(0, self.master.quit)  # Ieșim din aplicație.

    # Funcție pentru simularea apăsării unui buton din interfață.
    def simulate_button_press(self, button):
        if button == self.buttons["🔁"]:  # Nu simulăm apăsarea pentru butonul Repeat, deoarece își schimbă starea.
            return
        original_color = button.cget('bg')  # Salvăm culoarea originală a butonului.
        button.config(bg='#a0a0a0')  # Schimbăm culoarea butonului pentru a simula apăsarea.
        self.master.after(100, lambda: button.config(bg=original_color))  # Revenim la culoarea originală după 100ms.

    # Funcție pentru obținerea listei de melodii din directorul Songs.
    def get_songs(self):
        songs_dir = os.path.join(os.path.dirname(__file__), 'Songs')  # Directorul în care se află melodiile.
        if not os.path.exists(songs_dir):  # Verificăm dacă directorul există.
            print(f"Directory not found: {songs_dir}")  # Afișăm mesaj de eroare dacă directorul nu există.
            return []  # Returnăm o listă goală dacă directorul nu există.
        songs = sorted([f for f in os.listdir(songs_dir) if f.endswith('.mp3')])  # Filtrăm și sortăm fișierele MP3.
        return songs  # Returnăm lista de melodii.

    # Funcție pentru încărcarea unei melodii.
    def load_song(self):
        if not self.songs:  # Verificăm dacă există melodii în listă.
            self.current_time_label.config(text="No songs")  # Afișăm mesajul dacă nu există melodii.
            return

        song_path = os.path.join(os.path.dirname(__file__), 'Songs', self.songs[self.current_song_index])  # Calea către melodia curentă.
        pygame.mixer.music.load(song_path)  # Încărcăm melodia în player.
        audio = MP3(song_path)  # Obținem informații despre melodia MP3 folosind mutagen.
        self.song_length = audio.info.length  # Stocăm durata totală a melodiei.
        self.total_time_label.config(text=self.format_time(self.song_length))  # Afișăm durata totală a melodiei.

        song_file = os.path.basename(song_path)  # Obținem numele fișierului melodiei.
        if '-' in song_file:  # Dacă numele fișierului conține caracterul '-'.
            artist, title = song_file.rsplit('-', 1)  # Împărțim numele fișierului în artist și titlu.
            title = title.rsplit('.', 1)[0]  # Eliminăm extensia fișierului.
            song_info = f"{artist.strip()} - {title.strip()}"  # Formatăm informațiile despre artist și titlu.
        else:
            artist = "Unknown"  # Setăm artistul ca necunoscut dacă nu există separatorul '-'.
            title = song_file.rsplit('.', 1)[0]  # Folosim numele fișierului ca titlu.
            song_info = f"{artist.strip()} - {title.strip()}"  # Formatăm informațiile.

        self.song_info_label.config(text=song_info)  # Afișăm informațiile despre melodia curentă.

    # Funcție pentru a porni sau opri redarea muzicii.
    def play_pause(self):
        if not self.songs:  # Dacă nu există melodii, ieșim din funcție.
            return
        if self.is_playing:  # Dacă muzica este redată, oprim redarea (pauză).
            pygame.mixer.music.pause()  # Punem pauză la melodia curentă.
            self.buttons["▶"].config(text="▶")  # Schimbăm textul butonului la Play.
            self.is_playing = False  # Setăm starea de redare pe False.
        else:  # Dacă muzica nu este redată.
            if pygame.mixer.music.get_pos() == -1:  # Dacă melodia nu a început niciodată.
                pygame.mixer.music.play(start=self.current_time)  # Redăm melodia de la timpul curent.
            else:
                pygame.mixer.music.unpause()  # Reluăm redarea melodiei.
            self.buttons["▶"].config(text="⏸")  # Schimbăm textul butonului la Pause.
            self.is_playing = True  # Setăm starea de redare pe True.

    # Funcție pentru oprirea redării muzicii.
    def stop(self):
        pygame.mixer.music.stop()  # Oprim redarea muzicii.
        self.is_playing = False  # Setăm starea de redare pe False.
        self.current_time = 0  # Resetăm timpul curent la 0.
        self.buttons["▶"].config(text="▶")  # Schimbăm textul butonului la Play.
        self.current_time_label.config(text="00:00")  # Resetăm eticheta timpului curent.
        self.update_progress_bar(0)  # Resetăm bara de progres.

    # Funcție pentru a trece la melodia precedentă.
    def previous(self):
        if not self.songs:  # Dacă nu există melodii, ieșim din funcție.
            return
        self.current_song_index = (self.current_song_index - 1) % len(self.songs)  # Trecem la melodia precedentă în listă.
        self.load_song()  # Încărcăm melodia.
        self.current_time = 0  # Resetăm timpul curent la 0.
        if self.is_playing:  # Dacă muzica este redată.
            pygame.mixer.music.play()  # Redăm melodia.

    # Funcție pentru a trece la melodia următoare.
    def next(self):
        if not self.songs:  # Dacă nu există melodii, ieșim din funcție.
            return
        self.current_song_index = (self.current_song_index + 1) % len(self.songs)  # Trecem la melodia următoare în listă.
        self.load_song()  # Încărcăm melodia.
        self.current_time = 0  # Resetăm timpul curent la 0.
        if self.is_playing:  # Dacă muzica este redată.
            pygame.mixer.music.play()  # Redăm melodia.

    # Funcție pentru activarea/dezactivarea modului Repeat.
    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat  # Comutăm starea Repeat (activat/dezactivat).
        if self.is_repeat:  # Dacă Repeat este activat.
            self.buttons["🔁"].config(bg=self.repeat_active_color)  # Schimbăm culoarea butonului Repeat la activat.
            self.buttons["🔁"].unbind("<Enter>")  # Dezactivăm efectul hover pentru butonul Repeat.
            self.buttons["🔁"].unbind("<Leave>")  # Dezactivăm efectul hover pentru butonul Repeat.
        else:  # Dacă Repeat este dezactivat.
            self.buttons["🔁"].config(bg=self.repeat_inactive_color)  # Schimbăm culoarea butonului Repeat la dezactivat.
            self.buttons["🔁"].bind("<Enter>", lambda e: self.on_hover(self.buttons["🔁"]))  # Reactivăm efectul hover.
            self.buttons["🔁"].bind("<Leave>", lambda e: self.on_leave(self.buttons["🔁"]))  # Reactivăm efectul hover.
        print(f"Repeat mode: {'On' if self.is_repeat else 'Off'}")  # Afișăm starea Repeat în consolă.

    # Funcție pentru verificarea sfârșitului melodiei curente.
    def check_end(self):
        if self.is_playing:  # Dacă muzica este redată.
            if not pygame.mixer.music.get_busy():  # Dacă melodia s-a terminat.
                if self.is_repeat:  # Dacă modul Repeat este activat.
                    pygame.mixer.music.play()  # Redăm melodia din nou.
                    self.current_time = 0  # Resetăm timpul curent la 0.
                else:
                    self.next()  # Trecem la melodia următoare.
        self.master.after(500, self.check_end)  # Verificăm din nou peste 500 ms.

    # Funcție pentru actualizarea timpului curent și a barei de progres.
    def update_time(self):
        if self.is_playing:  # Dacă muzica este redată.
            self.current_time = pygame.mixer.music.get_pos() / 1000  # Obținem timpul curent al melodiei.
            if self.current_time >= 0:  # Dacă timpul curent este valid.
                self.current_time_label.config(text=self.format_time(self.current_time))  # Afișăm timpul curent.
                self.update_progress_bar(self.current_time)  # Actualizăm bara de progres.
        self.master.after(100, self.update_time)  # Actualizăm din nou după 100 ms.

    # Funcție pentru actualizarea barei de progres în funcție de timpul curent.
    def update_progress_bar(self, current_time):
        if self.song_length > 0:  # Dacă durata melodiei este validă.
            progress_ratio = current_time / self.song_length  # Calculăm procentajul de progres.
            progress_width = progress_ratio * self.progress_canvas.winfo_width()  # Calculăm lățimea barei de progres.
            self.progress_canvas.coords(self.progress_bar, 0, 0, progress_width, 10)  # Actualizăm bara de progres.

    # Funcție pentru setarea volumului.
    def set_volume(self, value):
        volume = float(value) / 100  # Convertim valoarea volumului într-o proporție (între 0 și 1).
        pygame.mixer.music.set_volume(volume)  # Setăm volumul playerului.

    # Funcție pentru ajustarea volumului cu o valoare dată.
    def adjust_volume(self, step):
        current_volume = self.volume_slider.get()  # Obținem volumul curent.
        new_volume = max(0, min(100, current_volume + step))  # Calculăm noul volum (între 0 și 100).
        self.volume_slider.set(new_volume)  # Setăm noul volum pe slider.
        self.set_volume(new_volume)  # Setăm volumul playerului.

    # Funcție pentru formatarea timpului în minute și secunde.
    def format_time(self, seconds):
        return time.strftime('%M:%S', time.gmtime(seconds))  # Convertim timpul în format MM:SS.

    # Funcție pentru efectul hover când un buton este apăsat.
    def on_hover(self, button):
        if button != self.buttons["🔁"] or not self.is_repeat:  # Dacă butonul nu este Repeat sau Repeat este dezactivat.
            button.config(bg='#cccccc')  # Schimbăm culoarea butonului la hover.

    # Funcție pentru efectul de retragere a hover-ului când butonul nu mai este apăsat.
    def on_leave(self, button):
        if button != self.buttons["🔁"] or not self.is_repeat:  # Dacă butonul nu este Repeat sau Repeat este dezactivat.
            button.config(bg=self.repeat_inactive_color)  # Revenim la culoarea inactivă.
        else:  # Dacă Repeat este activat.
            button.config(bg=self.repeat_active_color)  # Menținem culoarea activă.

# Inițializăm fereastra principală și playerul de muzică.
if __name__ == "__main__":
    root = tk.Tk()  # Creăm fereastra principală.
    player = MusicPlayer(root)  # Inițializăm playerul de muzică.
    root.mainloop()  # Pornim bucla principală a interfeței grafice.
