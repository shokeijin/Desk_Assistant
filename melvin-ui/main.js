/**
 * Melvin – Electron Hauptprozess
 * ================================
 * Erstellt das rahmenlose, transparente Anwendungsfenster
 * und verwaltet die IPC-Kommunikation mit dem Renderer-Prozess.
 *
 * IPC-Kanäle:
 *   'move-window'  – Verschiebt das Fenster um (deltaX, deltaY) Pixel
 *   'close-window' – Beendet die Anwendung
 */

const { app, BrowserWindow, ipcMain } = require('electron')

/**
 * Erstellt das Hauptfenster mit futuristischem HUD-Design.
 * Das Fenster ist rahmenlos, transparent und immer im Vordergrund.
 */
function createWindow() {
  const win = new BrowserWindow({
    width: 400,
    height: 600,
    frame: false,          // Kein nativer Fensterrahmen
    transparent: true,     // Hintergrund des Fensters ist durchsichtig
    resizable: false,      // Feste Größe – Layout ist darauf ausgelegt
    alwaysOnTop: true,     // Bleibt immer über anderen Fenstern sichtbar
    webPreferences: {
      nodeIntegration: true,    // Ermöglicht require() im Renderer
      contextIsolation: false,  // Notwendig für direkten IPC-Zugriff
    },
  })

  win.loadFile('src/index.html')

  // Fenster per Drag auf der Titelleiste verschieben
  ipcMain.on('move-window', (_event, { deltaX, deltaY }) => {
    const [x, y] = win.getPosition()
    win.setPosition(x + deltaX, y + deltaY)
  })

  // Anwendung sauber beenden
  ipcMain.on('close-window', () => {
    app.quit()
  })
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())