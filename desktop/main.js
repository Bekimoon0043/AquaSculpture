// LuxuryForm Studio — Electron shell.
// Spawns the Python backend (single-process mode: it serves the UI on :8100),
// then loads the app in a native window. Kills the backend on exit.
// ELECTRON_RUN_AS_NODE is stripped: some dev machines set it globally, which
// silently turns Electron into plain Node (app becomes undefined).
delete process.env.ELECTRON_RUN_AS_NODE

const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

const APP_URL = 'http://localhost:8100'
let backend = null

function startBackend() {
  const backendDir = path.join(__dirname, '..', 'backend')
  backend = spawn('python', ['main.py'], { cwd: backendDir })
  backend.on('error', (err) => console.error('backend failed to start:', err))
}

function waitForBackend(retries = 60) {
  return new Promise((resolve, reject) => {
    const attempt = (n) => {
      fetch(`${APP_URL}/api/health`)
        .then((r) => (r.ok ? resolve() : attempt(n - 1)))
        .catch(() => (n > 0
          ? setTimeout(() => attempt(n - 1), 500)
          : reject(new Error('backend did not come up'))))
    }
    attempt(retries)
  })
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1520,
    height: 950,
    backgroundColor: '#14161a',
    title: 'LuxuryForm Studio',
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })
  win.loadURL(APP_URL)
}

app.whenReady().then(async () => {
  startBackend()
  try {
    await waitForBackend()
  } catch (e) {
    console.error(e)
  }
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (backend) backend.kill()
  app.quit()
})
