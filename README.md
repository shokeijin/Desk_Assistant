# M.E.L.V.I.N – KI Desktop Assistant

> Persönlicher Sprachassistent, inspiriert von J.A.R.V.I.S. aus Iron Man

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![LangChain](https://img.shields.io/badge/LangChain-latest-green?style=flat-square)
![Electron](https://img.shields.io/badge/Electron-latest-47848F?style=flat-square&logo=electron)
![GPT-4o-mini](https://img.shields.io/badge/GPT--4o--mini-OpenAI-black?style=flat-square&logo=openai)
![License](https://img.shields.io/badge/Lizenz-MIT-yellow?style=flat-square)

---

## 🤖 Was ist Melvin?

Melvin ist ein vollständig selbst entwickelter KI-Desktop-Assistent der per Sprache gesteuert wird. Er läuft lokal auf dem eigenen Computer, hört auf ein Wake-Word, versteht natürliche Sprache und antwortet mit einer hochwertigen KI-Stimme.

**Kernfunktionen:**
- 🎤 Wake-Word Erkennung (`"Melvin"`) via Google Speech-to-Text
- 🔊 Sprachausgabe mit Conrad Neural (Microsoft edge-tts)
- 🧠 KI-Agent mit Gesprächsgedächtnis (LangChain + GPT-4o-mini)
- 🖥️ Animiertes Gesicht als Desktop-UI (Electron)
- 👥 Multi-Profil System mit Spracheingabe
- 🔐 Admin Panel (F12 + 6-stellige PIN)

---

## 📁 Projektstruktur

```
Desk_Assistant/
├── assistant/
│   ├── storage/
│   │   ├── profiles/          # Pro Nutzer eigener Ordner
│   │   │   └── <name>/
│   │   │       ├── todos.json
│   │   │       ├── reminders.json
│   │   │       ├── user_profile.json
│   │   │       └── settings.json
│   │   ├── admin.json         # Admin-PIN (SHA-256 gehasht)
│   │   ├── reminder_store.py
│   │   ├── todo_store.py
│   │   ├── user_profile_store.py
│   │   └── settings_store.py
│   ├── tools/
│   │   ├── todo_tools.py
│   │   ├── reminder_tools.py
│   │   ├── user_profile_tools.py
│   │   ├── math_tools.py
│   │   ├── web_tools.py
│   │   └── settings_tools.py
│   ├── agent.py               # LangChain Agent + Persönlichkeit
│   ├── profile_manager.py
│   └── router.py              # Anfrage-Routing
├── melvin-ui/                 # Electron Frontend
│   ├── src/
│   │   ├── index.html
│   │   ├── style.css
│   │   └── renderer.js
│   ├── main.js
│   └── package.json
├── main.py                    # Hauptprogramm
├── websocket_bridge.py        # Python ↔ Electron Verbindung
├── admin_store.py             # PIN Speicherung (SHA-256)
├── admin_panel.py             # Admin Konsole
├── start_melvin.bat           # Ein-Klick Start
├── requirements.txt           # Python Abhängigkeiten
└── .env                       # API Keys (nicht im Repo!)
```

---

## 🚀 Installation

### Voraussetzungen

- Python 3.12+
- Node.js 18+ & npm
- Git

### 1. Repository klonen

```bash
git clone https://github.com/dein-name/Desk_Assistant.git
cd Desk_Assistant
```

### 2. Python Virtual Environment erstellen

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Python Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. Electron Abhängigkeiten installieren

```bash
cd melvin-ui
npm install
cd ..
```

### 5. API Keys konfigurieren

Erstelle eine `.env` Datei im `Desk_Assistant/` Ordner:

```env
OPENAI_API_KEY=dein_openai_key
TAVILY_API_KEY=dein_tavily_key
USER_NAME=DeinName
```

> **OpenAI API Key:** https://platform.openai.com/api-keys  
> **Tavily API Key:** https://tavily.com (kostenloser Plan verfügbar)

### 6. Melvin starten

**Option A – Ein-Klick Start (empfohlen):**
```
start_melvin.bat doppelklicken
```

**Option B – Manuell:**
```bash
# Terminal 1: Electron UI
cd melvin-ui
npm start

# Terminal 2: Python Backend
python main.py
```

---

## 🎤 Verwendung

1. Sage **"Melvin"** gefolgt von deinem Befehl
2. Oder sage nur **"Melvin"** – er fragt dann nach dem Befehl

**Beispiele:**
```
"Melvin, wie ist das Wetter heute?"
"Melvin, füge Milch zur Einkaufsliste hinzu"
"Melvin, erinnere mich morgen um 9 Uhr an den Arzttermin"
"Melvin, wie viel ist 245 mal 17?"
"Melvin, was sind die neuesten Nachrichten?"
```

**Beenden:**
```
"Melvin, exit"
```

---

## 🔐 Admin Panel

Das Admin Panel ermöglicht vollen Zugriff auf alle Profile und Daten.

1. **F12** drücken (während Melvin läuft)
2. 6-stellige PIN eingeben
3. Admin Panel öffnet sich im Terminal

**Funktionen:**
- Profile anzeigen, umbenennen, löschen
- Todos & Reminder aller Profile verwalten
- Einstellungen bearbeiten
- Benutzerprofile anpassen

> Die PIN wird beim ersten Start einmalig festgelegt und als SHA-256-Hash gespeichert.

---

## ⚙️ Einstellungen

Die Einstellungen werden pro Profil in `storage/profiles/<name>/settings.json` gespeichert:

```json
{
  "agent_name": "melvin",
  "use_speech_output": true
}
```

| Einstellung | Beschreibung | Standard |
|---|---|---|
| `agent_name` | Wake-Word (lowercase) | `"melvin"` |
| `use_speech_output` | Sprachausgabe an/aus | `true` |

---

## 🛠️ Technologien

| Bereich | Technologie | Zweck |
|---|---|---|
| KI & Logik | LangChain + GPT-4o-mini | Agent, Routing, Gedächtnis |
| Spracheingabe | speech_recognition + Google STT | Wake-Word & Befehle |
| Sprachausgabe | edge-tts (Conrad Neural) | Natürliche deutsche Stimme |
| Audio | pygame | MP3-Wiedergabe |
| Desktop UI | Electron + HTML/CSS/JS | Animiertes Gesicht |
| Verbindung | websockets | Python ↔ Electron Echtzeit |
| Websuche | Tavily API | Aktuelle Informationen |
| Datenspeicher | JSON (pro Profil) | Todos, Reminder, Profil |
| Sicherheit | SHA-256 | Admin-PIN Speicherung |
| Hotkey | keyboard | F12 Admin-Trigger |

---

## 🧠 Architektur

```
Nutzer spricht
     ↓
Google STT (Sprache → Text)
     ↓
Wake-Word Erkennung ("Melvin")
     ↓
Router (klassifiziert Anfrage)
     ↓
┌────────────────────────────────────┐
│  todo │ reminder │ web │ chat │ .. │
└────────────────────────────────────┘
     ↓
KI-Agent (GPT-4o-mini + LangChain)
     ↓
edge-tts (Text → Sprache, Conrad Neural)
     ↓
WebSocket → Electron UI (Zustand + Text)
```

---

## 🔧 Debug & Test Modus

In `main.py` ganz oben:

```python
DEBUG_MODE = True   # Zeigt [DEBUG] Ausgaben im Terminal
TEST_MODE  = False  # Tastatur statt Mikrofon (zum Testen)
```

Im Test-Modus kannst du Befehle direkt eintippen:
```
melvin wie ist das wetter in berlin
```

---

## 📋 Bekannte Einschränkungen

- **Fuzzy-Matching** beim Profilnamen vergleicht nur die ersten 3 Buchstaben (z.B. `Andy` → `Andi`)
- **Spracherkennung** benötigt eine Internetverbindung (Google STT)
- **Websuche** benötigt einen Tavily API Key

---

## 🚀 Roadmap

- [ ] Portable `.exe` für USB-Stick (PyInstaller + Electron Builder)
- [ ] Profil-Bestätigung per Sprache nach Erkennung
- [ ] Nachname bei doppeltem Vornamen
- [ ] Reminder-Anzeige direkt in der Electron UI
- [ ] UI weiter verfeinern

---


*Entwickelt mit ❤️ – M.E.L.V.I.N ist kein offizielles Produkt und steht in keiner Verbindung zu Marvel oder Disney.*
