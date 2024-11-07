import tkinter as tk  # Biblioteca pentru construirea interfeței grafice.
from tkinter import ttk  # Extensie pentru widgeturi avansate în tkinter.
import pygame  # Biblioteca pentru redarea sunetelor și a muzicii.
import os  # Biblioteca pentru interacțiunea cu sistemul de fișiere.
from mutagen.mp3 import MP3  # Biblioteca pentru manipularea fișierelor MP3 și obținerea informațiilor despre acestea.
import time  # Biblioteca pentru gestionarea timpului.
import cv2  # Biblioteca pentru capturarea și manipularea imaginilor video.
import threading  # Biblioteca pentru gestionarea firelor de execuție.
from gesture_recognizer import recognize_gesture, detect_motion  # Funcții pentru recunoașterea gesturilor și detectarea mișcării.

# Clasa pentru playerul de muzică.
class MusicPlayer:
    def __init__(self, master):
        self.master = master  # Referință la fereastra principală.
        self.master.title("Music Player")  # Titlul ferestrei.
        self.master.geometry("400x400")  # Dimensiunea ferestrei.
        self.master.minsize(400, 400)  # Dimensiunea minimă a ferestrei.

        pygame.mixer.init()  # Inițializăm mixerul pentru redarea sunetelor.

        # Variabile de stare ale playerului.
        self.is_playing = False  # Indică dacă muzica este redată.
        self.is_repeat = False  # Indică dacă modul Repeat este activ.
        self.current_time = 0  # Timpul curent al melodiei.
        self.song_length = 0  # Durata totală a melodiei.
        self.current_song_index = 0  # Indexul melodiei curente.
        self.songs = self.get_songs()  # Obținem lista de melodii.
        self.last_repeat_time = 0  # Momentul ultimei apăsări a butonului Repeat.
        self.repeat_cooldown = 2  # Cooldown de 2 secunde pentru butonul Repeat.
        self.repeat_active_color = '#a0a0a0'  # Culoarea butonului Repeat activat.
        self.repeat_inactive_color = '#e0e0e0'  # Culoarea butonului Repeat dezactivat.

        self.create_widgets()  # Creăm elementele de interfață.

        if self.songs:  # Dacă există melodii, încărcăm prima melodie.
            self.load_song()

        self.gesture_control_active = False  # Indică dacă controlul prin gesturi este activ.
        self.gesture_thread = None  # Firul de execuție pentru gesturi este inițializat cu None.
        # Buton pentru activarea controlului prin gesturi.
        self.gesture_control_button = tk.Button(self.master, text="Activare control gestual",
                                                command=self.toggle_gesture_control)
        self.gesture_control_button.pack(pady=10)  # Afișăm butonul în interfață.

        # Actualizăm timpul și verificăm sfârșitul melodiei periodic.
        self.master.after(100, self.update_time)
        self.master.after(500, self.check_end)

    # Funcția pentru crearea elementelor de interfață grafică.
    def create_widgets(self):
        # Eticheta care afișează informațiile despre melodie.
        self.song_info_label = tk.Label(self.master, text="", font=("Arial", 12))
        self.song_info_label.pack(pady=5)  # Afișăm eticheta în interfață.

        # Cadru pentru timpul curent și timpul total.
        self.time_frame = tk.Frame(self.master)
        self.time_frame.pack(fill='x', padx=20)  # Afișăm cadrul în interfață.

        # Eticheta pentru timpul curent al melodiei.
        self.current_time_label = tk.Label(self.time_frame, text="00:00")
        self.current_time_label.pack(side='left')  # Afișăm eticheta în stânga.

        # Eticheta pentru timpul total al melodiei.
        self.total_time_label = tk.Label(self.time_frame, text="00:00")
        self.total_time_label.pack(side='right')  # Afișăm eticheta în dreapta.

        # Bara de progres pentru redarea melodiei.
        self.progress_canvas = tk.Canvas(self.master, height=10, bg="white")
        self.progress_canvas.pack(fill='x', padx=20)  # Afișăm bara de progres.
        # Creăm o bară de progres albastră.
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill="#1E90FF")

        # Cadru pentru butoanele de control (Play, Next, Previous, etc.).
        self.control_frame = tk.Frame(self.master)
        self.control_frame.pack(pady=20)  # Afișăm cadrul pentru butoane.

        # Definim butoanele și acțiunile lor.
        button_data = [
            ("⏮", self.previous, '#e0e0e0'),  # Buton Previous.
            ("▶", self.play_pause, '#e0e0e0'),  # Buton Play/Pause.
            ("⏹", self.stop, '#e0e0e0'),  # Buton Stop.
            ("⏭", self.next, '#e0e0e0'),  # Buton Next.
            ("🔁", self.toggle_repeat, '#e0e0e0')  # Buton Repeat.
        ]

        self.buttons = {}  # Dicționar pentru stocarea butoanelor.
        for symbol, command, color in button_data:
            # Creăm fiecare buton și îl adăugăm în interfață.
            btn = tk.Button(self.control_frame, text=symbol, command=command,
                            font=("Arial", 16), width=3, bg=color)
            btn.pack(side='left', padx=10)  # Afișăm butonul în interfață.
            # Adăugăm efecte hover la butoane.
            btn.bind("<Enter>", lambda e, b=btn: self.on_hover(b))
            btn.bind("<Leave>", lambda e, b=btn: self.on_leave(b))
            self.buttons[symbol] = btn  # Stocăm butonul în dicționar.

        # Slider pentru controlul volumului.
        self.volume_var = tk.IntVar()  # Variabilă pentru stocarea valorii volumului.
        self.volume_slider = ttk.Scale(self.master, from_=0, to=100, orient='horizontal',
                                       variable=self.volume_var, command=self.set_volume)
        self.volume_slider.set(50)  # Setăm volumul inițial la 50%.
        self.volume_slider.pack(fill='x', padx=20, pady=20)  # Afișăm sliderul în interfață.

        # Legăm diverse funcții la taste (Play/Pause, Previous, Next, etc.).
        self.master.bind('<space>', lambda e: self.play_pause())  # Butonul Play/Pause.
        self.master.bind('a', lambda e: self.previous())  # Butonul Previous.
        self.master.bind('d', lambda e: self.next())  # Butonul Next.
        self.master.bind('<Up>', lambda e: self.adjust_volume(5))  # Creșterea volumului.
        self.master.bind('<Down>', lambda e: self.adjust_volume(-5))  # Scăderea volumului.
        self.master.bind('<Return>', lambda e: self.toggle_repeat())  # Activare/Dezactivare Repeat.
        self.master.bind('<Delete>', lambda e: self.stop())  # Oprire redare.

    # Funcție pentru activarea/dezactivarea controlului prin gesturi.
    def toggle_gesture_control(self):
        if self.gesture_control_active:  # Dacă controlul prin gesturi este activ.
            self.gesture_control_active = False  # Dezactivăm controlul prin gesturi.
            self.gesture_control_button.config(text="Activare control gestual")  # Schimbăm textul butonului.
            if self.gesture_thread:  # Dacă există un fir de execuție pentru gesturi.
                self.gesture_thread.join(timeout=1.0)  # Așteptăm ca firul să se termine.
        else:  # Dacă controlul prin gesturi este dezactivat.
            self.gesture_control_active = True  # Activăm controlul prin gesturi.
            self.gesture_control_button.config(text="Dezactivare control gestual")  # Schimbăm textul butonului.
            self.gesture_thread = threading.Thread(target=self.process_gestures, daemon=True)  # Creăm firul de execuție pentru procesarea gesturilor.
            self.gesture_thread.start()  # Pornim firul de execuție.

    # Funcția care procesează gesturile folosind camera video.
    def process_gestures(self):
        cap = cv2.VideoCapture(0)  # Pornim camera video.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Setăm lățimea cadrului video.
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Setăm înălțimea cadrului video.

        last_gesture_time = time.time()  # Timpul ultimei gesturi procesate.
        gesture_cooldown = 0.5  # Cooldown de 0.5 secunde între procesarea gesturilor.
        frame_interval = 0.1  # Interval între cadrele analizate.
        prev_frame = None  # Cadru anterior pentru detectarea mișcării.

        while self.gesture_control_active:  # Cât timp controlul prin gesturi este activ.
            current_time = time.time()  # Timpul curent.
            if current_time - last_gesture_time < frame_interval:  # Verificăm intervalul dintre cadre.
                time.sleep(0.01)  # Așteptăm puțin.
                continue  # Trecem la următorul cadru.

            ret, frame = cap.read()  # Citim un cadru din fluxul video.
            if not ret:  # Dacă nu putem citi cadrul, continuăm.
                continue

            frame = cv2.resize(frame, (160, 120))  # Redimensionăm cadrul video.

            if prev_frame is not None and not detect_motion(frame, prev_frame):  # Verificăm dacă există mișcare între cadre.
                prev_frame = frame  # Actualizăm cadrul anterior.
                continue  # Trecem la următorul cadru.

            gesture, confidence = recognize_gesture(frame)  # Recunoaștem gestul din cadru.

            if gesture and confidence > 0.8 and (current_time - last_gesture_time) > gesture_cooldown:  # Dacă gestul este recunoscut cu o încredere mare.
                last_gesture_time = current_time  # Actualizăm timpul ultimei gesturi.
                self.master.after(0, lambda g=gesture: self.execute_gesture_command(g))  # Executăm comanda asociată gestului.

            prev_frame = frame  # Actualizăm cadrul anterior.
            time.sleep(0.05)  # Așteptăm înainte de a trece la următorul cadru.

        cap.release()  # Eliberăm camera video.

    # Funcție pentru executarea comenzii asociate gestului recunoscut.
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