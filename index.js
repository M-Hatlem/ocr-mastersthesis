// This file contains the required code to run the Electrong GUI and the python backend

// Modules to control application life and create native browser window
const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const fsExtra = require('fs-extra')

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 1000,
    webPreferences: {
      //Load preload scripts
      nodeIntegration: true,
      contextIsolation: false,
      //preload: path.join(__dirname, 'functions.js')
    }
  
  })

  // and load the index.html of the app.
  mainWindow.loadFile('index.html')
  // Open the DevTools.
  // mainWindow.webContents.openDevTools()
}

const StartPy = () => {
  pyProc = require('child_process').spawn('./Python/venv/Scripts/python',["./Python/Image_detection.py"])
  if (pyProc != null) {
    console.log('child process success')
  }
  //print python errors
  pyProc.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
  });

  //print python messages
  pyProc.stdout.on(`data` , (data) => {
    console.log("DATA:" + data)
  });
}


const exitPy = () => {
  pyProc.kill()
  pyProc = null
  if (pyProc == null) {
    console.log('child process kill success')
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})


// Starts the Python backend on startup
app.on('ready', StartPy)

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})


//Kills the python backend on applicaton exit
app.on('will-quit', exitPy)

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.


// This code is used to save a file, mainy a temporary image in the temp folder
ipcMain.on("SAVE_FILE", (event, path, buffer) => {
  fsExtra.outputFile(path, buffer, err => {
    if (err) {
        event.sender.send("ERROR", err.message)
    } else {
        event.sender.send("SAVED_FILE", path)
    }
  })
})



