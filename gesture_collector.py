import cv2 # Biblioteca OpenCV pentru capturarea și prelucrarea imaginilor video.
import mediapipe as mp # Biblioteca Mediapipe pentru detectarea și urmărirea mâinilor.
import os # Biblioteca pentru interacțiunea cu sistemul de fișiere.
import numpy as np # Biblioteca pentru manipularea datelor numerice (arrays).

# Funcția principală pentru colectarea datelor despre gesturi.
def collect_gesture_data():
    # Inițializăm soluția Hands din Mediapipe pentru detectarea și urmărirea mâinilor.
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

    # Inițializăm funcționalitatea de desenare din Mediapipe pentru vizualizarea punctelor mâinii.
    mp_drawing = mp.solutions.drawing_utils

    # Lista de gesturi pe care dorim să le colectăm.
    gestures = ['Play', 'Pause', 'Next', 'Previous', 'Volume Up', 'Volume Down', 'Victory', 'Thumb Up', 'Rock and Roll']

    # Iterăm prin fiecare gest pentru a începe capturarea.
    for gesture in gestures:
        # Mesaj de instrucțiuni pentru utilizator.
        print(
            f"Colectarea datelor pentru gestul '{gesture}'. Apasă 'c' pentru a începe capturarea, 'q' pentru a trece la următorul gest.")

        while True:
            # Așteptăm input-ul de la utilizator.
            key = input().lower()
            if key == 'c':
                # Începem colectarea datelor pentru un singur gest.
                if collect_single_gesture(gesture, hands, mp_drawing):
                    break # Ieșim din bucla actuală după ce datele au fost colectate.
            elif key == 'q':
                # Mesaj de trecere la următorul gest.
                print(f"Trecere la următorul gest.")
                break
            else:
                # Mesaj de eroare dacă tasta apăsată nu este validă.
                print("Tastă nevalidă. Apasă 'c' pentru a începe sau 'q' pentru a trece la următorul gest.")

    # Mesaj la finalizarea colectării datelor pentru toate gesturile.
    print("Colectarea gesturilor a fost finalizată.")

# Funcție pentru colectarea datelor pentru un singur gest specific.
def collect_single_gesture(gesture, hands, mp_drawing):
    # Deschidem camera web pentru capturarea imaginilor.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Mesaj de eroare dacă camera nu poate fi accesată.
        print("Camera web nu a putut fi accesată.")
        return False

    frame_count = 0 # Inițializăm numărul de cadre capturate.
    max_frames = 2000  # Stabilim numărul maxim de cadre pe care dorim să le capturăm pentru un gest.

    while frame_count < max_frames:
        # Citim un cadru de la camera web.
        ret, frame = cap.read()
        if not ret:
            # Mesaj de eroare dacă nu putem citi cadrul.
            print("Eroare la citirea cadrului.")
            break

        # Convertim cadrul de la BGR (format OpenCV) la RGB (format utilizat de Mediapipe).
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)  # Procesăm cadrul pentru a detecta mâinile.

        if results.multi_hand_landmarks:
            # Iterăm prin fiecare mână detectată și desenăm punctele de referință pe cadrul video.
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

            # Salvăm datele despre gestul curent pe baza punctelor de referință detectate.
            save_gesture_data(gesture, results.multi_hand_landmarks, frame_count)
            frame_count += 1  # Incrementăm numărul de cadre capturate.

        # Afișăm textul cu numele gestului și numărul de cadre capturate pe ecranul video.
        cv2.putText(frame, f"{gesture}: {frame_count}/{max_frames}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                    2)
        # Afișăm cadrul video în fereastra "Camera".
        cv2.imshow("Camera", frame)

        # Ieșim din bucla de captură dacă utilizatorul apasă tasta 'q'.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Închidem fluxul de captură și fereastra video.
    cap.release()
    cv2.destroyAllWindows()
    # Mesaj de finalizare a capturii pentru gestul curent.
    print(f"Capturarea gestului '{gesture}' finalizată.")
    return True  # Întoarcem True pentru a indica succesul capturii.

# Funcție pentru salvarea datelor despre gesturi.
def save_gesture_data(gesture, hand_landmarks_list, frame_count):
    # Verificăm dacă directorul 'gestures' există; dacă nu, îl creăm.
    if not os.path.exists('gestures'):
        os.makedirs('gestures')

    # Creăm un subdirector pentru fiecare gest, dacă acesta nu există deja.
    gesture_dir = os.path.join('gestures', gesture)
    if not os.path.exists(gesture_dir):
        os.makedirs(gesture_dir)

    # Iterăm prin fiecare mână detectată (pot fi 1 sau 2 mâini).
    for i, hand_landmarks in enumerate(hand_landmarks_list):
        # Convertim punctele de referință ale mâinii într-un array de coordonate (x, y, z).
        landmarks_array = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]).flatten()
        # Creăm un nume de fișier unic pentru fiecare cadru și mână capturată.
        file_name = f"{gesture}_hand{i + 1}_{frame_count}.npy"
        # Generăm calea completă pentru fișier.
        file_path = os.path.join(gesture_dir, file_name)
        # Salvăm array-ul de coordonate într-un fișier .npy (format NumPy).
        np.save(file_path, landmarks_array)

# Blocul principal al scriptului; inițializăm colectarea datelor despre gesturi atunci când scriptul este rulat
if __name__ == "__main__":
    collect_gesture_data()  # Apelăm funcția principală pentru colectarea datelor.