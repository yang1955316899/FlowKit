// Electron Window API
export const electronWindow = {
  minimize: () => { window.electronAPI?.minimizeWindow() },
  maximize: () => { window.electronAPI?.maximizeWindow() },
  close: () => { window.electronAPI?.closeWindow() },
  resizeCompact: () => { window.electronAPI?.resizeCompact() },
  resizeNormal: () => { window.electronAPI?.resizeNormal() },
}
