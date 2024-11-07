import os # Biblioteca pentru interacțiunea cu sistemul de fișiere.
import numpy as np # Biblioteca pentru manipularea datelor numerice (arrays).
import tensorflow as tf # Biblioteca TensorFlow pentru construirea și antrenarea rețelelor neuronale.
from tensorflow.keras import layers, models # Importă layerele și modelele din Keras, care face parte din TensorFlow.

# Funcția pentru încărcarea datelor despre gesturi.
def load_gesture_data():
    gestures_dir = "gestures"  # Directorul unde sunt stocate datele despre gesturi.
    if not os.path.exists(gestures_dir):  # Verifică dacă directorul 'gestures' există.
        print(f"Eroare: Directorul '{gestures_dir}' nu există.")  # Mesaj de eroare dacă directorul nu există.
        return None, None, None  # Returnează None dacă directorul nu există.

    # Lista gesturilor dorite care trebuie încărcate.
    desired_gestures = ['Play', 'Pause', 'Next', 'Previous', 'Volume Up', 'Volume Down', 'Victory', 'Thumb Up',
                        'Rock and Roll']

    images = []  # Listă pentru a stoca imaginile/landmark-urile gesturilor.
    labels = []  # Listă pentru a stoca etichetele asociate gesturilor.
    gestures = []  # Listă pentru a stoca gesturile reale (numele acestora).

    # Iterează prin fiecare gest dorit și încarcă fișierele .npy corespunzătoare.
    for label, gesture in enumerate(desired_gestures):
        gesture_dir = os.path.join(gestures_dir, gesture)  # Creează calea către directorul pentru fiecare gest.
        if not os.path.isdir(gesture_dir):  # Verifică dacă directorul pentru gest există.
            print(f"Avertisment: Directorul pentru gestul '{gesture}' nu există.")  # Afișează un avertisment dacă nu există.
            continue  # Trece la următorul gest dacă directorul nu există.

        gesture_files = os.listdir(gesture_dir)  # Listăm fișierele din directorul gestului curent.
        if not gesture_files:  # Verifică dacă există fișiere în director.
            print(f"Avertisment: Nu s-au găsit fișiere pentru gestul '{gesture}'.")  # Afișează un avertisment dacă nu sunt fișiere.
            continue  # Trece la următorul gest dacă nu există fișiere.

        gestures.append(gesture)  # Adaugă gestul în lista de gesturi.
        for file_name in gesture_files:  # Iterează prin fișierele din directorul gestului curent.
            file_path = os.path.join(gesture_dir, file_name)  # Creează calea completă către fișier.
            if file_name.endswith('.npy'):  # Verifică dacă fișierul este de tip .npy (fișier NumPy).
                landmarks = np.load(file_path)  # Încarcă datele din fișierul .npy.
                images.append(landmarks)  # Adaugă landmark-urile în lista de imagini.
                labels.append(label)  # Adaugă eticheta (indexul gestului) în lista de etichete.
            else:
                print(f"Avertisment: Fișierul '{file_name}' nu este de tip .npy și va fi ignorat.")  # Afișează avertisment dacă fișierul nu este .npy.

    if not images:  # Verifică dacă nu s-au încărcat imagini.
        print("Eroare: Nu s-au putut încărca datele pentru niciun gest.")  # Mesaj de eroare dacă nu s-au găsit imagini.
        return None, None, None  # Returnează None dacă nu s-au încărcat imagini.

    images = np.array(images)  # Convertim lista de imagini într-un array NumPy.
    labels = np.array(labels)  # Convertim lista de etichete într-un array NumPy.

    return images, labels, gestures  # Returnează imaginile, etichetele și gesturile.

# Funcția pentru antrenarea modelului de recunoaștere a gesturilor.
def train_model():
    images, labels, gestures = load_gesture_data()  # Încarcă datele despre gesturi.
    if images is None or labels is None or gestures is None:  # Verifică dacă datele au fost încărcate corect.
        print("Antrenarea modelului a eșuat din cauza lipsei datelor.")  # Afișează un mesaj dacă datele lipsesc.
        return  # Ieșire din funcție dacă datele lipsesc.

    # Afișează informații despre datele încărcate.
    print(f"Forma datelor de intrare: {images.shape}")  # Afișează forma datelor de intrare (imaginile).
    print(f"Forma etichetelor: {labels.shape}")  # Afișează forma etichetelor.
    print(f"Număr de gesturi: {len(gestures)}")  # Afișează numărul de gesturi încărcate.
    print(f"Gesturi incluse: {gestures}")  # Afișează lista de gesturi incluse.

    # Definirea arhitecturii modelului neuronal.
    model = models.Sequential([
        layers.Input(shape=(63,)),  # Definim input-ul de 63 de valori (21 de puncte de referință pentru fiecare dimensiune x, y, z).
        layers.Dense(128, activation='relu'),  # Primul strat dens cu 128 de neuroni și funcția de activare ReLU.
        layers.Dropout(0.3),  # Strat de dropout cu 30% pentru a preveni overfitting-ul.
        layers.Dense(64, activation='relu'),  # Al doilea strat dens cu 64 de neuroni și funcția de activare ReLU.
        layers.Dropout(0.3),  # Strat de dropout cu 30% pentru a preveni overfitting-ul.
        layers.Dense(len(gestures), activation='softmax')  # Stratul de ieșire cu numărul de gesturi și activarea Softmax pentru clasificare.
    ])

    # Compilăm modelul cu optimizer-ul Adam și funcția de pierdere 'sparse_categorical_crossentropy'.
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])  # Afișează precizia ca metrică de evaluare.

    # Afișează sumarul arhitecturii modelului.
    model.summary()

    # Antrenăm modelul folosind datele încărcate.
    model.fit(images, labels, epochs=50, validation_split=0.2, batch_size=32)  # Antrenare pe 50 de epoci cu 20% date de validare și batch-size de 32.

    # Salvăm modelul antrenat într-un fișier .h5.
    model.save("gesture_model.h5")  # Salvăm modelul într-un fișier h5.
    print("Modelul a fost antrenat și salvat ca 'gesture_model.h5'.")  # Afișează mesajul de succes al salvării modelului.

# Verificăm dacă acest script este rulat direct.
if __name__ == "__main__":
    train_model()  # Apelăm funcția pentru antrenarea modelului.