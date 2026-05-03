const { ipcRenderer } = require('electron')

// --- Elemente ---
const mouthPath = document.getElementById('mouthPath')
const statusLabel = document.getElementById('statusLabel')
const responseText = document.getElementById('responseText')
const closeBtn = document.getElementById('closeBtn')

// --- Fenster schließen ---
closeBtn.addEventListener('click', () => ipcRenderer.send('close-window'))

// --- Fenster verschieben ---
let isDragging = false
let startX, startY
const titlebar = document.getElementById('titlebar')

titlebar.addEventListener('mousedown', (e) => {
  isDragging = true
  startX = e.screenX
  startY = e.screenY
})

document.addEventListener('mousemove', (e) => {
  if (!isDragging) return
  const deltaX = e.screenX - startX
  const deltaY = e.screenY - startY
  startX = e.screenX
  startY = e.screenY
  ipcRenderer.send('move-window', { deltaX, deltaY })
})

document.addEventListener('mouseup', () => isDragging = false)

// =====================
// ZUSTANDS-MANAGEMENT
// =====================

const states = {
  IDLE: 'idle',
  LISTENING: 'listening',
  THINKING: 'thinking',
  SPEAKING: 'speaking',
}

const stateLabels = {
  idle: 'BEREIT',
  listening: 'ZUHÖREN',
  thinking: 'DENKEN',
  speaking: 'SPRECHEN',
}

const mouthShapes = {
  idle:      'M 20 15 Q 50 20 80 15',
  listening: 'M 20 15 Q 50 10 80 15',
  thinking:  'M 25 15 Q 50 13 75 17',
  speaking:  'M 20 15 Q 50 25 80 15',
}

let currentState = states.IDLE
let mouthAnimFrame = null
let mouthPhase = 0

function setState(newState) {
  if (currentState === newState) return
  currentState = newState

  document.body.classList.remove(...Object.values(states))
  document.body.classList.add(newState)
  statusLabel.textContent = stateLabels[newState] || newState.toUpperCase()

  if (mouthAnimFrame) cancelAnimationFrame(mouthAnimFrame)

  if (newState === states.SPEAKING) {
    animateMouthSpeaking()
  } else {
    setMouthShape(mouthShapes[newState] || mouthShapes.idle)
  }
}

function setMouthShape(d) {
  mouthPath.setAttribute('d', d)
}

function animateMouthSpeaking() {
  mouthPhase += 0.15
  const openAmount = Math.abs(Math.sin(mouthPhase)) * 15
  const d = `M 20 15 Q 50 ${15 + openAmount} 80 15`
  setMouthShape(d)
  mouthAnimFrame = requestAnimationFrame(animateMouthSpeaking)
}

// =====================
// ANTWORT ANZEIGEN
// =====================

function typeResponse(text) {
  responseText.textContent = ''
  let i = 0
  const interval = setInterval(() => {
    responseText.textContent += text[i]
    i++
    if (i >= text.length) clearInterval(interval)
  }, 18)
}

// =====================
// ✅ WEBSOCKET VERBINDUNG ZU PYTHON
// =====================

let ws = null
let reconnectTimer = null

function connectWebSocket() {
  ws = new WebSocket('ws://localhost:8765')

  ws.onopen = () => {
    console.log('[WS] Verbunden mit Python Backend ✅')
    if (reconnectTimer) {
      clearInterval(reconnectTimer)
      reconnectTimer = null
    }
    setState('idle')
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)

      if (msg.type === 'state') {
        setState(msg.state)

        // Text anzeigen wenn mitgeschickt
        if (msg.text) {
          typeResponse(msg.text)
        }
      }
    } catch (e) {
      console.error('[WS] Fehler beim Parsen:', e)
    }
  }

  ws.onclose = () => {
    console.log('[WS] Verbindung getrennt – versuche neu...')
    // Alle 2 Sekunden neu versuchen
    if (!reconnectTimer) {
      reconnectTimer = setInterval(connectWebSocket, 2000)
    }
  }

  ws.onerror = () => {
    // Fehler werden durch onclose behandelt
  }
}

// Verbindung herstellen
connectWebSocket()

// Startanimation während wir auf Python warten
setState('idle')
responseText.textContent = 'Warte auf Verbindung mit Melvin...'