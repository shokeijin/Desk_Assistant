/**
 * Melvin – Renderer-Prozess
 * ==========================
 * Steuert die gesamte UI-Logik:
 *   - Zustandsanimationen des Gesichts (Idle, Zuhören, Denken, Sprechen)
 *   - Tippen der Antworten in der Antwort-Box
 *   - Eingabe-Overlay für Text-, PIN- und Ja/Nein-Eingaben
 *   - WebSocket-Verbindung zum Python-Backend
 *   - Fenster verschieben und schließen via IPC
 *
 * WebSocket-Nachrichtentypen die empfangen werden:
 *   { type: 'state', state: '...', text: '...' }  – Zustand und Anzeigetext
 *   { type: 'input_request', prompt, input_type, masked }  – Eingabe anfordern
 *   { type: 'quit' }  – Anwendung beenden
 *
 * WebSocket-Nachrichtentypen die gesendet werden:
 *   { type: 'input_response', value: '...' }  – Nutzereingabe zurücksenden
 */

const { ipcRenderer } = require('electron')

// ---------------------------------------------------------------------------
// DOM-Elemente
// ---------------------------------------------------------------------------

const mouthPath       = document.getElementById('mouthPath')
const statusLabel     = document.getElementById('statusLabel')
const responseText    = document.getElementById('responseText')
const closeBtn        = document.getElementById('closeBtn')
const titlebar        = document.getElementById('titlebar')
const inputOverlay    = document.getElementById('inputOverlay')
const inputPrompt     = document.getElementById('inputPrompt')
const inputField      = document.getElementById('inputField')
const inputFieldWrap  = document.getElementById('inputFieldWrap')
const inputConfirmWrap = document.getElementById('inputConfirmWrap')
const inputSubmit     = document.getElementById('inputSubmit')
const confirmYes      = document.getElementById('confirmYes')
const confirmNo       = document.getElementById('confirmNo')

// ---------------------------------------------------------------------------
// Fenster-Steuerung
// ---------------------------------------------------------------------------

closeBtn.addEventListener('click', () => ipcRenderer.send('close-window'))

// Fenster per Drag auf der Titelleiste verschieben
let isDragging = false
let dragStartX, dragStartY

titlebar.addEventListener('mousedown', (e) => {
  isDragging = true
  dragStartX = e.screenX
  dragStartY = e.screenY
})

document.addEventListener('mousemove', (e) => {
  if (!isDragging) return
  const deltaX = e.screenX - dragStartX
  const deltaY = e.screenY - dragStartY
  dragStartX = e.screenX
  dragStartY = e.screenY
  ipcRenderer.send('move-window', { deltaX, deltaY })
})

document.addEventListener('mouseup', () => { isDragging = false })

// ---------------------------------------------------------------------------
// Zustandsverwaltung des Gesichts
// ---------------------------------------------------------------------------

// Alle möglichen Zustände des Assistenten
const STATES = {
  IDLE:      'idle',
  LISTENING: 'listening',
  THINKING:  'thinking',
  SPEAKING:  'speaking',
}

// Anzeigetexte für das Status-Label
const STATE_LABELS = {
  idle:      'BEREIT',
  listening: 'ZUHÖREN',
  thinking:  'DENKEN',
  speaking:  'SPRECHEN',
}

// SVG-Pfade für verschiedene Mundformen
const MOUTH_SHAPES = {
  idle:      'M 20 15 Q 50 20 80 15',  // Leichtes Lächeln
  listening: 'M 20 15 Q 50 10 80 15',  // Leicht angespannt / offen
  thinking:  'M 25 15 Q 50 13 75 17',  // Schief / nachdenklich
  speaking:  'M 20 15 Q 50 25 80 15',  // Geöffnet
}

let currentState = STATES.IDLE
let mouthAnimFrame = null
let mouthPhase = 0

/**
 * Wechselt den Zustand des Assistenten und aktualisiert die UI entsprechend.
 * Wird über WebSocket-Nachrichten vom Python-Backend ausgelöst.
 */
function setState(newState) {
  if (currentState === newState) return
  currentState = newState

  // CSS-Klassen tauschen – alle Animationen laufen über CSS
  document.body.classList.remove(...Object.values(STATES))
  document.body.classList.add(newState)

  statusLabel.textContent = STATE_LABELS[newState] || newState.toUpperCase()

  // Laufende Mundanimation stoppen
  if (mouthAnimFrame) {
    cancelAnimationFrame(mouthAnimFrame)
    mouthAnimFrame = null
  }

  if (newState === STATES.SPEAKING) {
    animateMouth()
  } else {
    setMouthShape(MOUTH_SHAPES[newState] || MOUTH_SHAPES.idle)
  }
}

/** Setzt den SVG-Pfad des Mundes auf eine neue Form. */
function setMouthShape(d) {
  mouthPath.setAttribute('d', d)
}

/**
 * Animiert den Mund beim Sprechen durch eine sinusförmige Auf-/Zubewegung.
 * Läuft als requestAnimationFrame-Loop solange der Zustand "speaking" ist.
 */
