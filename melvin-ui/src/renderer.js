const { ipcRenderer } = require('electron')

// --- Elemente ---
const mouthPath = document.getElementById('mouthPath')
const statusLabel = document.getElementById('statusLabel')
const responseText = document.getElementById('responseText')
const closeBtn = document.getElementById('closeBtn')
const inputOverlay = document.getElementById('inputOverlay')
const inputPrompt = document.getElementById('inputPrompt')
const inputField = document.getElementById('inputField')
const inputFieldWrap = document.getElementById('inputFieldWrap')
const inputConfirmWrap = document.getElementById('inputConfirmWrap')
const inputSubmit = document.getElementById('inputSubmit')
const confirmYes = document.getElementById('confirmYes')
const confirmNo = document.getElementById('confirmNo')

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

function setMouthShape(d) { mouthPath.setAttribute('d', d) }

function animateMouthSpeaking() {
  mouthPhase += 0.15
  const openAmount = Math.abs(Math.sin(mouthPhase)) * 15
  setMouthShape(`M 20 15 Q 50 ${15 + openAmount} 80 15`)
  mouthAnimFrame = requestAnimationFrame(animateMouthSpeaking)
}

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
// ✅ EINGABE OVERLAY
// =====================

let currentInputType = 'text'

function showInputOverlay(prompt, inputType, masked) {
  currentInputType = inputType
  inputPrompt.textContent = prompt

  // Reset
  inputField.value = ''
  inputField.type = masked ? 'password' : 'text'
  inputField.placeholder = masked ? '● ● ● ● ● ●' : 'Hier eingeben...'

  // Anzeige je nach Typ
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

  // Fokus nach kurzer Verzögerung
  setTimeout(() => {
    if (inputType !== 'confirm') inputField.focus()
  }, 100)
}

function hideInputOverlay() {
  inputOverlay.classList.remove('active')
  inputField.value = ''
}

function submitInput(value) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'input_response', value }))
  }
  hideInputOverlay()
}

// Submit per Button
inputSubmit.addEventListener('click', () => {
  const val = inputField.value.trim()
  if (val) submitInput(val)
})

// Submit per Enter
inputField.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const val = inputField.value.trim()
    if (val) submitInput(val)
  }
})

// Bestätigung Ja/Nein
confirmYes.addEventListener('click', () => submitInput('ja'))
confirmNo.addEventListener('click', () => submitInput('nein'))

// =====================
// WEBSOCKET
// =====================

let ws = null
let reconnectTimer = null

function connectWebSocket() {
  ws = new WebSocket('ws://localhost:8765')

  ws.onopen = () => {
    console.log('[WS] Verbunden ✅')
    if (reconnectTimer) { clearInterval(reconnectTimer); reconnectTimer = null }
    setState('idle')
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)

      if (msg.type === 'state') {
        setState(msg.state)
        if (msg.text) typeResponse(msg.text)
      }

      // ✅ UI schließen wenn Python beendet wird
      if (msg.type === 'quit') {
        ipcRenderer.send('close-window')
        return
      }

      // ✅ Eingabe-Anfrage von Python
      if (msg.type === 'input_request') {
        showInputOverlay(
          msg.prompt || 'Eingabe erforderlich',
          msg.input_type || 'text',
          msg.masked || false
        )
      }

    } catch (e) {
      console.error('[WS] Fehler:', e)
    }
  }

  ws.onclose = () => {
    if (!reconnectTimer) reconnectTimer = setInterval(connectWebSocket, 2000)
  }

  ws.onerror = () => {}
}

connectWebSocket()
setState('idle')
responseText.textContent = 'Warte auf Verbindung mit Melvin...'