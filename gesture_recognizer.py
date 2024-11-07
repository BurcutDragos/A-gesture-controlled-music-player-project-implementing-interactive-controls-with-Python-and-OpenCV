import cv2  # Biblioteca OpenCV pentru capturarea și prelucrarea imaginilor video.
import tensorflow as tf  # Biblioteca TensorFlow pentru utilizarea modelului de învățare automată.
import numpy as np  # Biblioteca pentru manipularea datelor numerice (arrays).
import mediapipe as mp  # Biblioteca Mediapipe pentru detectarea și urmărirea mâinilor.

# Încărcăm modelul de recunoaștere a gesturilor o singură dată pentru eficiență.
model = tf.keras.models.load_model("gesture_model.h5")
# Inițializăm soluția Hands din Mediapipe pentru detectarea și urmărirea mâinilor.
mp_hands = mp.solutions.hands
# Configurăm parametrii pentru detecția mâinilor: modul dinamic, numărul maxim de mâini, și încrederea minimă pentru detecție și urmărire.
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7,
                       min_tracking_confidence=0.5)
# Lista gesturilor recunoscute de model, corespondente cu etichetele din model.
gestures = ['Play', 'Pause', 'Next', 'Previous', 'Volume Up', 'Volume Down', 'Victory', 'Thumb Up', 'Rock and Roll']

# Funcția pentru recunoașterea gesturilor dintr-un cadru video.
def recognize_gesture(frame):
    # Convertim cadrul din format BGR (OpenCV) în format RGB (Mediapipe) pentru a putea fi procesat.
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Procesăm cadrul RGB pentru a detecta mâinile și landmark-urile acestora.
    results = hands.process(frame_rgb)

    # Verificăm dacă au fost detectate landmark-uri pentru mâini.
    if results.multi_hand_landmarks:
        # Iterăm prin fiecare mână detectată.
        for hand_landmarks in results.multi_hand_landmarks:
            # Convertim landmark-urile mâinii într-un array cu coordonate x, y și z.
            landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]).flatten()
            # Reshape pentru a se potrivi cu input-ul modelului (1 rând și toate coordonatele).
            processed_landmarks = landmarks.reshape(1, -1)

            # Facem predicția folosind modelul încărcat, fără a afișa detalii suplimentare.
            predictions = model.predict(processed_landmarks, verbose=0)
            # Determinăm clasa (gestul) cu probabilitatea cea mai mare.
            predicted_class = np.argmax(predictions)
            # Obținem probabilitatea maximă (încrederea) asociată cu predicția.
            confidence = np.max(predictions)

            # Returnăm numele gestului recunoscut și încrederea în predicție.
            gesture_name = gestures[predicted_class]
            return gesture_name, confidence

    # Dacă nu s-au detectat mâini, returnăm None și o încredere de 0.
    return None, 0.0

# Funcția pentru detectarea mișcării între două cadre consecutive.
def detect_motion(frame1, frame2):
    # Calculăm diferența absolută între cele două cadre.
    diff = cv2.absdiff(frame1, frame2)
    # Convertim cadrul de diferență în gri pentru a-l prelucra mai ușor.
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    # Aplicăm un blur Gaussian pentru a reduce zgomotul din imagine.
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Aplicăm o operațiune de threshold pentru a obține o imagine binară (alb-negru).
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    # Returnăm True dacă suma pixelilor albi din imaginea binară depășește un prag, indicând mișcare semnificativă.
    return np.sum(thresh) > 10000  # Pragul poate fi ajustat în funcție de sensibilitatea dorită.

# Blocul principal pentru rularea aplicației de recunoaștere a gesturilor.
if __name__ == "__main__":
    # Deschidem camera web pentru capturarea imaginilor video.
    cap = cv2.VideoCapture(0)
    prev_frame = None  # Inițializăm variabila pentru a stoca cadrul anterior.
    while True:
        # Citim un nou cadru de la camera web.
        ret, frame = cap.read()
        if not ret:  # Dacă nu putem citi cadrul, ieșim din buclă.
            break

        # Redimensionăm cadrul pentru a reduce consumul de resurse și a accelera procesarea.
        frame = cv2.resize(frame, (320, 240))

        # Dacă există un cadru anterior și nu se detectează mișcare semnificativă, continuăm la următorul cadru.
        if prev_frame is not None and not detect_motion(frame, prev_frame):
            prev_frame = frame  # Actualizăm cadrul anterior cu cadrul curent.
            continue  # Sărim peste restul buclei dacă nu se detectează mișcare.

        # Recunoaștem gestul în cadrul curent.
        gesture, confidence = recognize_gesture(frame)
        if gesture:  # Dacă un gest a fost recunoscut.
            # Afișăm numele gestului și încrederea în predicție pe cadrul video.
            cv2.putText(frame, f"Gesture: {gesture} ({confidence:.2f})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0), 2)

        # Afișăm cadrul video în fereastra "Gesture Recognition".
        cv2.imshow("Gesture Recognition", frame)
        prev_frame = frame  # Actualizăm cadrul anterior cu cadrul curent.

        # Verificăm dacă utilizatorul apasă tasta 'q' pentru a ieși din buclă.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Închidem camera și toate ferestrele deschise.
    cap.release()
    cv2.destroyAllWindows()