function animateMouth() {
  mouthPhase += 0.15
  const openAmount = Math.abs(Math.sin(mouthPhase)) * 15
  setMouthShape(`M 20 15 Q 50 ${15 + openAmount} 80 15`)
  mouthAnimFrame = requestAnimationFrame(animateMouth)
}

// ---------------------------------------------------------------------------
// Antwort-Box
// ---------------------------------------------------------------------------

/**
 * Schreibt den Text zeichenweise in die Antwort-Box (Schreibmaschinen-Effekt).
 * Laufende Animationen werden abgebrochen wenn ein neuer Text kommt.
 */
let typeInterval = null

function typeResponse(text) {
  if (typeInterval) clearInterval(typeInterval)
  responseText.textContent = ''
  let i = 0
  typeInterval = setInterval(() => {
    responseText.textContent += text[i]
    i++
    if (i >= text.length) clearInterval(typeInterval)
  }, 18)
}

// ---------------------------------------------------------------------------
// Eingabe-Overlay
// ---------------------------------------------------------------------------

/**
 * Zeigt das Eingabe-Overlay mit dem angegebenen Prompt an.
 *
 * inputType: 'text'    – Freie Texteingabe mit Bestätigen-Button
 *            'pin'     – Zahleneingabe, optional maskiert
 *            'confirm' – Ja/Nein-Auswahl ohne Textfeld
 */
function showInputOverlay(prompt, inputType, masked) {
  inputPrompt.textContent = prompt
  inputField.value = ''
  inputField.type = masked ? 'password' : 'text'
  inputField.placeholder = masked ? '● ● ● ● ● ●' : 'Hier eingeben...'

  if (inputType === 'confirm') {
    inputFieldWrap.style.display = 'none'
    inputConfirmWrap.style.display = 'flex'
    inputSubmit.style.display = 'none'
  } else {
    inputFieldWrap.style.display = 'flex'
    inputConfirmWrap.style.display = 'none'
    inputSubmit.style.display = 'block'
  }

  inputOverlay.classList.add('active')
  setTimeout(() => { if (inputType !== 'confirm') inputField.focus() }, 100)
}

/** Blendet das Eingabe-Overlay aus und leert das Eingabefeld. */
function hideInputOverlay() {
  inputOverlay.classList.remove('active')
  inputField.value = ''
}

/**
 * Sendet die Nutzereingabe per WebSocket an Python und schließt das Overlay.
 * Python wartet blockierend auf diese Antwort (request_input in websocket_bridge.py).
 */
function submitInput(value) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'input_response', value }))
  }
  hideInputOverlay()
}

// Event-Listener für die verschiedenen Eingabemethoden
inputSubmit.addEventListener('click', () => {
  const val = inputField.value.trim()
  if (val) submitInput(val)
})

inputField.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const val = inputField.value.trim()
    if (val) submitInput(val)
  }
})

confirmYes.addEventListener('click', () => submitInput('ja'))
confirmNo.addEventListener('click',  () => submitInput('nein'))

// ---------------------------------------------------------------------------
// WebSocket-Verbindung zum Python-Backend
// ---------------------------------------------------------------------------

let ws = null
let reconnectTimer = null

/**
 * Baut die WebSocket-Verbindung zum Python-Backend auf.
 * Versucht bei Verbindungsverlust automatisch alle 2 Sekunden neu zu verbinden.
 */
function connectWebSocket() {
  ws = new WebSocket('ws://localhost:8765')

  ws.onopen = () => {
    console.log('[WS] Verbunden mit Python-Backend ✅')
    if (reconnectTimer) {
      clearInterval(reconnectTimer)
      reconnectTimer = null
    }
    setState(STATES.IDLE)
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)

      if (msg.type === 'state') {
        setState(msg.state)
        if (msg.text) typeResponse(msg.text)
      }

      if (msg.type === 'quit') {
        // Python hat das Programm beendet – UI schließen
        ipcRenderer.send('close-window')
        return
      }

      if (msg.type === 'input_request') {
        // Python wartet auf eine Nutzereingabe
        showInputOverlay(
          msg.prompt     || 'Eingabe erforderlich',
          msg.input_type || 'text',
          msg.masked     || false,
        )
      }

    } catch (e) {
      console.error('[WS] Fehler beim Verarbeiten der Nachricht:', e)
    }
  }

  ws.onclose = () => {
    console.log('[WS] Verbindung getrennt – versuche Neuverbindung...')
    if (!reconnectTimer) {
      reconnectTimer = setInterval(connectWebSocket, 2000)
    }
  }

  ws.onerror = () => {
    // Fehler werden durch onclose abgehandelt
  }
}

// ---------------------------------------------------------------------------
// Initialisierung
// ---------------------------------------------------------------------------

connectWebSocket()
setState(STATES.IDLE)
responseText.textContent = 'Warte auf Verbindung mit Melvin...'