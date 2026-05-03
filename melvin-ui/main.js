const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 400,
    height: 600,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  })

  win.loadFile('src/index.html')

  // Fenster verschieben
  ipcMain.on('move-window', (event, { deltaX, deltaY }) => {
    const [x, y] = win.getPosition()
    win.setPosition(x + deltaX, y + deltaY)
  })

  // Fenster schließen
  ipcMain.on('close-window', () => {
    app.quit()
  })
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())