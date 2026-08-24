<div align="center">

# 👁️ GazeAlert AI Suite
### *Medical-Grade Real-Time Eye Tracking, Cognitive Load Analyzer & Autonomous Study Coach*

[![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-Accelerated-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/Google%20MediaPipe-Face%20Landmarker-0097A7?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![Hardware Acceleration](https://img.shields.io/badge/AMD%20OpenCL-RDNA%202%20%2F%20DirectShow-ED1C24?style=for-the-badge&logo=amd&logoColor=white)](https://www.amd.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

**GazeAlert AI** este o suită software avansată pentru monitorizarea atenției, postura capului și ritmul de învățare/muncă la calculator. Folosește algoritmi de precizie sub-pixelică (Daugman Radial Operator) și corecție anatomică a axei foveale (**Unghiul Kappa $\kappa = 4.2^\circ$**) pentru a transforma orice cameră web obișnuită într-un eye-tracker de nivel profesional.

</div>

---

## 🌟 Caracteristici Principale (Key Features)

### 🔬 1. Optică & Fuziune Neuronală Medical-Grade
* **Daugman Integro-Differential Operator**: Rafinament la rezoluție de **0.05 pixeli** a marginii irisului și pupilei.
* **Corecția Anatomică Unghi Kappa ($\kappa = 4.2^\circ$)**: Corectează deviația naturală dintre axa optică a ochiului și linia vizuală foveală.
* **Pupillometrie & Efort Mental**: Măsurarea diametrului pupilar raportat la iris (30–42%) pentru estimarea în timp real a efortului cognitiv (**Cognitive Load %**).
* **Ritm de Lectură & Saccade**: Diferențiere automată între lectură normală, fixație stabilă și oboseală oculară (PERCLOS).
* **Filtru 1-Euro 1D & 2D**: Elimină tremurul camerei fără a introduce latență sau lag perceptibil.

### 👑 2. Moduri de Interfață & Floating Pill Widget
* **🖥️ Mod Studio HUD (1000x560)**: Randare completă a măștii faciale 478-Landmark FaceID, raze laser fluorescente 3D din pupile și panouri HUD translucide (*Glassmorphism*).
* **🔲 Mini-Widget OpenCV (Always-on-Top)**: Panou compact (420x110) cu orb de status pulsatil și bară de progres Pomodoro.
* **🪟 Desktop Floating Pill Widget (Frameless)**: Widget plutitor fără margini, transparent (92% opacity), cu suport **Drag-and-Drop** oriunde pe ecran.
* **🛡️ Minimize to System Tray (Lângă Ceas)**: Ascundere completă în bara de activități cu meniu de click-dreapta (`pystray`) și funcționare silențioasă în fundal.

### 🧠 3. Coach de Studiu Pomodoro & Statistici
* **Auto-Pause Inteligent**: Cronometrul de studiu se oprește automat dacă utilizatorul se uită la telefon sau pleacă de la birou.
* **Regula 20-20-20**: Memento la fiecare 20 de minute pentru relaxarea ochilor și prevenirea sindromului de ochi uscat.
* **Istoric SQLite & Export CSV/JSON**: Salvează automat fiecare sesiune în `study_history.db`, `study_sessions.csv` și `study_sessions.json`.
* **Raport Grafic HTML Interactiv (`study_report.html`)**: Generat automat cu grafice Chart.js (Donut Chart & Scor de Eficiență $A^+$).

### 🔔 4. Alerte Inteligente Anti-Spam & Sunete WAV
* **Sistem Progresiv în 3 Trepte**:
  1. *Chime Armonic Subtil* (la 4.5s) $\rightarrow$ C5/E5 acord muzical.
  2. *Reminder Politicos* (la 12s) $\rightarrow$ Sunet de atenționare.
  3. *Alertă Away* (la 25s) $\rightarrow$ Notificare nativă Windows Toast (`Win10Toast`).
* **Sintetizator Audio WAV Încorporat**: Fără dependențe externe greoaie, redare asincronă cu 0 ms lag prin Windows Multimedia.

---

## ⌨️ Scurtături Globale de Windows (Global Hotkeys)

> [!TIP]
> Scurtăturile funcționează **de oriunde din Windows**, chiar și când scrii cod în VS Code sau citești un PDF în browser!

| Scurtătură Globală | Tastă Fereastră | Acțiune |
|:---|:---:|:---|
| **`Ctrl + Alt + C`** | **`C`** | **Calibrare Rapidă Centru** (re-centrează la postura ta curentă) |
| **`Ctrl + Alt + W`** | **`W`** | **Comutare Mini-Widget / Fereastră Mare** |
| **`Ctrl + Alt + G`** | **`G`** | **Activează / Ascunde Widgetul Plutitor Frameless (Pill)** |
| **`Ctrl + Alt + H`** | **`H`** | **Minimizează în System Tray (Lângă Ceas)** |
| **`Ctrl + Alt + P`** | **`P`** | **Pornire / Pauză Pomodoro (25 / 5 min)** |
| **`Ctrl + Alt + S`** | **`S`** | **Sunet Alerte ON / OFF** |
| — | **`O`** | **Schimbă Tema Culori** (*Cyber Dark, Nord, Amber, Light*) |
| — | **`E`** | **Exportă Datele în CSV și JSON** |
| — | **`K`** | **Calibrare în 9 Puncte pe Ecran** |
| — | **`Q`** | **Ieșire & Deschide Raportul HTML de Studiu** |

---

## 🚀 Instalare și Rulare

### Cerințe de Sistem:
* **Sistem de Operare**: Windows 10 / 11 (64-bit)
* **Python**: 3.10, 3.11, 3.12, 3.13 sau 3.14
* **Cameră Web**: Orice webcam USB sau integrat (720p/1080p recomandat)
* **GPU**: Orice placă video compatibilă OpenCL (ex: AMD Radeon RX 6000/7000, NVIDIA GTX/RTX, Intel Iris)

### 1. Clonare Repository
```bash
git clone https://github.com/YOUR_USERNAME/GazeAlert.git
cd GazeAlert
```

### 2. Instalare Dependențe
```bash
pip install -r requirements.txt
```

### 3. Pornire Aplicație
Fă dublu-click pe **`run.bat`** sau rulează în terminal:
```bash
python main.py
```

---

## 🏗️ Structura Proiectului

```
GazeAlert/
├── main.py                   # Punctul principal de intrare, buclă video și randare HUD
├── gaze_detector.py          # Motorul AI: Daugman, Unghi Kappa, Pupillometrie, PERCLOS
├── modern_gui.py             # Widget plutitor frameless (Tkinter + Windows DWM)
├── system_tray.py            # Integrare în bara de sistem (pystray) cu meniu click-dreapta
├── alert_manager.py          # Notificări progresive Windows Toast și throttling anti-spam
├── sound_manager.py          # Sintetizator armonic de sunete WAV (0 ms latență)
├── theme_manager.py          # Manager teme vizuale (Cyberpunk, Nord, Warm Amber, Light)
├── session_logger.py         # Persistență automată în SQLite și export CSV/JSON
├── study_manager.py          # Motor Pomodoro, auto-pause și raport HTML interactiv
├── pro_face_tessellation.py  # Mască 3D 478 landmarks și raze laser fluorescente
├── screen_calibrator.py      # Calibrator în 9 puncte cu regresie polinomială Ridge
├── one_euro_filter.py        # Filtrare adaptivă 1-Euro fără lag
├── test_system.py            # Suită completă de 8 teste automate unitare
├── config.json               # Configurație personalizabilă
└── run.bat                   # Script de lansare rapidă pe Windows
```

---

## 🧪 Rulare Teste Automate
Pentru a valida toate cele 8 module (AI, Video, Audio, Teme, Bază de Date, Tray):
```bash
python test_system.py
```

---

## 📄 Licență
Acest proiect este licențiat sub termenii licenței **MIT**. Vezi fișierul `LICENSE` pentru detalii.
