// SculptFlow Studio — Electron shell (Phase 0).
// Dev: loads the Vite dev server. Packaged: loads the built frontend.
const { app, BrowserWindow } = require('electron')
const path = require('path')

const DEV_URL = 'http://localhost:5173'
const isDev = !app.isPackaged

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    backgroundColor: '#14161a',
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })

  if (isDev) {
    win.loadURL(DEV_URL)
  } else {
    win.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  app.quit()
})
